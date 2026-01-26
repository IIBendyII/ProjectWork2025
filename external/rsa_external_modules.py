'''
Modulo python esterno all'applicazione contenente funzioni per la generazione di chiavi RSA e per la
re-identificazione di pseudonimi di Smart Card.
'''

import sys
from Crypto.PublicKey import RSA
from Crypto.Util.number import bytes_to_long, long_to_bytes
import base64
import argparse

def prendisegreto(secretFile: str) -> str:
    """Funzione che prende un segreto dalla cartella secrets"""
    try:
        with open(f"secrets/{secretFile}", "r") as f:
            return f.read().strip()
    except Exception as e:
        sys.exit(f"Errore nella lettura del segreto, eccezione: {e}")

def generate_keys(passphrase:str) -> tuple[bytes,bytes]:
    """Funzione per la generazione di chiavi RSA"""
    key = RSA.generate(2048)
    decrypt_key = key.export_key(
        format='PEM',
        passphrase=passphrase,
        pkcs=8,
        protection='PBKDF2WithHMAC-SHA512AndAES256-CBC'
    )
    encrypt_key = key.publickey().export_key()
    return encrypt_key, decrypt_key

def re_identificazione(pseudo_id: str, decrypt_key: RSA.RsaKey, pseudo_pad:str) -> str:
    """Decifra lo pseudonimo usando la chiave privata."""    
    try:
        # Decodifica da Base64 lo pseudonimo e lo trasforma in un numero intero
        cypher_bytes = base64.urlsafe_b64decode(pseudo_id)
        cypher_int = bytes_to_long(cypher_bytes)
        
        # Raw RSA Decryption: m = c^d mod n
        m_int = decrypt_key._decrypt(cypher_int)
        
        # Recupero il plaintext originale
        plaintext = long_to_bytes(m_int)
        
        # Rimozione del padding ed identificazione dell'ID
        if not plaintext.endswith(f'{pseudo_pad}'.encode('utf-8')):
            raise ValueError("Decifratura fallita o chiave errata")
            
        id_originale = plaintext[:-len(pseudo_pad)].decode('utf-8')
        return id_originale
        
    except Exception as e:
        return f"Errore decifratura: {str(e)}"
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-m', '--mode', required=True, choices=['genera_chiavi','identifica'],
                        help="""
                        Seleziona la modalità di esecuzione:
                        - 'genera_chiavi'-> Genera un nuovo paio di chiavi RSA partendo da una passphrase;
                        - 'identifica'-> richiama la funzione di re-identificazione per ottenere uno 
                                        Smart Card ID da uno pseudonimo;
                        """)
    args = parser.parse_args()
    match args.mode:
        case 'genera_chiavi':
            passphrase = input('Inserisci una passphrase: ')
            encrypt_key, decrypt_key = generate_keys(passphrase)

            try:
                with open('secrets/encrypt_key.txt', 'w') as enc:
                    enc.write(encrypt_key.decode('utf-8'))
            except Exception as e:
                print(f"Errore di salvataggio della chiave di cifratura: {str(e)}")

            try:
                with open('secrets/decrypt_key.txt', 'w') as dec:
                    dec.write(decrypt_key.decode('utf-8'))
            except Exception as e:
                print(f"Errore di salvataggio della chiave di decifratura: {str(e)}")
            
            print('Chiavi generate!')

        case 'identifica':
            pseudo_id=input('Inserisci uno pseudonimo da re-identificare: ')
            try:
                id = re_identificazione(
                    pseudo_id=pseudo_id,
                    decrypt_key=RSA.import_key(
                        extern_key=prendisegreto('decrypt_key.txt'),
                        passphrase=input('Inserisci la passphrase per la chiave di decifratura: ')
                    ),
                    pseudo_pad=prendisegreto('pseudo_pad.txt')
                    )
            except Exception as e:
                print(f'Errore nel processo di re-identificazione: {str(e)}')
            
            print(f'ID originale: {id}')

        case _:
            print('Funzionalità non valida')