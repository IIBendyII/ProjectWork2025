"""
Modulo python contenente funzioni per la anonimizzazione e pseudonimizzazione delle informazioni.
La Presudonimizzazione è basata su RSA. Le funzioni qui contenute riguardano soltanto la cifratura
"""
from Crypto.PublicKey import RSA
from Crypto.Util.number import bytes_to_long, long_to_bytes
from datetime import date
import base64

def load_encrypt_key(key:str) -> RSA.RsaKey:
    """
    Funzione che data una chiave testuale per la cifratura RSA (chiave pubblica) restituisce un
    oggetto RsaKey
    """
    encrypt_key = RSA.import_key(
        extern_key=key
    )
    return encrypt_key

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
            raise ValueError("Lo Smart Card ID è troppo lungo per la chiave RSA scelta.")
            
        # Raw RSA Encryption: c = m^e mod n
        cypher_int = pow(plain_int, encrypt_key.e, encrypt_key.n)
        
        # Converto in stringa sicura per DB (Base64 URL-safe)
        cypher_bytes = long_to_bytes(cypher_int)
        return base64.urlsafe_b64encode(cypher_bytes).decode('utf-8')
    except Exception as e:
        return f'Errore Cifratura: {str(e)}'

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
    from api_logger import prendisegreto
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