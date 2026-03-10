from sqlalchemy import Column, BigInteger, String, SmallInteger, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id              = Column(BigInteger, primary_key=True, index=True, autoincrement=True)
    email           = Column(String(255), unique=True, nullable=False, index=True)
    username        = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active       = Column(SmallInteger, default=1)
    created_at      = Column(DateTime, default=datetime.utcnow)
    last_login      = Column(DateTime, nullable=True)

