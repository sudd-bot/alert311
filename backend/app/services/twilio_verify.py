"""
Twilio Verification API service for phone number verification.
"""
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from typing import Optional
import logging

from ..core.config import settings

logger = logging.getLogger(__name__)


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

            if verification.status == "pending":
                logger.info(f"Verification code sent to {phone} (SID: {verification.sid})")
                return True
            logger.warning(f"Verification created with non-pending status: {verification.status}")
            return False
        except TwilioRestException as e:
            logger.error(f"Twilio verification send error: {e}")
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

            if verification_check.status == "approved":
                logger.info(f"Phone {phone} verified successfully")
                return True
            logger.info(f"Phone {phone} verification check failed with status: {verification_check.status}")
            return False
        except TwilioRestException as e:
            logger.error(f"Twilio verification check error: {e}")
            return False


twilio_verify_service = TwilioVerifyService()
