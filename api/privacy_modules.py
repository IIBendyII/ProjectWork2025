"""
Modulo python contenente funzioni per la anonimizzazione e pseudonimizzazione delle informazioni.
La Presudonimizzazione è basata su RSA. Le funzioni qui contenute riguardano soltanto la cifratura
"""
from Crypto.PublicKey import RSA
from Crypto.Util.number import bytes_to_long, long_to_bytes
from datetime import date, datetime
from sys import stdout
from babel import Locale
from pytz import country_timezones, timezone, utc
import base64, logging

# Impostazione di Logging per stampare eventuali eccezioni nei Docker Logs
logger = logging.getLogger(__name__)
handler = logging.StreamHandler(stdout)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.ERROR)

FASCEETA = [(0,19),(20,29),(30,39),(40,49),(50,59),(60,69),(70,79),(80,200)]
FASCEORARIE = [(7,12),(13,18),(19,24),(0,6)]
# Creo un dizionario di sigle, derivanti dai nomi delle nazioni del mondo in italiano
STATO_A_SIGLA = {stato.lower():sigla for sigla, stato in Locale("it").territories.items()}

def load_encrypt_key(key:str) -> RSA.RsaKey:
    """
        Funzione che data una chiave testuale per la cifratura RSA (chiave pubblica) restituisce un
        oggetto RsaKey
    """
    encrypt_key = RSA.import_key(
        extern_key=key
    )
    return encrypt_key

def timezone_converter(timestamp:datetime, stato:str) -> datetime:
    '''
        Funzione che dato un timestamp con fuso orario utc, lo converte nel fuso orario corrispondete allo
        stato di provenienza del timestamp
    '''
    try:
        sigla = STATO_A_SIGLA[stato.lower()]
        nome_tz = country_timezones[sigla.lower()][0] # Prendo il primo fuso orario della lista per paese
        tz = timezone(nome_tz)
    except:
        logger.error("Errore nell'identificazione di una sigla per lo stato %s. Timezone impostata a UTC")
        tz = utc

    return timestamp.astimezone(tz)

def pseudonimizzatore(smart_card_id: str, encrypt_key:RSA.RsaKey, pseudo_pad:str) -> str:
    """
        Funzione che dato un ID, chiave e padding, pseudonimizza l'ID con cifratura asimmetrica RSA.
        La tipologia di RSA utilizzata è di tipo Raw RSA con padding preimpostato, per rendere gli
        presudonimi generati deterministici in modo da garantire controlli anti-frode senza impegare
        chiavi di decifratura o tabelle di corrispondenza on-line.
        
        Questo tipo di implementazione si è rivelato necessario in quanto per motivi di sicurezza,
        le librerie per la cifratura RSA come cryptography inseriscono sempre e comunque
        un padding causale, di fatto rendendo l'implementazione non deterministica.
    """
    try:
        plaintext = (smart_card_id + pseudo_pad).encode('utf-8')
        
        # Converto il mio plaintext in un numero intero
        plain_int = bytes_to_long(plaintext)
        
        # Controllo di sicurezza (non dovrebbe essere necessario: lo Smart Card ID dovrebbe
        # essere validato in fase di acquisizione)
        if plain_int >= encrypt_key.n:
            raise ValueError("Lo Smart Card ID è troppo lungo per la chiave scelta.")
            
        # Raw RSA Encryption: c = m^e mod n
        cypher_int = pow(plain_int, encrypt_key.e, encrypt_key.n)
        
        # Converto in stringa sicura per DB (Base64 URL-safe)
        cypher_bytes = long_to_bytes(cypher_int)
        return base64.urlsafe_b64encode(cypher_bytes).decode('utf-8')
    except Exception as e:
        logger.error('Errore Cifratura: %s', str(e))

def anonimizzatore(dati: dict) -> dict:
    """
        Funzione di anonimizzazione della tabella Statistiche, basata su k-anonimity.
        Dato un dizionario contenente oggetti Cliente, Palestra ed un timestamp, ricava i dati 
        necessari per l'inserimento nella tabella Statistiche ed anonimizza le seguenti informazioni:
        - Data di nascita -> fascia di età
        - Timestamp di ingresso -> data e fascia oraria di ingresso
    """

    # creo data del compleanno con giorno e mese di nascita ed anno di oggi poi controllo: 
    # se (data_oggi >= data_compleanno) allora (età = anno oggi - anno nascita)
    # altrimenti (età = anno oggi - anno nascita - 1)
    oggi = date.today()
    data_nascita = dati['cliente'].data_nascita
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
    
    # Converto il Timestamp in base al fuso orario dello stato in cui si trova la palestra
    timestamp = timezone_converter(dati['timestamp'], dati['palestra'].stato)
    data_ingresso = timestamp.date()
    ora_ingresso = timestamp.time()

    # determino la fascia oraria di ingresso
    for fascia in FASCEORARIE:
        if ora_ingresso.hour in range(fascia[0],fascia[1]+1):
            fascia_oraria = f'{fascia[0]}-{fascia[1]}'
            break

    return {"sesso":dati["cliente"].sesso, "fascia_eta":fascia_eta, "palestra_id":dati["palestra"].id, 
            "data_ingresso":data_ingresso, "fascia_oraria":fascia_oraria}

if __name__ == "__main__":
    from api_server import prendisegreto
    smartID = input("Inserisci uno Smart Card ID da pseudonimizzare: ")
    if len(smartID) == 6:
        valori = '0123456789ABCDEF'
        for char in smartID:
            if char not in valori:
                raise ValueError("La Smart Card ID inserita non è valida")
        print(f"Ecco il suo pseudonimo: {pseudonimizzatore(
            smart_card_id=smartID,
            encrypt_key=load_encrypt_key(prendisegreto("encrypt_key.txt")),
            pseudo_pad=prendisegreto("pseudo_pad.txt")
        )}")    
    else:
        print("Lunghezza Smart Card ID errata!")