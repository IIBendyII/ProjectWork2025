from flask import Flask, request, jsonify
from flask_cors import cross_origin
from db_handler import Gestionale, LogsAndStats
from privacy_modules import anonimizzatore, pseudonimizzatore, load_encrypt_key
from datetime import datetime, date, timezone
import hmac
from hashlib import sha256
from sys import stdout
import os, logging

# Impostazione di Logging per stampare eventuali eccezioni nei Docker Logs
logger = logging.getLogger(__name__)
handler = logging.StreamHandler(stdout)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

def prendisegreto(secretFile: str) -> str:
    """Funzione che prende un segreto dalla cartella dei docker secrets"""
    try:
        with open(f"/run/secrets/{secretFile}", "r") as f:
            return f.read().strip()
    except Exception as e:
        logger.critical("Errore nella lettura del segreto, eccezione: %s", str(e))

DB_LS_USER = os.getenv("DB_LS_USER")
DB_GS_USER = prendisegreto("db_gs_api_user")
DB_LS_PASS = prendisegreto("db_ls_api_password")
DB_GS_PASS = prendisegreto("db_gs_api_password")
DB_LS_HOST = os.getenv("DB_LS_HOST")
DB_GS_HOST = prendisegreto("db_gs_ip")
DB_LS_NAME = os.getenv("DB_LS_DATABASE")
DB_GS_NAME = os.getenv("DB_GS_DATABASE")
DATABASE_LS_URI = f"mysql+pymysql://{DB_LS_USER}:{DB_LS_PASS}@{DB_LS_HOST}/{DB_LS_NAME}"
DATABASE_GS_URI = f"mysql+pymysql://{DB_GS_USER}:{DB_GS_PASS}@{DB_GS_HOST}/{DB_GS_NAME}"
ENCRYPTKEY = load_encrypt_key(prendisegreto("encrypt_key"))
ENCRYPTPAD = prendisegreto("pseudo_pad")
API_KEY = prendisegreto("api_key")

HEXDIGITS = '0123456789ABCDEF'
SECONDI_ACCETTABILI = 20

def timestampCheck(ricezione: float, timestamp: int) -> bool:
    '''
        Funzione che controlla il timestamp della richiesta ricevuta.
        Se la ricezione è avvenuta entro un delta di secondi accettabile restituisce vero,
        altrimenti falso.
    '''
    if ricezione - (timestamp/1000) <= SECONDI_ACCETTABILI:
        return True
    else:
        return False

def signatureCheck(idSmartCard:str, idPalestra:int, timestamp:int, signature:str) -> bool:
    '''Funzione che controlla la validità della firma ricevuta nella richiesta'''
    string = idSmartCard + str(idPalestra) + str(timestamp)
    check = hmac.new(key=API_KEY.encode('utf-8'),msg=string.encode('utf-8'),digestmod=sha256).hexdigest()
    if check == signature:
        return True
    else:
        return False

def check(gestore: Gestionale, ricezione:float,
          idSmartCard:str, idPalestra:int, timestamp:int, signature:str) -> dict:
    '''
        Funzione che effettua in cascata tutti i controlli necessari 
        a verificare la validità della richiesta ricevuta. Se i controlli hanno
        successo, restituisce un dizionario contenente un oggetto Cliente e Palestra.
    '''
    if timestampCheck(ricezione, timestamp):
        if signatureCheck(idSmartCard, idPalestra, timestamp, signature):
            # Verifico che la palestra esista
            palestra = gestore.select_palestra(idPalestra)
            if palestra is not None:
                # Verifico che il cliente esista
                cliente = gestore.select_client(idSmartCard)
                if cliente is not None:
                    return {"cliente": cliente, "palestra": palestra}
    return None

def smartcardCorretto(idSmartCard:str) -> bool:
    '''
        Funzione che controlla la correttezza del campo SmartCardID:
        6 caratteri esadecimali uppercase
    '''
    if len(idSmartCard)==6 and all(c in HEXDIGITS for c in idSmartCard):
        return True
    else:
        return False
    
def finalHmac(idSmartCard:str, timestamp:int):
    '''Funzione che calcola la signature finale con cui rispondere al client'''
    string = idSmartCard + str(timestamp)
    return hmac.new(key=API_KEY.encode('utf-8'),msg=string.encode('utf-8'),digestmod=sha256).hexdigest()


app = Flask(__name__)

@app.route("/", methods=["POST"])
@cross_origin()
def home():
    logger.debug("Connessione stabilita")
    data = request.json

    # I timestamp vengono trattati tutti in timezone UTC
    ricezione = datetime.now(tz=timezone.utc).timestamp()
    gestore = Gestionale(DATABASE_GS_URI)

    #controlla che i dati siano nel formato richiesto
    try:
        idSmartCard = data["IDSmartCard"]
        if not smartcardCorretto(idSmartCard):
            raise ValueError("SmartCard ID non ha un formato accettabile")
        idPalestra = int(data["IDPalestra"])
        timestamp = int(data["Timestamp"])
        signature = data["Signature"]
    except ValueError as e:
        logger.error("Dati ricevuti incorretti: %s", str(e))
        return jsonify({"valido": False,
                        "signature": finalHmac(data["IDSmartCard"], data["Timestamp"])})
    
    abbonamentoValido = False
    
    # Controllo la validità della richiesta e mi salvo le informazioni recuperate sul Cliente e Palestra
    info = check(gestore, ricezione, idSmartCard, idPalestra, timestamp, signature)
    if info is not None:
        logger.debug("Check passed")

        #fa richicesta a selet_abbonamenti,
        #se la smart card ricevuta ha un abbonamento valido associato continuano le operazioni
        abbonamenti = gestore.select_abbonamenti(info["cliente"].id)
        oggi = date.today()
        for x in abbonamenti:
            if x.valido_dal < oggi < x.valido_al:
                abbonamentoValido = True
                break
        if abbonamentoValido:
            #conversione timestamp in datetime per il Database Logs e Statistiche
            timestamp = datetime.fromtimestamp(timestamp=timestamp/1000,tz=timezone.utc)

            #pseudonimizzazione id
            pseudoSmartID = pseudonimizzatore(idSmartCard,
                                              encrypt_key=ENCRYPTKEY,
                                              pseudo_pad=ENCRYPTPAD)

            #anonimizzazione dati gestionale
            dati = anonimizzatore({
            "cliente":info["cliente"],
            "palestra":info["palestra"],
            "timestamp":timestamp})

            #salvo logs e statistiche
            magazziniere = LogsAndStats(DATABASE_LS_URI)
            magazziniere.insert_log(smart_card_id=pseudoSmartID,
                                    palestra_id=idPalestra,
                                    timestamp=timestamp)
            magazziniere.insert_stats(sesso=dati["sesso"],
                                      fascia_eta=dati["fascia_eta"],
                                      palestra_id=dati["palestra_id"],
                                      data_ingresso=dati["data_ingresso"],
                                      fascia_oraria=dati["fascia_oraria"])
    
    logger.debug("Abbonamento Valido: %s", abbonamentoValido)
    return jsonify({"valido": abbonamentoValido,
                    "signature": finalHmac(idSmartCard, timestamp)})

if __name__ == "__main__":
    app.run()