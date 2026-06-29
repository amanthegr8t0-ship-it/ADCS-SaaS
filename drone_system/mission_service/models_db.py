from sqlalchemy import Column, Integer, Float, String, DateTime, func
from database import Base

class MissionLog(Base):
    __tablename__ = "mission_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    drone_id = Column(Integer, nullable=False)
    customer_id = Column(String, nullable=False, default="default_customer")
    start_x = Column(Float)
    start_y = Column(Float)
    target_x = Column(Float)
    target_y = Column(Float)
    distance = Column(Float)
    battery_consumed = Column(Float)
    eta_seconds = Column(Float)
    status = Column(String, default="assigned")
    created_at = Column(DateTime, server_default=func.now())

class BillingRecord(Base):
    __tablename__ = "billing_records"
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(String, nullable=False, default="default_customer")
    drone_id = Column(Integer)
    mission_id = Column(Integer)
    units_consumed = Column(Float)
    created_at = Column(DateTime, server_default=func.now())
    