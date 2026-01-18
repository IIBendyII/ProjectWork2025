USE WorldFitLS;

-- Tabella Log
CREATE TABLE `Logs` (
    `Id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `SmartCardId` VARCHAR(1000) NOT NULL, -- Pseudonimizzato
    `PalestraId` INT NOT NULL,
    `Timestamp` DATETIME NOT NULL -- Proveniente dal Client
);

-- Tabella Statistiche
CREATE TABLE `Statistiche` (
    `Id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `Sesso` CHAR(1) DEFAULT NULL,
    `FasciaEta` VARCHAR(100) DEFAULT NULL,       -- "Fascia di età" (Es: 20-30)
    `NomePalestra` VARCHAR(1000) DEFAULT NULL,
    `DataIngresso` DATE DEFAULT NULL,
    `FasciaOraria` VARCHAR(100) DEFAULT NULL    -- "Fascia Oraria di Accesso" (Es: 18:00-20:00)
);

-- Evento di Cancellazione Dati Trimestrale
CREATE EVENT `Pulizia`
ON SCHEDULE EVERY 1 DAY 
DO DELETE FROM `Logs` WHERE `Timestamp` < DATE_SUB(NOW(), INTERVAL 3 MONTH);
