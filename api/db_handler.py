'''Modulo Python contenente classi e metodi per l'interazione con il database gestionale ed il databse di logs e statistiche'''

from sqlalchemy import create_engine, Integer, CHAR, String, Date, DateTime, ForeignKey, select, insert
from sqlalchemy.orm import DeclarativeBase, Session, Mapped, mapped_column
from typing import Optional
from datetime import date, datetime
import logging
from sys import stdout

# Impostazione di Logging per stampare eventuali eccezioni nei Docker Logs
logger = logging.getLogger(__name__)
handler = logging.StreamHandler(stdout)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

class DB_handler:
    """Classe base per l'interazione con un database generico"""
    def __init__(self,database_uri:str):
        # creazione dell'engine, la "Fabbrica" che crea le comunicazioni con il DB
        # https://docs.sqlalchemy.org/en/20/orm/quickstart.html#create-an-engine
        self.engine = create_engine(database_uri, echo=False) #DA METTERE A FALSE A FINE TESTING. echo stampa su terminale tutte le operazioni sql

class Base (DeclarativeBase):
    '''classe base per i template di tabelle: https://docs.sqlalchemy.org/en/20/tutorial/metadata.html'''
    pass

class LogsAndStats(DB_handler):
    '''Classe specifica per integargire con il DB Log e statistiche'''

    class Log(Base):
        '''Mapped Class per interagire con la tabella dei logs'''
        __tablename__ = 'Logs'

        id: Mapped[int] = mapped_column("Id", Integer, primary_key=True, autoincrement=True)
        smart_card_id: Mapped[str] = mapped_column("SmartCardId", String(1000))
        palestra_id: Mapped[int] = mapped_column("PalestraId", Integer)
        timestamp: Mapped[datetime] = mapped_column("Timestamp", DateTime)

        def __repr__(self) -> str:
            return f"<Log(id={self.id}, smart_card_id={self.smart_card_id}, palestra_id={self.palestra_id}, timestamp='{self.timestamp}')>"
    
    class Stat(Base):
        '''Mapped Class per interagire con la tabella delle statistiche'''
        __tablename__ = 'Statistiche'

        # Optional[] indica che il campo può essere NULL nel database (DEFAULT NULL)
        id: Mapped[int] = mapped_column("Id", Integer, primary_key=True, autoincrement=True)
        sesso: Mapped[Optional[str]] = mapped_column("Sesso", CHAR(1))
        fascia_eta: Mapped[Optional[str]] = mapped_column("FasciaEta", String(100))
        palestra_id: Mapped[Optional[str]] = mapped_column("PalestraId", Integer)
        data_ingresso: Mapped[Optional[date]] = mapped_column("DataIngresso", Date)
        fascia_oraria: Mapped[Optional[str]] = mapped_column("FasciaOraria", String(100))

        def __repr__(self) -> str:
            return f"<Stat(id={self.id}, sesso={self.sesso}, fascia_eta='{self.fascia_eta}', palestra_id='{self.palestra_id}'" \
                f", data_ingresso={self.data_ingresso}, fascia_oraria='{self.fascia_oraria}')>"
    
    def insert_log(self, smart_card_id:str, palestra_id:int, timestamp:datetime):
        """Funzione per scrittura nella tabella 'Logs' del database"""
        with self.engine.connect() as connection:
            try:
                stmt = insert(self.Log).values(
                    smart_card_id = smart_card_id,
                    palestra_id = palestra_id,
                    timestamp=timestamp)
                connection.execute(stmt)
                connection.commit()
                logger.debug("Scrittura Tabella Log avvenuta con successo")

            except Exception as e:
                logger.error("Errore durante l'inserimento riga in tabella Log: %s", str(e))
    
    def insert_stats(self, sesso:str, fascia_eta:str, palestra_id:int, data_ingresso:date, fascia_oraria:str):
        """Funzione per scrittura nella tabella 'Statistiche' del database"""
        with self.engine.connect() as connection:
            try:
                stmt = insert(self.Stat).values(
                    sesso = sesso,
                    fascia_eta = fascia_eta,
                    palestra_id = palestra_id,
                    data_ingresso = data_ingresso,
                    fascia_oraria = fascia_oraria)
                connection.execute(stmt)
                connection.commit()
                logger.debug("Scrittura Tabella Statistiche avvenuta con successo")

            except Exception as e:
                logger.error("Errore durante l'inserimento riga in tabella Statistiche: %s", str(e))

