'''
Modulo "proof of concept" di un client per testare la nostra API. Per il lancio di questo script sono
necessari come parametri l'indirizzo ip dell'API con porta, l'id di una palestra ed uno smard card id.
La API key verrà letta da un file al seguente percorso: "secrets/api_key.txt"

Non aggiungo la libreria requests in requirements.txt, non so se serve all'API.
Per il momento installatevela voi a mano se dovete fare del testing.
'''
import sys, argparse
from datetime import datetime
from hashlib import sha256
import hmac
import requests

def prendisegreto(secretFile: str) -> str:
    """Funzione che prende un segreto dalla cartella secrets"""
    try:
        with open(f"secrets/{secretFile}", "r") as f:
            return f.read().strip()
    except Exception as e:
        sys.exit(f"Errore nella lettura del segreto, eccezione: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-i','--indirizzo', required=True,
                        help='Indirizzo IP e porta del container, es: 10.10.10.10:234')
    parser.add_argument('-p', '--palestraId', required=True,
                        help='Id della palestra')
    parser.add_argument('-s', '--smartcardId', required=True,
                        help='Smard Card ID')
    args = parser.parse_args()

    timestamp = int(datetime.now().timestamp() * 1000)
    api_key = prendisegreto("api_key.txt")
    dati = args.smartcardId + args.palestraId + str(timestamp)
    signature = hmac.new(key=api_key.encode('utf-8'), msg=dati.encode('utf-8'), digestmod=sha256).hexdigest()
    body = {
        "IDSmartCard":args.smartcardId,
        "IDPalestra":args.palestraId,
        "Timestamp":timestamp,
        "Signature":signature
    }

    response = requests.post(url=f"{args.indirizzo}", json=body)
    print(response.content)
    