from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped,mapped_column
from sqlalchemy import Integer, String, Float, DateTime, Boolean, func
from datetime import datetime

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
class NoiseLog(db.Model):
    __tablename__ = 'noise_log'
    id:Mapped[int]=mapped_column(Integer,primary_key=True)
    email:Mapped[str]=mapped_column(String(255),nullable=False)
    noise_level:Mapped[float]=mapped_column(Float,nullable=False)
    alert_sent:Mapped[bool]=mapped_column(Boolean,nullable=False)
    created_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),server_default=func.now())
    alert_attempted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True),nullable=True)