class Gestionale(DB_handler):
    '''Classe specifica per interagire con il DB Gestionale'''

    class Cliente(Base):
        '''Mapped Class per interagire con la tabella dei clienti'''
        __tablename__ = "Clienti"
        
        id: Mapped[int] = mapped_column("Id", Integer, primary_key=True, autoincrement=True)
        cognome: Mapped[Optional[str]] = mapped_column("Cognome", String(1000))
        nome: Mapped[Optional[str]] = mapped_column("Nome", String(1000))
        sesso: Mapped[Optional[str]] = mapped_column("Sesso", CHAR(1))
        data_nascita: Mapped[Optional[date]] = mapped_column("DataNascita", Date)
        luogo_nascita: Mapped[Optional[str]] = mapped_column("LuogoNascita", String(1000))
        stato_nascita: Mapped[Optional[str]] = mapped_column("StatoNascita", String(1000))
        indirizzo_residenza: Mapped[Optional[str]] = mapped_column("IndirizzoResidenza", String(1000))
        luogo_residenza: Mapped[Optional[str]] = mapped_column("LuogoResidenza", String(1000))
        stato_residenza: Mapped[Optional[str]] = mapped_column("StatoResidenza", String(1000))
        smart_card_id: Mapped[Optional[str]] = mapped_column("SmartCardId", String(1000))

        def __repr__(self) -> str:
            return f"<Cliente(id={self.id}, cognome='{self.cognome}', nome='{self.nome}', sesso={self.sesso}, data_nascita={self.data_nascita}" \
                f", luogo_nascita='{self.luogo_nascita}', stato_nascita='{self.stato_nascita}', indirizzo_residenza='{self.indirizzo_residenza}'" \
                f", luogo_residenza='{self.luogo_residenza}', stato_residenza='{self.stato_residenza}', smart_card_id={self.smart_card_id})>"
    
    class Abbonamento(Base):
        '''Mapped Class per interagire con la tabella degli abbonamenti'''
        __tablename__ = "Abbonamenti"

        id: Mapped[int] = mapped_column("Id", Integer, primary_key=True, autoincrement=True)
        id_cliente: Mapped[int] = mapped_column("IdCliente", ForeignKey("Clienti.Id"))
        valido_dal: Mapped[date] = mapped_column("ValidoDal", Date)
        valido_al: Mapped[date] = mapped_column("ValidoAl", Date)

        def __repr__(self) -> str:
            return f"<Abbonamento(id={self.id}, id_cliente={self.id_cliente}, valido_dal={self.valido_dal}, valido_al={self.valido_al})>"

    class Palestra(Base):
        '''Mapped Class per interagire con la tabella delle palestre'''
        __tablename__ = "Palestre"

        id: Mapped[int] = mapped_column("Id", Integer, primary_key=True, autoincrement=True)
        nome: Mapped[Optional[str]] = mapped_column("Nome", String(1000))
        indirizzo: Mapped[Optional[str]] = mapped_column("Indirizzo", String(1000))
        luogo: Mapped[Optional[str]] = mapped_column("Luogo", String(1000))
        stato: Mapped[Optional[str]] = mapped_column("Stato", String(1000))

        def __repr__(self) -> str:
            return f"<Palestra(id={self.id}, nome='{self.nome}', indirizzo='{self.indirizzo}', luogo='{self.luogo}', stato='{self.stato}')>"
        
    def select_client(self, smart_card_id:str) -> Cliente:
        '''Funzione che data una SmartCardID, restituisce il primo oggetto Cliente corrispondente'''
        try:
            with Session(self.engine) as session:
                stmt = select(self.Cliente).where(self.Cliente.smart_card_id == smart_card_id)
                return session.scalar(stmt)
        except Exception as e:
            logger.error("Errore nel recupero di un Cliente dal DB Gestionale: %s", str(e))

    def select_abbonamenti(self, id_cliente:str) -> list:
        '''Funzione che dato un ID della tabella dei Clienti, recupera una lista di abbonamenti ad esso associati'''
        try:
            with Session(self.engine) as session:
                stmt = select(self.Abbonamento).where(self.Abbonamento.id_cliente == id_cliente)
                return session.scalars(stmt).all()
        except Exception as e:
            logger.error("Errore nel recupero degli abbonamenti dal DB Gestionale: %s", str(e))

    def select_palestra(self, palestra_id:str) -> Palestra:
        '''Funzione che dato un ID di una palestra, restituisce il primo oggetto palestra corrispondente'''
        try:
            with Session(self.engine) as session:
                stmt = select(self.Palestra).where(self.Palestra.id == palestra_id)
                return session.scalar(stmt)
        except Exception as e:
            logger.error("Errore nel recupero di una Palestra dal DB Gestionale: %s", str(e))