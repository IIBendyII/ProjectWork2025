// Configurazione
const API_ENDPOINT = 'http://127.0.0.1:8000';

let config = {
    gymId: '',
    apiKey: ''
};

// ========================
// UTILITY FUNCTIONS
// ========================

/**
 * Genera HMAC-SHA256
 */
async function generateHMAC(message, key) {
    const encoder = new TextEncoder();
    const keyData = encoder.encode(key);
    const messageData = encoder.encode(message);

    try {
        const cryptoKey = await crypto.subtle.importKey(
            'raw',
            keyData,
            { name: 'HMAC', hash: 'SHA-256' },
            false,
            ['sign']
        );

        const signature = await crypto.subtle.sign(
            'HMAC',
            cryptoKey,
            messageData
        );

        // Converti in hex
        const hexSignature = Array.from(new Uint8Array(signature))
            .map(b => b.toString(16).padStart(2, '0'))
            .join('');
        
        return hexSignature;
    } catch (error) {
        throw error;
    }
}

/**
 * Valida ID SmartCard
 */
function validateSmartCardId(id) {
    const pattern = /^[A-Z0-9]+$/;
    const isValid = pattern.test(id);
    
    return isValid;
}

// ========================
// UI FUNCTIONS
// ========================

/**
 * Mostra messaggio di stato
 */
function showStatus(message, type) {
    const statusDiv = document.getElementById('statusMessage');
    statusDiv.className = `status ${type}`;
    statusDiv.textContent = message;
    statusDiv.style.display = 'block';
	setTimeout(() => {
            statusDiv.style.display = 'none';
        }, 5000);

    /*if (type === 'error' || type === 'warning') {
        setTimeout(() => {
            statusDiv.style.display = 'none';
        }, 5000);
    }*/
}

/**
 * Apre il tornello
 */
function openTurnstile() {
    document.getElementById('turnstileBar').classList.add('open');
}

/**
 * Chiude il tornello
 */
function closeTurnstile() {
    document.getElementById('turnstileBar').classList.remove('open');
}

// ========================
// CONFIGURATION
// ========================

/**
 * Carica configurazione all'avvio
 */
window.onload = function() {
    const savedConfig = localStorage.getItem('turnstileConfig');
    config = JSON.parse(savedConfig);

    document.getElementById('configSection').classList.add('hidden');
    document.getElementById('accessSection').classList.remove('hidden');
    document.getElementById('displayGymId').textContent = config.gymId;
};

/**
 * Salva configurazione
 */
function saveConfig() {

    const gymId = document.getElementById('gymId').value.trim();
    const apiKey = document.getElementById('apiKey').value.trim();

    if (!gymId || !apiKey) {
        showStatus('Compila tutti i campi!', 'error');
        return;
    }

    config = { gymId, apiKey };
    localStorage.setItem('turnstileConfig', JSON.stringify(config));

    document.getElementById('configSection').classList.add('hidden');
    document.getElementById('accessSection').classList.remove('hidden');
    document.getElementById('displayGymId').textContent = config.gymId;

}

/**
 * Mostra configurazione
 */
function showConfig() {

    document.getElementById('accessSection').classList.add('hidden');
    document.getElementById('configSection').classList.remove('hidden');
    
    // Precompila i campi
    document.getElementById('gymId').value = config.gymId;
    document.getElementById('apiKey').value = config.apiKey;
}

// ========================
// ACCESS CHECK
// ========================

/**
 * Verifica accesso
 */
async function checkAccess() {

    const smartCardId = document.getElementById('smartCardId').value.trim().toUpperCase();
    const btn = document.getElementById('checkAccessBtn');

    // Validazione input
    if (!smartCardId) {
        showStatus('Inserisci un ID Smart Card!', 'error');
        return;
    }

    if (!validateSmartCardId(smartCardId)) {
        showStatus('ID Smart Card non valido! Usa solo lettere maiuscole e numeri.', 'error');
        return;
    }

    // Disabilita il pulsante
    btn.disabled = true;
    btn.innerHTML = '<span class="loading"></span> Verificando...';

    try {
        // Genera timestamp
        const timestamp = Date.now().toString();

        // Genera la signature per la richiesta
        const requestMessage = smartCardId + config.gymId + timestamp;
        const requestSignature = await generateHMAC(requestMessage, config.apiKey);

        // Prepara i dati da inviare
        const requestData = {
            IDSmartCard: smartCardId,
            IDPalestra: config.gymId,
            Timestamp: timestamp,
            Signature: requestSignature
        };

        // Invia richiesta POST all'API
        const response = await fetch(API_ENDPOINT, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });

        if (!response.ok) {
            throw new Error(`Errore HTTP: ${response.status} ${response.statusText}`);
        }

        // Parsing della risposta
        const data = await response.json();

        // Verifica che la risposta contenga i campi necessari
        if (typeof data.valido !== 'boolean') {
            throw new Error('Risposta API non valida: campo valido mancante');
        }
        if (typeof data.signature !== 'string') {
            throw new Error('Risposta API non valida: campo signature mancante');
        }
        if (!/^[a-z0-9]+$/.test(data.signature)) {
            throw new Error('Risposta API non valida: Campo "signature" contiene caratteri non validi');
        }

        // Verifica validità temporale (TOTP)
        const responseTime = parseInt(timestamp); //messo il timestamp iniziale
        const currentTime = Date.now();
        const timeDiff = Math.abs(currentTime - responseTime);
        const maxTimeDiff = 20000; // 20 secondi

        if (timeDiff > maxTimeDiff) {
            showStatus('⏱️ Risposta scaduta! Riprova.', 'error');
            closeTurnstile();
            return;
        }

        // Verifica la signature della risposta
        const responseMessage = smartCardId + timestamp;
        const expectedSignature = await generateHMAC(responseMessage, config.apiKey);

        if (data.signature !== expectedSignature) {
            showStatus('🚫 Signature non valida! Possibile tentativo di manomissione.', 'error');
            closeTurnstile();
            return;
        }

        // Controlla se l'accesso è garantito
        if (data.valido === true) {
            showStatus(`✅ ${'Accesso Consentito! Benvenuto!'}`, 'success');
            openTurnstile();
            
            // Chiudi il tornello dopo 5 secondi
            setTimeout(() => {
                closeTurnstile();
                document.getElementById('smartCardId').value = '';
            }, 5000);
        } else {
            showStatus(`🚫 Accesso Negato`, 'error');
            closeTurnstile();
        }

    } catch (error) {
        console.error('Errore completo:', error);
        
        let errorMessage = error.message;
        if (error.message.includes('Failed to fetch')) {
            errorMessage = 'Impossibile connettersi al server. Verifica che il server sia in esecuzione su ' + API_ENDPOINT;
        }
        
        showStatus(`❌ Errore: ${errorMessage}`, 'error');
        closeTurnstile();
    } finally {
        // Riabilita il pulsante
        btn.disabled = false;
        btn.innerHTML = 'Verifica Accesso';
    }
}

// ========================
// EVENT LISTENERS
// ========================

// Permetti l'invio con il tasto Enter
document.addEventListener('DOMContentLoaded', function() {
    const smartCardInput = document.getElementById('smartCardId');
    if (smartCardInput) {
        smartCardInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                checkAccess();
            }
        });

        // Converti automaticamente in maiuscolo
        smartCardInput.addEventListener('input', function(e) {
            const original = e.target.value;
            e.target.value = e.target.value.toUpperCase();
        });
    }
});
