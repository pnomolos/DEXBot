import os
import json
import datetime
import sqlalchemy
from sqlalchemy import create_engine, Table, Column, String, Integer, MetaData, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from appdirs import user_data_dir
Base = declarative_base()

# For dexbot.sqlite file
appname = "dexbot"
appauthor = "ChainSquad GmbH"
storageDatabase = "dexbot.sqlite"


def mkdir_p(d):
    if os.path.isdir(d):
        return
    else:
        try:
            os.makedirs(d)
        except FileExistsError:
            return
        except OSError:
            raise


class Config(Base):
    __tablename__ = 'config'

    id = Column(Integer, primary_key=True)
    category = Column(String)
    key = Column(String)
    value = Column(String)

    def __init__(self, c, k, v):
        self.category = c
        self.key = k
        self.value = v

class Journal(Base):
    __tablename__ = 'journal'
    id = Column(Integer, primary_key=True)
    category = Column(String)
    key = Column(String)
    amount = Column(Float)
    stamp = Column(DateTime,default=datetime.datetime.now)
    
class Storage(dict):
    """ Storage class

        :param string category: The category to distinguish
                                different storage namespaces
    """
    def __init__(self, category):
        self.category = category

    def __setitem__(self, key, value):
        value = json.dumps(value)
        e = session.query(Config).filter_by(
            category=self.category,
            key=key
        ).first()
        if e:
            e.value = value
        else:
            e = Config(self.category, key, value)
            session.add(e)
        session.commit()

    def __getitem__(self, key):
        e = session.query(Config).filter_by(
            category=self.category,
            key=key
        ).first()
        if not e:
            return None
        else:
            return json.loads(e.value)

    def __delitem__(self, key):
        e = session.query(Config).filter_by(
            category=self.category,
            key=key
        ).first()
        session.delete(e)
        session.commit()

    def __contains__(self, key):
        e = session.query(Config).filter_by(
            category=self.category,
            key=key
        ).first()
        return bool(e)

    def items(self):
        es = session.query(Config).filter_by(
            category=self.category
        ).all()
        return [(e.key, e.value) for e in es]

    def clear(self):
        rows = session.query(Config).filter_by(
            category=self.category
        )
        for row in rows:
            session.delete(row)
            session.commit()

    def save_journal(self, amounts):
        now_t = datetime.datetime.now()
        for key, amount in amounts:
            e = Journal(key=key,category=self.category,amount=amount,stamp=now_t)
            session.add(e)
        session.commit()

    def query_journal(self, start, end_=None):
        """Query this bots journal
        start: datetime of start time
        end_: datetime of end (None means up to now)
        """
        return static_query_journal(self.category,start,end_)

def static_query_journal(category,start,end_):
    """Query journal without instantiating a bot
    """
    r = session.query(Journal).filter(Journal.category == category)
    if end_: 
        r = r.filter(Journal.stamp > start,Journal.stamp < end_)
    else:
        r = r.filter(Journal.stamp > start)
    return r.all()

        

# Derive sqlite file directory
data_dir = user_data_dir(appname, appauthor)
sqlDataBaseFile = os.path.join(data_dir, storageDatabase)

# Create directory for sqlite file
mkdir_p(data_dir)

# Obtain engine and session
engine = create_engine('sqlite:///%s' % sqlDataBaseFile, echo=False)
Session = sessionmaker(bind=engine)
session = Session()
Base.metadata.create_all(engine)
session.commit()

if __name__ == "__main__":
    storage = Storage("test")
    storage["foo"] = "bar"
    storage["foo1"] = "bar"
    storage["foo3"] = "bar"
    print(storage.items())
    print("foo" in storage)
    print("bar" in storage)
