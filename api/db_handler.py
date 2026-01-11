'''Modulo Python contenente classi e metodi per l'interazione con il database gestionale ed il databse di logs e statistiche'''

from sqlalchemy import create_engine, Integer, CHAR, String, Date, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, Session, Mapped, mapped_column
from typing import Optional
from datetime import date, datetime

class DB_handler:
    """Classe base per l'interazione con un database generico"""
    def __init__(self,database_uri):
        self.engine = create_engine(database_uri, echo=False) # creazione dell'engine, la "Fabbrica" che crea le comunicazioni con il DB: https://docs.sqlalchemy.org/en/20/orm/quickstart.html#create-an-engine
        self.base = declarative_base() # classe base per i template di tabelle: https://docs.sqlalchemy.org/en/20/tutorial/metadata.html

class LogsAndStats(DB_handler):
    '''Classe specifica per integargire con il DB Log e statistiche'''

    class Log(DB_handler.base):
        '''Mapped Class per interagire con la tabella dei logs'''
        __tablename__ = 'Logs'

        id: Mapped[int] = mapped_column("Id", Integer, primary_key=True, autoincrement=True)
        smart_card_id: Mapped[str] = mapped_column("SmartCardId", String(1000))
        palestra_id: Mapped[int] = mapped_column("PalestraId", Integer)
        timestamp: Mapped[datetime] = mapped_column("Timestamp", DateTime)

        def __repr__(self) -> str:
            return f"<Log(id={self.id}, smart_card_id={self.smart_card_id}, palestra_id={self.palestra_id}, timestamp='{self.timestamp}')>"
    
    class Stat(DB_handler.base):
        '''Mapped Class per interagire con la tabella delle statistiche'''
        __tablename__ = 'Statistiche'

        # Optional[] indica che il campo può essere NULL nel database (DEFAULT NULL)
        id: Mapped[int] = mapped_column("Id", Integer, primary_key=True, autoincrement=True)
        sesso: Mapped[Optional[str]] = mapped_column("Sesso", CHAR(1))
        fascia_eta = Mapped[Optional[str]] = mapped_column("FasciaEta", String(100))
        nome_palestra = Mapped[Optional[str]] = mapped_column("NomePalestra", String(1000))
        data_ingresso = Mapped[Optional[date]] = mapped_column("DataIngresso", Date)
        fascia_oraria = Mapped[Optional[str]] = mapped_column("FasciaOraria", String(100))

        def __repr__(self) -> str:
            return f"<Stat(id={self.id}, sesso={self.sesso}, fascia_eta='{self.fascia_eta}', nome_palestra='{self.nome_palestra}'" \
                f", data_ingresso={self.data_ingresso}, fascia_oraria='{self.fascia_oraria}')>"
    
    def insert_log(self, smart_card_id:str, palestra_id:int, timestamp:datetime):
        """Funzione per scrittura nella tabella 'Logs' del database"""
        with Session(self.engine) as session:
            try:
                nuovo_log = self.Log(
                    smart_card_id=smart_card_id,
                    palestra_id=palestra_id,
                    timestamp=timestamp
                )

                session.add(nuovo_log)
                session.commit()
                print(f"+ Dato inserito con successo: {nuovo_log}") #da mettere in un log

            except Exception as e:
                session.rollback() # Annulla in caso di errore
                print(f"- Errore durante l'inserimento: {e}") #da mettere in un log
    
    def insert_stats(self, sesso:str, fascia_eta:str, nome_palestra:str, data_ingresso:date, fascia_oraria:str):
        """Funzione per scrittura nella tabella 'Statistiche' del database"""
        # TDB

class Gestionale(DB_handler):
    '''Classe specifica per interagire con il DB Gestionale'''

    class Cliente(DB_handler.base):
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
    
    class Abbonamento(DB_handler.base):
        '''Mapped Class per interagire con la tabella degli abbonamenti'''
        __tablename__ = "Abbonamenti"

        id: Mapped[int] = mapped_column("Id", Integer, primary_key=True, autoincrement=True)
        id_cliente: Mapped[int] = mapped_column("IdCliente", ForeignKey("Clienti.Id"))
        valido_dal: Mapped[date] = mapped_column("ValidoDal", Date)
        valido_al: Mapped[date] = mapped_column("ValidoAl", Date)

        def __repr__(self) -> str:
            return f"<Abbonamento(id={self.id}, id_cliente={self.id_cliente}, valido_dal={self.valido_dal}, valido_al={self.valido_al})>"

    class Palestra(DB_handler.base):
        '''Mapped Class per interagire con la tabella delle palestre'''
        __tablename__ = "Palestre"

        id: Mapped[int] = mapped_column("Id", Integer, primary_key=True, autoincrement=True)
        nome: Mapped[Optional[str]] = mapped_column("Nome", String(1000))
        indirizzo: Mapped[Optional[str]] = mapped_column("Indirizzo", String(1000))
        luogo: Mapped[Optional[str]] = mapped_column("Luogo", String(1000))
        stato: Mapped[Optional[str]] = mapped_column("Stato", String(1000))

        def __repr__(self) -> str:
            return f"<Palestra(id={self.id}, nome='{self.nome}', indirizzo='{self.indirizzo}', luogo='{self.luogo}', stato='{self.stato}')>"
        
    def select_client(self, smart_card_id:str):
        '''Funzione'''
        # TBD