from sqlalchemy import Column, Integer, String, Boolean, Enum
from sqlalchemy.orm import relationship
import enum

from .base import Base, TimestampMixin


class AccountType(str, enum.Enum):
    FREE = "free"
    PAID = "paid"


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    phone = Column(String, unique=True, index=True, nullable=False)
    verified = Column(Boolean, default=False, nullable=False)
    account_type = Column(Enum(AccountType), default=AccountType.FREE, nullable=False)
    
    # Twilio verification SID for tracking verification status
    verification_sid = Column(String, nullable=True)
    
    # SF 311 API OAuth tokens (per-user)
    sf311_access_token = Column(String, nullable=True)
    sf311_refresh_token = Column(String, nullable=True)
    sf311_token_expires_at = Column(Integer, nullable=True)  # Unix timestamp
    
    # Relationships
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, phone={self.phone}, verified={self.verified})>"
