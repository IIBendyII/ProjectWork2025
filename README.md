# WorldFit Access
Applicazione di controllo degli accessi basato su tornelli e SmartCard per una catena di palestre fittizia (WorkFit) con sedi in tutta Europa.
Tale applicazione si affida ad un Database Gestionale esterno per la registrazione delle SmartCard e degli abbonamenti ad esse associati.

## Struttura
L'applicazione è suddivisa in due parti:
- un tornello/client frontend
- un'API backend hostata su cloud che risponde alle richieste del tornello

### Tornello
Client frontend, costituito da una pagina web (ancora in fase di sviluppo...). Il tornello comunica all'API l'ID della SmartCard ricevuta come parametro, unitamente all'ID della palestra in cui il tornello stesso si trova. Viene aggiunto anche un timestamp della richiesta ed una signature, composta dall'hash sha256 generato dalla concatenazione dei parametri precedentemente elencati assieme ad un segreto. Tale comunicazione avviene tramite una richiesta HTTP in POST.

A risposta ricevuta, il client controlla il seguente paio di parametri: un booleano che rappresenta la validità o meno dell'abbonamento associato alla SmartCard, ed una signature corrispondente all'hash sha256 generato dalla concatenazione dell'ID della SmartCard e dal timestamp di invio della richiesta.

Se l'abbonamento è valido e la signature corrisponde, il tornello garantisce l'accesso all'utente in palestra, altrimenti lo nega.

### API
Servizio di backend composto da due microservizi: 
- un'API che risponde alle richieste dei tornelli.
- un Database MySQL contenente i log di accesso alla palestra e le statistiche utili all'azienda per rilevare le preferenze dei clienti ed effettuare eventuali controlli anti-frode.

Quando l'API riceve una richiesta per prima cosa ne verifica la leggitimità, controllando che il timestamp non sia troppo vecchio e cercando di ricreare la signature. Se la richiesta è legittima, interroga il Database Gestionale per verificare se l'abbonamento associato alla SmartCard risulta valido, comunicando il risultato al Client.

Se l'abbonamento è risultato valido, registra inoltre l'accesso effettuando una query SQL tramite librerie ORM al Database di Log e Statistiche.

### Reti
Mentre tornello, API e Database Gestionale comunicano via internet, il Database di Log e Statistiche rimane isolato in una rete interna, accessibile solamente dall'API.

## Repository
Il repository del seguente progetto è strutturato in questo modo:
- **api**: Cartella contenente il files necessari per il build del container worldfit_api, ovvero l'API che risponde alle richieste del tornello della palestra.
- **db**: Cartella contenente il files necessari per il build del container db_logs_stats, ovvero il Database MySQL contenente i log di accesso e le statistiche.
- **external**: Cartella contenente files esterni all'applicazione backend. Attualmente sono presenti:
    - un modulo python contenenti funzioni per la re-identificazione degli pseudonimi e la generazione di chiavi asimmetriche.
    - uno script "proof of concept" di un tornello/client per l'applicazione, utilizzato per testare il backend.