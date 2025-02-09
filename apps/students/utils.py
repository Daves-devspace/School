import logging
import re
import requests
from django.conf import settings
from apps.Manage.utils import get_sms_provider_token

class MobileSasaAPI:
    BASE_URL_SINGLE = "https://api.mobilesasa.com/v1/send/message"
    BASE_URL_BULK = "https://api.mobilesasa.com/v1/send/bulk"
    BASE_URL_BULK_PERSONALIZED = "https://api.mobilesasa.com/v1/send/bulk-personalized"

    def __init__(self):
        # Fetch the API token and sender_id using your method.
        token_data = get_sms_provider_token()
        if token_data:
            self.api_token = token_data.get('api_token')
            self.sender_id = token_data.get('sender_id')
        else:
            raise ValueError("No API token or sender ID found. Please check the token setup.")

        # Debug output (you can remove these prints or use logging instead)
        print("Using API Token:", self.api_token)
        print("Using Sender ID:", self.sender_id)

        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        self.logger = logging.getLogger(__name__)

    def clean_phone_number(self, phone):
        """Standardize phone number format to match API requirements."""
        if not phone:
            return None
        # Remove any non-digit characters.
        phone = ''.join(filter(str.isdigit, str(phone)))
        # Handle Kenyan numbers (e.g., convert 0712345678 to 254712345678)
        if phone.startswith('0'):
            phone = '254' + phone[1:]
        elif phone.startswith('+'):
            phone = phone[1:]
        elif len(phone) == 9:
            phone = '254' + phone
        return phone

    def send_single_sms(self, message, phone):
        """
        Sends a single SMS to the specified phone number.
        Returns a dictionary with the API response.
        """
        cleaned_phone = self.clean_phone_number(phone)
        if not cleaned_phone:
            return {"status": False, "message": "Invalid phone number"}

        payload = {
            "senderID": self.sender_id,
            "message": message,
            "phone": cleaned_phone,
        }

        self.logger.debug(f"Sending single SMS. Payload: {payload}")

        try:
            response = requests.post(self.BASE_URL_SINGLE, headers=self.headers, json=payload)
            response.raise_for_status()
            self.logger.debug(f"Single SMS response: {response.text}")
            response_data = response.json()
            return response_data if isinstance(response_data, dict) else {"status": False, "message": "Unexpected response format"}
        except requests.RequestException as e:
            error_msg = {"status": False, "message": f"Request error: {str(e)}"}
            self.logger.error(f"Single SMS error: {error_msg}")
            return error_msg
        except ValueError as e:
            error_msg = {"status": False, "message": f"JSON parse error: {str(e)}"}
            self.logger.error(f"JSON parse error: {error_msg}")
            return error_msg

    def send_bulk_sms(self, message, phone_numbers):
        """
        Sends bulk SMS to the provided phone numbers in batches of 50.
        According to the API documentation, the payload should be:
            {
                "senderID": "MOBILESASA",
                "message": "Your message here",
                "phones": "254707XXXXXX,25411XXXXX,25470XXXXXX"
            }
        """
        chunk_size = 50
        success_count = 0
        errors = []

        if not self.sender_id or not self.api_token:
            raise ValueError("Missing API credentials")

        # Clean and filter phone numbers.
        cleaned_numbers = [self.clean_phone_number(phone) for phone in phone_numbers]
        cleaned_numbers = [phone for phone in cleaned_numbers if phone]

        for i in range(0, len(cleaned_numbers), chunk_size):
            chunk = cleaned_numbers[i:i + chunk_size]
            phones = ",".join(chunk)
            payload = {
                "senderID": self.sender_id,
                "message": message,
                "phones": phones,
            }
            self.logger.debug(f"Sending bulk SMS batch {i // chunk_size + 1}. Payload: {payload}")

            try:
                response = requests.post(self.BASE_URL_BULK, headers=self.headers, json=payload)
                response.raise_for_status()
                try:
                    response_data = response.json()
                except Exception as parse_error:
                    self.logger.error(f"Error parsing JSON for batch {i // chunk_size + 1}: {response.text}")
                    errors.append({
                        "message": "Invalid API response format",
                        "response": response.text,
                        "phones": chunk
                    })
                    continue

                self.logger.debug(f"Bulk SMS response for batch {i // chunk_size + 1}: {response_data}")
                if response_data.get("status"):
                    success_count += len(chunk)
                else:
                    errors.append({
                        "code": response_data.get("responseCode"),
                        "message": response_data.get("message", "Unknown error"),
                        "phones": chunk
                    })
            except requests.RequestException as e:
                error_msg = {"message": f"Request error: {str(e)}", "phones": chunk}
                self.logger.error(f"Bulk SMS request error for batch {i // chunk_size + 1}: {error_msg}", exc_info=True)
                errors.append(error_msg)

        return success_count, errors

    def send_bulk_personalized_sms(self, personalized_messages):
        """
        Sends personalized bulk SMS to multiple recipients.
        Expects a payload like:
        {
            "senderID": "MOBILESASA",
            "messageBody": [
                {
                    "phone": "2547078614xx",
                    "message": "Personalized message"
                },
                ...
            ]
        }
        """
        try:
            chunk_size = 50
            success_count = 0
            errors = []
            if not self.sender_id or not self.api_token:
                raise ValueError("Missing API credentials")

            for i in range(0, len(personalized_messages), chunk_size):
                chunk = personalized_messages[i:i + chunk_size]
                payload = {
                    "senderID": self.sender_id,  # Added senderID as required
                    "messageBody": [
                        {
                            "phone": msg['phone'],
                            "message": msg['message']
                        } for msg in chunk
                    ]
                }
                self.logger.debug(f"Sending personalized SMS batch {i // chunk_size + 1}. Payload: {payload}")
                response = requests.post(self.BASE_URL_BULK_PERSONALIZED, headers=self.headers, json=payload)
                response.raise_for_status()

                try:
                    response_data = response.json()
                except Exception as parse_error:
                    self.logger.error(
                        f"Error parsing JSON for personalized batch {i // chunk_size + 1}: {response.text}")
                    errors.append({
                        "message": "Invalid API response format",
                        "response": response.text,
                        "failed_chunk": chunk
                    })
                    continue

                self.logger.debug(f"Personalized SMS response for batch {i // chunk_size + 1}: {response_data}")
                if response_data.get('status'):
                    success_count += len(chunk)
                else:
                    errors.append({
                        "code": response_data.get("responseCode"),
                        "message": response_data.get("message", "Unknown error"),
                        "failed_chunk": chunk
                    })
            return success_count, errors

        except Exception as e:
            self.logger.error(f"SMS sending failed: {str(e)}", exc_info=True)
            return 0, [str(e)]
