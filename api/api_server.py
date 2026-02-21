from flask import Flask, request, jsonify
from db_handler import Gestionale, LogsAndStats
from privacy_modules import anonimizzatore, pseudonimizzatore, load_encrypt_key
from datetime import datetime, date
from hashlib import sha256
from sys import stdout
import os, logging

# Impostazione di Logging per stampare eventuali eccezioni nei Docker Logs
logger = logging.getLogger(__name__)
handler = logging.StreamHandler(stdout)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.ERROR)

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

DATETIME_FORMAT = r"%Y-%m-%d %H:%M:%S"
HEXDIGITS = '0123456789ABCDEF'
SECONDI_ACCETTABILI = 10

def timestampCheck(ricezione: datetime, timestamp: datetime) -> bool:
    '''
        Funzione che controlla il timestamp della richiesta ricevuta.
        Se la ricezione è avvenuta entro un delta di secondi accettabile restituisce vero,
        altrimenti falso.
    '''
    if int((ricezione - timestamp).total_seconds()) <= SECONDI_ACCETTABILI:
        return True
    else:
        return False

def signatureCheck(idSmartCard:str, idPalestra:int, timestamp:datetime, signature:str) -> bool:
    '''Funzione che controlla la validità della firma ricevuta nella richiesta'''
    string = idSmartCard + str(idPalestra) + timestamp.strftime(DATETIME_FORMAT) + API_KEY
    hash = sha256(string.encode('utf-8')).hexdigest()
    if hash == signature:
        return True
    else:
        return False

def palestraIdCheck(gestore:Gestionale, idPalestra:int) -> bool:
    '''
        Funzione che controlla che l'ID palestra ricevuto 
        sia presente nella tabella delle palestre del DB Gestionale
    '''
    pal = gestore.select_palestra(idPalestra)
    if pal is not None:
        return True
    else:
        return False

def cardIdCheck(gestore:Gestionale, idSmartCard:str) -> bool:
    '''
        Funzione che controlla che lo SmartCard ID ricevuto 
        sia presente nella tabella dei clienti del DB Gestionale
    '''
    card = gestore.select_client(idSmartCard)
    if card is not None:
        return True
    else:
        return False

def check(gestore: Gestionale, ricezione:datetime,
          idSmartCard:str, idPalestra:int, timestamp:datetime, signature:str) -> bool:
    '''
        Funzione che effettua in cascata tutti i controlli necessari 
        a verificare la validità della richiesta ricevuta
    '''
    if timestampCheck(ricezione, timestamp):
        if signatureCheck(idSmartCard, idPalestra, timestamp, signature):
            if palestraIdCheck(gestore, idPalestra):
                if cardIdCheck(gestore, idSmartCard):
                    return True
    return False

def smartcardCorretto(idSmartCard:str) -> bool:
    '''
        Funzione che controlla la correttezza del campo SmartCardID:
        6 caratteri esadecimali uppercase
    '''
    if len(idSmartCard)==6 and all(c in HEXDIGITS for c in idSmartCard):
        return True
    else:
        return False
    
def finalHash(idSmartCard:str, timestamp:str):
    '''Funzione che calcola la signature finale con cui rispondere al client'''
    string = idSmartCard + timestamp + API_KEY
    return sha256(string.encode('utf-8')).hexdigest()


app = Flask(__name__)

@app.route("/", methods=["POST"])
def home():
    logger.debug("Connessione stabilita")
    data = request.json

    ricezione = datetime.now()
    gestore = Gestionale(DATABASE_GS_URI)

    #controlla che i dati siano nel formato richiesto
    try:
        idSmartCard = data["IDSmartCard"]
        if not smartcardCorretto(idSmartCard):
            raise ValueError("SmartCard ID non ha un formato accettabile")
        idPalestra = int(data["IDPalestra"])
        timestamp = datetime.strptime(data["Timestamp"], r"%Y-%m-%d %H:%M:%S")
        signature = data["Signature"]
    except ValueError as e:
        logger.error("Dati ricevuti incorretti: %s", str(e))
        return jsonify({"valido": False,
                        "signature": finalHash(data["IDSmartCard"], data["Timestamp"])})
    
    abbonamentoValido = False
    if check(gestore, ricezione, idSmartCard, idPalestra, timestamp, signature):
        logger.debug("Check passed")

        #fa richicesta a selet_abbonamenti,
        #se la smart card ricevuta ha un abbonamento valido associato continuano le operazioni
        abbonamenti = gestore.select_abbonamenti(idSmartCard)
        oggi = date.today()
        for x in abbonamenti:
            if x.valido_dal < oggi < x.valido_al:
                abbonamentoValido = True
        
        if abbonamentoValido:
            cliente = gestore.select_client(idSmartCard)

            #pseudonimizzazione id
            pseudoSmartID = pseudonimizzatore(idSmartCard,
                                              encrypt_key=ENCRYPTKEY,
                                              pseudo_pad=ENCRYPTPAD)

            #anonimizzazione dati gestionale
            dati = anonimizzatore({
            "sesso":cliente.sesso,
            "data_nascita":cliente.data_nascita,
            "palestra_id":idPalestra,
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
                    "signature": finalHash(idSmartCard, timestamp.strftime(DATETIME_FORMAT))})

if __name__ == "__main__":
    app.run()