'''
Modulo python d'esempio per l'inserimento di dati nel database di Log e Statistiche ed il
controllo di dati nel database gestionale. Crea ciclicamente log fasulli e statistiche che
vengono poi inserite nelle rispettive tabelle. Contiene:
    - funzioni per la gestione di segreti con docker
    - funzione per la pseudonimizzazione
    - funzione per l'anonimizzazione
'''

from db_handler import Gestionale, LogsAndStats
from datetime import datetime, date
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
PSEUDOKEY = None #prendisegreto("pseudo_key.txt")
PSEUDOPAD = None #prendisegreto("pseudo_pad.txt")

def pseudonimizzatore(smartID: str, pseudoKey:str, pseudoPad:str) -> str:
    """Funzione che dato un ID, chiave e padding, pseudonimizza l'ID (Raw RSA)"""
    #implementare RSA in modo che lo smartID da implementare sia, grazie ad un padding preimpostato,
    # sempre di una dimensione specifica, in modo che l'algoritmo RSA non ne crei uno lui randomico
    # rendendo l'implementazione deterministica
    return smartID

def anonimizzatore(dati: dict) -> dict:
    """
        Funzione di anonimizzazione della tabella Statistiche, basata su k-anonimity.
        Data una riga da inserire nella tabella Statistiche, anonimizza le seguenti informazioni:
        - Data di nascita -> fascia di età
        - Timestamp di ingresso -> data e fascia oraria di ingresso
    """
    FASCEETA = [(0,19),(20,29),(30,39),(40,49),(50,59),(60,69),(70,79),(80,200)]
    FASCEORARIE = [(7,12),(13,18),(19,24),(0,6)]

    # creo data del compleanno con giorno e mese di nascita ed anno di oggi poi controllo: 
    # se (data_oggi >= data_compleanno) allora (età = anno oggi - anno nascita)
    # altrimenti (età = anno oggi - anno nascita - 1)
    oggi = date.today()
    data_nascita = dati['data_nascita']
    compleanno = date(
        year=oggi.year,
        month=data_nascita.month,
        day=data_nascita.day
        )
    if oggi >= compleanno:
        eta = oggi.year - data_nascita.year
    else:
        eta = oggi.year - data_nascita.year - 1
    
    # determino la fascia di età
    for fascia in FASCEETA:
        if eta in range(fascia[0],fascia[1]+1):
            fascia_eta = f'{fascia[0]}-{fascia[1]}'
            break
    
    data_ingresso = dati['timestamp'].date()
    ora_ingresso = dati['timestamp'].time()

    # determino la fascia oraria di ingresso
    for fascia in FASCEORARIE:
        if ora_ingresso.hour in range(fascia[0],fascia[1]+1):
            fascia_oraria = f'{fascia[0]}-{fascia[1]}'
            break

    return {"sesso":dati["sesso"], "fascia_eta":fascia_eta, "palestra_id":dati["palestra_id"], 
            "data_ingresso":data_ingresso, "fascia_oraria":fascia_oraria}

if __name__ == "__main__":
    smartIDs = [] # non carico id su github, ve li inserite voi ;)
    for smartID in smartIDs:
        pseudoSmartID = pseudonimizzatore(smartID, pseudoKey=PSEUDOKEY)
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
        