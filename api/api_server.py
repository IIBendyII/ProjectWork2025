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

SECONDI_ACCETTABILI = 10

def timestampCheck(ricezione):
    differenza = timeDifferenceCalculator(timestamp, ricezione)
    if differenza <= SECONDI_ACCETTABILI:
        logger.debug("timestamp TRUE")
        return True
    else:
        logger.debug("timestamp FALSE")
        return False

def signatureCheck():
    string = str(idSmartCard) + str(idPalestra) + str(timestamp) + API_KEY
    hashResult = hashing(string)
    logger.debug(hashResult)

    if hashResult == signature:
        logger.debug("hash TRUE")
        return True
    else:
        logger.debug("hash FALSE")
        return False

def palestraIdCheck(gestore):
    '''
    Dobbiamo mettere un controllo per verificare che idPalestra sia effettivamente un intero.
    Non ha senso perdere tempo ad interrogare il gestore se idPalestra non è un numero.
    Inoltre è un controllo di sanificazione, passabile come Defense in Depth.
    '''
    pal = gestore.select_palestra(idPalestra)
    if pal is not None:
        logger.debug("pID TRUE")
        return True
    else:
        logger.debug("pID FALSE")
        return False

def cardIdCheck(gestore):
    '''
    Dobbiamo mettere un controllo per verificare che idSmartCard sia una stringa composta da 
    6 caratteri esadecimali (quindi valori da 0 a 9 e dalla A alla F maiuscole).
    Non ha senso perdere tempo ad interrogare il gestore se idSmartCard non è un id valido.
    Inoltre è un controllo di sanificazione, passabile come Defense in Depth.
    '''
    card = gestore.select_client(idSmartCard)
    if card is not None:
        logger.debug("cID TRUE")
        return True
    else:        
        logger.debug("cID FALSE")
        return False

def check(gestore, ricezione):
    '''
    da sistemare, non serve fare tutti e 4 i controlli alla volta ogni volta, (ricreare la signature 
    e contattare il Db gestionale richiede tempo...) meglio eseguirli in cascata per risparmiare risorse, 
    e se uno non passa allora return False
    '''
    c1 = timestampCheck(ricezione)
    c2 = signatureCheck()
    c3 = palestraIdCheck(gestore)
    c4 = cardIdCheck(gestore)

    if c1 and c2 and c3 and c4:
        return True
    else:
        return False
    
def hashing(string):
    return sha256(string.encode('utf-8')).hexdigest()

def timeDifferenceCalculator(timestamp, ricezione):
    '''
    Si può invece usare il metodo "datetime.strptime(date_string, format)" per creare un oggetto datetime dalla stringa
    di timestamp, e sottrarlo con ricezione. Il risultato sarebbe un oggetto "timedelta", dal quale puoi ricavare
    il numero di secondi di differenza con il medoto "total_seconds". Il codice dovrebbe venire molto più pulito così
    '''
    timestamp = datetime.strptime(timestamp,r"%Y-%m-%d %H:%M:%S")
    delta = ricezione - timestamp
    return delta.total_seconds()
    '''
    #ricostruisce i datetime in un formato col quale si possono sottrarre e calcola i secondi
    timestampDiviso = timestamp.split(' ')
    ricezioneDiviso = ricezione.split(' ')
    timestampData = timestampDiviso[0]
    timestampoOra = timestampDiviso[1]
    ricezioneData = ricezioneDiviso[0]
    ricezioneOra = ricezioneDiviso[1]
    td = timestampData.split('-')
    rd = ricezioneData.split('-')
    to = timestampoOra.split(':')
    ro = ricezioneOra.split(':')
    a = datetime(int(td[0]), int(td[1]), int(td[2]), int(to[0]), int(to[1]), int(to[2]))
    b = datetime(int(rd[0]), int(rd[1]), int(rd[2]), int(ro[0]), int(ro[1]), int(ro[2]))
    res = int((a - b).total_seconds() // 60)
    return res'''


app = Flask(__name__)

@app.route("/", methods=["POST"])
def home():
    logger.debug("Connessione stabilita")
    data = request.json
    '''
    Le variabili globali sono un problema in questo contesto: essendo leggibili da tutto il codice, se una
    funzione modifica lo stato di una variabile mentre essa viene letta da un'altra, si creano dei problemi
    (situazione possibile, nel contesto di due o più richieste contemporanee al server)
    '''
    global idSmartCard
    global idPalestra
    global timestamp
    global signature

    ricezione = datetime.now()
    gestore = Gestionale(DATABASE_GS_URI)

    idSmartCard = data["IDSmartCard"]
    idPalestra = data["IDPalestra"]
    timestamp = data["Timestamp"]
    signature = data["Signature"]

    if check(gestore, ricezione):
        logger.debug("Check passed")
        #fai rihicesta a selet_abbonamenti
        abbonamenti = gestore.select_abbonamenti(idSmartCard)
        abbonamentoValido = False
        oggi = date.today()
        for x in abbonamenti:
            if x.valido_dal < oggi < x.valido_al:
                abbonamentoValido = True
        
        if abbonamentoValido:
            logger.debug("validosss")
            cliente = gestore.select_client(idSmartCard)
            pal = gestore.select_palestra(idPalestra)

            #pseudonimizzazione id
            pseudoSmartID = pseudonimizzatore(idSmartCard, encrypt_key=ENCRYPTKEY, pseudo_pad=ENCRYPTPAD)

            #anonimizzazione dati gestionale
            dati = anonimizzatore({
            "sesso":cliente.sesso,
            "data_nascita":cliente.data_nascita,
            "palestra_id":idPalestra,
            "timestamp":datetime.strptime(timestamp,r"%Y-%m-%d %H:%M:%S")})

            #salvo logs e statistiche
            magazziniere = LogsAndStats(DATABASE_LS_URI)
            magazziniere.insert_log(smart_card_id=pseudoSmartID, palestra_id=idPalestra, timestamp=timestamp)
            magazziniere.insert_stats(sesso=dati["sesso"], fascia_eta=dati["fascia_eta"], palestra_id=dati["palestra_id"],
                                  data_ingresso=dati["data_ingresso"], fascia_oraria=dati["fascia_oraria"])
        
        #da ritornare a client
        string = str(idSmartCard) + str(timestamp) + API_KEY
        hashResult = hashing(string)
        return jsonify({"valido": abbonamentoValido, "signature": hashResult})
    else: 
        logger.debug("NOPE")
        return jsonify({"check": "fallito"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000) # Da cambiare con la porta 443 a progetto finito
    '''
    Da chiedere al Prof: Per il certificato vogliamo usare un container certbot che richieda il certificato 
    e lo salvi in un volume. Domanda: carichiamo il certificato SSL direttamente nella API o lo affidiamo ad
    un reverse proxy che si occupi lui di crittografare le comunicazioni con il client?

    Per caricardo direttamente qui nella API, ho trovato questo esempio di codice, ovviamente da modificare:
    context = SSL.Context(SSL.TLSv1_2_METHOD)
    context.use_privatekey_file('/etc/letsencrypt/live/your-api-domain.com/privkey.pem')
    context.use_certificate_file('/etc/letsencrypt/live/your-api-domain.com/fullchain.pem')
    if __name__ == '__main__':
       app.run(ssl_context=context, host='0.0.0.0', port=443)
    '''