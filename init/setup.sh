#!/bin/bash
set -e

LOG_API_PASSWORD=$(cat /run/secrets/mysql_api_password)

mysql -u api -p LOG_API_PASSWORD <<EOF
-- Crea il database se non esiste
CREATE DATABASE IF NOT EXISTS WorldFitLogs; /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `WorldFitLogs`;

-- TABELLA LOG (Pseudonimizzata)
CREATE TABLE Log (
    `Id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY, -- ID SmartCard (Pseudonimizzato)
    `SmartCardId` varchar(1000) NOT NULL,
    `Timestamp` DATETIME NOT NULL, -- Timestamp (Proveniente dal Client)
    `IdPalestra` INT NOT NULL,                    -- Id Palestra (Es: 14)
    
    -- Campo tecnico extra per sapere se è entrato o no (utile per il debug) #Inserire?
    -- esito_accesso TINYINT(1) DEFAULT 1, 
    
    -- Indice per velocizzare i controlli #Inserire?
    -- INDEX idx_smartcard (id_smartcard)
);

-- TABELLA STATISTICHE (Anonimizzata k-anonymity)
CREATE TABLE Statistiche (
    `Id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `sesso` CHAR(1) DEFAULT Null,               -- "Sesso" (M/F)
    `FasciaEta` VARCHAR(20) DEFAULT Null,       -- "Fascia di età" (Es: 20-30)
    `NomePalestra` VARCHAR(100) DEFAULT Null,   -- "Nome Palestra" (Es: Palestra12)
    `Data` DATE DEFAULT Null,                   -- "Data di Accesso" (Es: 2025-12-01)
    `FasciaOraria` VARCHAR(50) DEFAULT Null,    -- "Fascia Oraria" (Es: 18:00-20:00)
);

-- EVENTO DI CANCELLAZIONE DATI TRIMESTRALE
CREATE EVENT Pulizia
ON SCHEDULE EVERY 1 DAY 
DO DELETE FROM Log WHERE `Timestamp` < DATE_SUB(NOW(), INTERVAL 3 MONTH);
EOF