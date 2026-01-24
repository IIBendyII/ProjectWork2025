'''
Modulo python d'esempio per l'inserimento di dati nel database di Log e Statistiche ed il
controllo di dati nel database gestionale. Crea ciclicamente log fasulli e statistiche che
vengono poi inserite nelle rispettive tabelle. Contiene:
    - funzioni per la gestione di segreti con docker
    - funzione per la pseudonimizzazione
    - funzione per l'anonimizzazione
'''

from db_handler import Gestionale, LogsAndStats
from privacy_modules import load_encrypt_key, pseudonimizzatore, anonimizzatore
from datetime import datetime
from time import sleep
import sys, os, random  # random da rimuovere a fine testing

def prendisegreto(secretFile: str) -> str:
    """Funzione che prende un segreto nella cartella dei docker secrets"""
    try:
        #with open(f"run/secrets/{secretFile}", "r") as f:
        with open(f"secrets/{secretFile}", "r") as f: # da sostituire a fine testing
            return f.read().strip()
    except Exception as e:
        sys.exit(f"Errore nella lettura del segreto, eccezione: {e}")

DB_LS_USER = "api"
DB_GS_USER = prendisegreto("db_gs_api_user.txt")
DB_LS_PASS = prendisegreto("db_ls_api_password.txt")
DB_GS_PASS = prendisegreto("db_gs_api_password.txt")
#DB_LS_HOST = os.getenv("DB_HOST","worldfit_db")
DB_LS_HOST = "172.17.0.1" # da sostituire a fine testing
DB_GS_HOST = prendisegreto("db_gs_ip.txt")
DB_LS_PORT = "3306"
DB_GS_PORT = "3306"
DB_LS_NAME = "WorldFitLS"
DB_GS_NAME = "WorldFit"
DATABASE_LS_URI = f"mysql+pymysql://{DB_LS_USER}:{DB_LS_PASS}@{DB_LS_HOST}:{DB_LS_PORT}/{DB_LS_NAME}"
DATABASE_GS_URI = f"mysql+pymysql://{DB_GS_USER}:{DB_GS_PASS}@{DB_GS_HOST}:{DB_GS_PORT}/{DB_GS_NAME}"
ENCRYPTKEY = load_encrypt_key(prendisegreto("encrypt_key.txt"))
ENCRYPTPAD = prendisegreto("pseudo_pad.txt")

if __name__ == "__main__":
    smartIDs = [] # non carico id su github, ve li inserite voi ;)
    for smartID in smartIDs:
        pseudoSmartID = pseudonimizzatore(smartID, encryptKey=ENCRYPTKEY, encryptPad=ENCRYPTPAD)
        palestraID = random.randint(1,50)
        timestamp = datetime.now()
        print(f"SmartCardID Generato: {smartID}, SmartCardID pseudonimizzato: " \
              f"{pseudoSmartID}, ID Palestra: {palestraID}, Timestamp: {timestamp}")
        
        # creo un oggetto "magazziniere" per interagire con il DB di Logs e Statistiche
        magazziniere = LogsAndStats(DATABASE_LS_URI)
        # inserisco un log all'interno della tabella logs
        magazziniere.insert_log(smart_card_id=pseudoSmartID,palestra_id=palestraID,timestamp=timestamp)
        # creo un oggetto "gestore" per interagire con il DB Gestionale
        gestore = Gestionale(DATABASE_GS_URI)
        # prendo le informazioni del cliente partendo dalla sua SmartCard
        cliente = gestore.select_client(smartID)

        # anonimizzo le seguenti informazioni
        dati = anonimizzatore({
            "sesso":cliente.sesso,
            "data_nascita":cliente.data_nascita,
            "palestra_id":palestraID,
            "timestamp":timestamp
        })
        
        # inserisco i dati anonimizzati nella tabella statistiche
        magazziniere.insert_stats(sesso=dati["sesso"], fascia_eta=dati["fascia_eta"], palestra_id=dati["palestra_id"],
                                  data_ingresso=dati["data_ingresso"], fascia_oraria=dati["fascia_oraria"])
        sleep(1)
        