from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean
from extensions import db



class UserSetting(db.Model):
    id = Column(Integer, primary_key=True)
    risk = Column(String)
    spot = Column(String)   # spot/margin




class Position(db.Model):
    id = Column(Integer, primary_key=True)
    symbol = Column(String)
    side = Column(String)
    price = Column(Float)
    time = Column(String)
    qty = Column(Float)
    status = Column(String)   # entry/close
    timeExit = Column(String)
    priceExit = Column(Float)
    stgNumber = Column(String)







