"""
SMS alert service using Twilio for sending notifications.
"""
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from typing import Dict, Any
import logging

from ..core.config import settings

logger = logging.getLogger(__name__)


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
            if message.sid:
                logger.info(f"SMS alert sent successfully to {to_phone} (SID: {message.sid})")
                return True
            logger.warning(f"SMS alert created but no SID returned for {to_phone}")
            return False
        except TwilioRestException as e:
            logger.error(f"SMS alert send error to {to_phone}: {e}")
            return False
    
    def _format_alert_message(self, report_data: Dict[str, Any]) -> str:
        """
        Format 311 report data into SMS message.

        Handles both formats from SF 311 API:
        - GraphQL tickets: { ticketType: { name }, location: { address }, submittedAt, publicId, status }
        - Legacy format: { ticket_type_name, address, description, created_at, id }
        """
        # Extract type name from nested ticketType object (GraphQL) or direct field (legacy)
        ticket_type_obj = report_data.get("ticketType", {})
        if isinstance(ticket_type_obj, dict):
            ticket_type = ticket_type_obj.get("name", "Unknown")
        else:
            ticket_type = ticket_type_obj if ticket_type_obj else report_data.get("ticket_type_name", "Unknown")

        # Extract address from nested location object (GraphQL) or direct field (legacy)
        location_obj = report_data.get("location", {})
        if isinstance(location_obj, dict):
            address = location_obj.get("address", "Unknown location")
        else:
            address = location_obj if location_obj else report_data.get("address", "Unknown location")

        # Extract ID from publicId (GraphQL) or id (legacy)
        report_id = report_data.get("publicId") or report_data.get("id", "")
        created_at = report_data.get("submittedAt") or report_data.get("openedAt") or report_data.get("created_at", "")
        status = report_data.get("status", "").lower()

        message = f"🚨 Alert311: New {ticket_type}\n\n"
        message += f"📍 {address}\n"

        # Add status if available
        if status:
            status_label = "OPEN" if status == "open" else status.upper()
            message += f"⚠️ Status: {status_label}\n"

        if created_at:
            message += f"🕐 {created_at}\n"

        if report_id:
            message += f"\nCase #{report_id}"
        else:
            # Fallback to internal ID
            internal_id = report_data.get("id")
            if internal_id:
                message += f"\nID: {internal_id}"

        return message


sms_alert_service = SMSAlertService()
