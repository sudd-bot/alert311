"""
Twilio Verification API service for phone number verification.
"""
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from typing import Optional

from ..core.config import settings


class TwilioVerifyService:
    def __init__(self):
        self.client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        self.verify_service_sid = settings.TWILIO_VERIFY_SERVICE_SID
    
    def send_verification(self, phone: str) -> bool:
        """
        Send verification code to phone number.
        Returns True if successful, False otherwise.
        """
        try:
            verification = self.client.verify.v2.services(
                self.verify_service_sid
            ).verifications.create(to=phone, channel="sms")
            
            return verification.status == "pending"
        except TwilioRestException as e:
            print(f"Twilio verification send error: {e}")
            return False
    
    def check_verification(self, phone: str, code: str) -> bool:
        """
        Verify the code sent to phone number.
        Returns True if code is correct, False otherwise.
        """
        try:
            verification_check = self.client.verify.v2.services(
                self.verify_service_sid
            ).verification_checks.create(to=phone, code=code)
            
            return verification_check.status == "approved"
        except TwilioRestException as e:
            print(f"Twilio verification check error: {e}")
            return False


twilio_verify_service = TwilioVerifyService()
