from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class Report(Base, TimestampMixin):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer, ForeignKey("alerts.id", ondelete="CASCADE"), nullable=False)
    
    # 311 report ID from the API
    report_id = Column(String, unique=True, index=True, nullable=False)
    
    # Full report data from 311 API (JSON)
    report_data = Column(JSON, nullable=False)
    
    # SMS notification status
    sms_sent = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    alert = relationship("Alert", back_populates="reports")

    def __repr__(self):
        return f"<Report(id={self.id}, report_id={self.report_id}, sms_sent={self.sms_sent})>"
