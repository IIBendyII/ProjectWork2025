# Utilizziamo la versione slim più recente
FROM python:3.14-slim-bookworm
# Creazione dell'utente per l'api
RUN useradd -m -u 1002 api_user
WORKDIR /api
COPY ./requirements.txt /api/requirements.txt
# Installazione dei requisiti per l'applicazione
RUN pip install -r /api/requirements.txt
COPY ./*.py /api
# Cambio di ownership dei file per l'applicazione
RUN chown -R api_user:api_user /api
# Escalation ad utente dell'api ed esecuzione del programma
USER api_user
CMD ["gunicorn", "api_server:app"]