"""
SMS alert service using Twilio for sending notifications.
"""
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from typing import Dict, Any

from ..core.config import settings


class SMSAlertService:
    def __init__(self):
        self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        self.from_number = settings.TWILIO_FROM_NUMBER
    
    def send_alert(self, to_phone: str, report_data: Dict[str, Any]) -> bool:
        """
        Send SMS alert about a matching 311 report.
        
        Args:
            to_phone: Recipient phone number
            report_data: 311 report data from API
        
        Returns:
            True if SMS sent successfully, False otherwise
        """
        message_body = self._format_alert_message(report_data)
        
        try:
            message = self.client.messages.create(
                body=message_body,
                from_=self.from_number,
                to=to_phone,
            )
            return message.sid is not None
        except TwilioRestException as e:
            print(f"SMS alert send error to {to_phone}: {e}")
            return False
    
    def _format_alert_message(self, report_data: Dict[str, Any]) -> str:
        """Format 311 report data into SMS message."""
        ticket_type = report_data.get("ticket_type_name", "Unknown")
        address = report_data.get("address", "Unknown location")
        description = report_data.get("description", "No description")
        report_id = report_data.get("id", "")
        created_at = report_data.get("created_at", "")
        
        message = f"🚨 Alert311: New {ticket_type} report\n\n"
        message += f"📍 {address}\n"
        message += f"📝 {description}\n"
        
        if created_at:
            message += f"🕐 {created_at}\n"
        
        if report_id:
            message += f"\nReport ID: {report_id}"
        
        return message


sms_alert_service = SMSAlertService()
