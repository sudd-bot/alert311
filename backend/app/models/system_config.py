"""
System-wide configuration storage.
Used for SF 311 system tokens and other global settings.
"""
from sqlalchemy import Column, String, Integer
from .base import Base, TimestampMixin


class SystemConfig(Base, TimestampMixin):
    """Store system-wide configuration key-value pairs."""
    __tablename__ = "system_config"

    key = Column(String, primary_key=True, index=True)
    value = Column(String, nullable=False)  # JSON string for complex values
    
    # Optional: Track last update separately from created_at
    last_updated_timestamp = Column(Integer, nullable=True)  # Unix timestamp

    def __repr__(self):
        return f"<SystemConfig(key={self.key})>"
