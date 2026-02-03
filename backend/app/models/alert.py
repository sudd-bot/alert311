from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class Alert(Base, TimestampMixin):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Address info
    address = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    # Report type (311 ticket_type_id)
    # For "parking on sidewalk": 963f1454-7c22-43be-aacb-3f34ae5d0dc7
    report_type_id = Column(String, nullable=False)
    report_type_name = Column(String, nullable=False)  # Human-readable name
    
    # Indexed for cron job queries (finding active alerts)
    active = Column(Boolean, default=True, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="alerts")
    reports = relationship("Report", back_populates="alert", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Alert(id={self.id}, address={self.address}, type={self.report_type_name})>"
