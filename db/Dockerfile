#Meglio inserire una build precisa per evitare problemi?
FROM mysql:latest
# Creazione dell'utente per il Database
RUN useradd -m -u 1001 ls_user
# Cambio di ownership dei files utilizzati dal Database
RUN chown -R ls_user:ls_user /var/lib/mysql && chown -R ls_user:ls_user /var/run/mysqld
USER ls_user