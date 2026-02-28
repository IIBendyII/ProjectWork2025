USE WorldFitLS;

-- Tabella Log
CREATE TABLE `Logs` (
    `Id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    `SmartCardId` VARCHAR(1000) NOT NULL,
    `PalestraId` INT NOT NULL,
    `Timestamp` DATETIME NOT NULL
);

-- Tabella Statistiche
CREATE TABLE `Statistiche` (
    `Id` BINARY(16) NOT NULL PRIMARY KEY,       -- Chiave Primaria in UUIDv4 binario
    `Sesso` CHAR(1) DEFAULT NULL,
    `FasciaEta` VARCHAR(100) DEFAULT NULL,
    `PalestraId` INT DEFAULT NULL,
    `DataIngresso` DATE DEFAULT NULL,
    `FasciaOraria` VARCHAR(100) DEFAULT NULL
);

-- Evento di Cancellazione Dati Trimestrale
SET GLOBAL event_scheduler = ON;
CREATE EVENT IF NOT EXISTS `Pulizia`
ON SCHEDULE EVERY 1 DAY
STARTS CURRENT_TIMESTAMP
ON COMPLETION PRESERVE
DO DELETE FROM `Logs` WHERE `Timestamp` < DATE_SUB(NOW(), INTERVAL 3 MONTH);