#!/bin/sh
set -e

ROOT_PASSWORD=$(cat /run/secrets/db_ls_root_password)
LOG_API_PASSWORD=$(cat /run/secrets/db_ls_api_password)

mysql -u root -p"$ROOT_PASSWORD" "$MYSQL_DATABASE" <<-EOSQL
-- Creazione Utente API
CREATE USER IF NOT EXISTS 'api'@'%' IDENTIFIED BY '$LOG_API_PASSWORD';

-- Assegnazione di soli privilegi di scrittura
GRANT INSERT ON \`Logs\` TO 'api'@'%';
GRANT INSERT ON \`Statistiche\` TO 'api'@'%';

FLUSH PRIVILEGES;
EOSQL