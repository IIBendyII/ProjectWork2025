# 🏋️‍♂️ WorldFit Access
Applicazione di controllo degli accessi basata su tornelli e SmartCard per **WorldFit**, una catena fittizia di palestre con sedi in tutta Europa.
Tale applicazione si affida ad un Database Gestionale esterno per la registrazione delle SmartCard e degli abbonamenti ad esse associati.

---

## 📑 Indice
- [Architettura del Sistema](#-architettura-del-sistema)
  - [Tornello (Client Frontend)](#tornello-client-frontend)
  - [API (Backend)](#api-backend)
  - [Infrastruttura di Rete](#infrastruttura-di-rete)
- [Sicurezza e Autenticazione](#-sicurezza-e-autenticazione)
- [Struttura del Repository](#-struttura-del-repository)
- [Installazione e Avvio](#-installazione-e-avvio)
- [Sviluppi Futuri](#-sviluppi-futuri)

---

## 🏛 Architettura del Sistema

L'applicazione è progettata seguendo un'architettura a microservizi ed è suddivisa in due componenti principali: il client (tornello) e il servizio di backend (API + Database).

### Tornello (Client Frontend)
Un client simulato (attualmente tramite script/pagina web) che rappresenta il tornello d'ingresso della palestra. 
Il tornello effettua una richiesta `POST` all'API inviando:
- L'**ID della SmartCard**.
- L'**ID della palestra** in cui è installato.
- Un **timestamp** della richiesta per prevenire attacchi di tipo *replay*.
- Una **signature** di sicurezza (Firma HAMC usando hash SHA-256 generata dalla concatenazione dei parametri precedenti ed un *secret* condiviso).

Alla ricezione della risposta, il tornello verifica la validità dell'abbonamento e una firma di ritorno prima di sbloccare l'accesso.

### API (Backend)
Servizio backend ospitato in cloud che funge da intermediario tra i tornelli e i database. Si compone di:
1. **API Gateway/Service**: Riceve le richieste dai tornelli, valida le firme crittografiche (signature e timestamp) e interroga il Database Gestionale per verificare lo stato dell'abbonamento.
2. **Database Log & Statistiche (MySQL)**: Se l'accesso viene autorizzato, l'API utilizza un ORM per registrare l'ingresso su questo database in una tabella di Log, insieme a statistiche utili all'azienda per rilevare le preferenze dei clienti ed effettuare eventuali controlli anti-frode. A tal scopo, i timestamp dei Log sono tutti in formato UTC, mentre per i dati delle Statistiche i timestamp vengono convertiti nel fuso orario della nazione della Palestra su cui è avvenuto l'ingresso.

### Infrastruttura di Rete
- **Comunicazione Esterna**: Il Tornello, l'API e il Database Gestionale comunicano tramite Internet pubblico utilizzando protocolli sicuri.
- **Rete Interna Isolata**: Il Database dei Log e delle Statistiche risiede in una rete privata (Docker network) inaccessibile dall'esterno, raggiungibile esclusivamente dall'API backend per garantire la massima sicurezza dei dati.

---

## 🔒 Sicurezza e Autenticazione

La comunicazione tra il tornello e l'API è protetta da un meccanismo di firma digitale HMAC.
* **Richiesta (Client ➡️ API)**: Viene validata tramite signature HMAC utilizzando SHA-256, creato con `ID_SmartCard + ID_Palestra + Timestamp + Secret`. Se la firma non coincide o il timestamp è troppo vecchio, la richiesta viene respinta.
* **Risposta (API ➡️ Client)**: Il client verifica una firma di risposta generata HMAC SHA-256 di `ID_SmartCard + Timestamp di invio`.

Le smartcard vengono **pseudonimizzate** prima del salvataggio nella tabella di Log del **Database Log & Statistiche** utilizzando RSA, in modo che la chiave di decifratura non venga mai pubblicata online. I dati nella tabella delle Statistiche vengono opportunamente Anonimizzati tramite **k-anonimity**.

---

## 📂 Struttura del Repository

Il repository è organizzato per isolare i diversi container Docker e gli script di utilità:
* 📁 **`api/`**: Contiene il codice sorgente e il `Dockerfile` necessari per la build del container `worldfit_api` (il core backend del sistema).
* 📁 **`client/`**: Contiene il codice HTML, CSS e Javascript del Client
* 📁 **`db/`**: Contiene gli script di inizializzazione e configurazione per la build del container `db_logs_stats` (Database MySQL).
* 📁 **`external/`**: Moduli esterni e tool di testing, tra cui:
  * Un modulo Python con funzioni per la re-identificazione degli pseudonimi e la generazione di chiavi asimmetriche.
  * Uno script *Proof of Concept* (PoC) che funge da tornello fittizio per testare localmente le risposte del backend.
* 📁 **`threatmodel/`**: Threat model dell'applicazione sviluppato utilizzando OWASP Threat Dragon
* 📄 **`docker-compose.yml`**: File di orchestrazione per avviare l'intera infrastruttura (API + Database) con un solo comando.