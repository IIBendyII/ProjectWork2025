USE WorldFitLogs;

-- Tabella Log
CREATE TABLE `Logs` (
    `Id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `SmartCardId` VARCHAR(1000) NOT NULL, -- Pseudonimizzato
    `Timestamp` DATETIME NOT NULL, -- Proveniente dal Client
    `IdPalestra` INT NOT NULL
);

-- Tabella Statistiche
CREATE TABLE `Statistiche` (
    `Id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `Sesso` CHAR(1) DEFAULT Null,
    `FasciaEta` VARCHAR(20) DEFAULT Null,       -- "Fascia di età" (Es: 20-30)
    `NomePalestra` VARCHAR(100) DEFAULT Null,
    `Data` DATE DEFAULT Null,                   -- "Data di Accesso"
    `FasciaOraria` VARCHAR(50) DEFAULT Null    -- "Fascia Oraria di Accesso" (Es: 18:00-20:00)
);

-- Evento di Cancellazione Dati Trimestrale
CREATE EVENT `Pulizia`
ON SCHEDULE EVERY 1 DAY 
DO DELETE FROM `Log` WHERE `Timestamp` < DATE_SUB(NOW(), INTERVAL 3 MONTH);
