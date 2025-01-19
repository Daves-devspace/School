import logging
import requests
from django.conf import settings
from apps.management.models import ReportCard
from apps.students.models import StudentParent


class MobileSasaAPI:
    BASE_URL_BULK = "https://api.mobilesasa.com/v1/send/bulk"
    BASE_URL_SINGLE = "https://api.mobilesasa.com/v1/send/message"
    BASE_URL_BULK_PERSONALIZED = "https://api.mobilesasa.com/v1/send/bulk-personalized"

    def __init__(self):
        self.api_token = settings.MOBILESASA_API_TOKEN
        self.sender_id = settings.MOBILESASA_SENDER_ID
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        self.logger = logging.getLogger(__name__)

    def clean_phone_number(self, phone):
        """Standardize phone number format to match API requirements.txt."""
        if not phone:
            return None

        # Remove any non-digit characters
        phone = ''.join(filter(str.isdigit, str(phone)))

        # Handle Kenyan numbers
        if phone.startswith('0'):  # Convert 0712345678 to 254712345678
            phone = '254' + phone[1:]
        elif phone.startswith('+'):  # Remove + if present
            phone = phone[1:]
        elif len(phone) == 9:  # Add country code if missing
            phone = '254' + phone

        return phone

    def send_bulk_sms(self, message, phone_numbers):
        """
        Sends bulk SMS to the provided phone numbers in batches of 50.
        Args:
            message (str): The SMS message to send.
            phone_numbers (list): List of phone numbers in E.164 format (e.g., '2547XXXXXXX').
        Returns:
            list: A list of responses for each batch.
        """
        responses = []
        batch_size = 50

        # Clean all phone numbers first
        cleaned_numbers = [self.clean_phone_number(phone) for phone in phone_numbers]
        cleaned_numbers = [phone for phone in cleaned_numbers if phone]  # Remove None values

        for i in range(0, len(cleaned_numbers), batch_size):
            batch = cleaned_numbers[i:i + batch_size]
            phones = ",".join(batch)
            payload = {
                "senderID": self.sender_id,
                "message": message,
                "phones": phones,
            }

            self.logger.debug(f"Sending bulk SMS batch {i // batch_size + 1}. Payload: {payload}")

            try:
                response = requests.post(self.BASE_URL_BULK, headers=self.headers, json=payload)
                response.raise_for_status()
                response_data = response.json()
                self.logger.debug(f"Bulk SMS response: {response_data}")
                responses.append(response_data)
            except requests.RequestException as e:
                error_msg = {"status": False, "message": f"Request error: {str(e)}"}
                self.logger.error(f"Bulk SMS error: {error_msg}")
                responses.append(error_msg)
        return responses

    def send_single_sms(self, message, phone):
        """
        Sends a single SMS to the specified phone number.
        Args:
            message (str): The SMS message to send.
            phone (str): Phone number in E.164 format (e.g., '2547XXXXXXX').
        Returns:
            dict: A response from the API with the status of the SMS delivery.
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
            response_data = response.json()
            self.logger.debug(f"Single SMS response: {response_data}")
            return response_data
        except requests.RequestException as e:
            error_msg = {"status": False, "message": f"Request error: {str(e)}"}
            self.logger.error(f"Single SMS error: {error_msg}")
            return error_msg

    def send_bulk_personalized_sms(self, personalized_messages):
        """
        Sends bulk personalized SMS where each phone number gets a different message.
        Args:
            personalized_messages (list): List of dicts with 'phone' and 'message' keys
        Returns:
            dict: API response with status and message
        """
        # Clean phone numbers and format message body
        message_body = []
        for msg in personalized_messages:
            cleaned_phone = self.clean_phone_number(msg['phone'])
            if cleaned_phone:
                message_body.append({
                    "phone": cleaned_phone,
                    "message": msg['message']
                })

        if not message_body:
            return {
                'status': False,
                'message': 'No valid phone numbers provided',
                'responseCode': '0400'
            }

        # Construct payload as per API documentation
        payload = {
            "senderID": self.sender_id,
            "messageBody": message_body
        }

        self.logger.info(f"Sending personalized SMS to {len(message_body)} recipients")
        self.logger.debug(f"Request payload: {payload}")

        try:
            response = requests.post(
                self.BASE_URL_BULK_PERSONALIZED,
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()

            # Log the complete response
            self.logger.debug(f"API Response Status: {response.status_code}")
            self.logger.debug(f"API Response Body: {response.text}")

            # Parse response
            response_data = response.json()

            if response.status_code == 200 and response_data.get('status'):
                self.logger.info(f"SMS sent successfully. Bulk ID: {response_data.get('bulkId')}")
                return [{
                    'status': True,
                    'message': 'SMS sent successfully',
                    'bulkId': response_data.get('bulkId')
                }]
            else:
                error_msg = response_data.get('message', 'Unknown error')
                self.logger.error(f"API Error: {error_msg}")
                return [{
                    'status': False,
                    'message': error_msg,
                    'responseCode': response_data.get('responseCode', 'Unknown')
                }]

        except requests.RequestException as e:
            error_msg = f"Request failed: {str(e)}"
            self.logger.error(error_msg)
            return [{
                'status': False,
                'message': error_msg,
                'responseCode': '0500'
            }]
        except ValueError as e:
            error_msg = f"Failed to parse JSON response: {str(e)}"
            self.logger.error(error_msg)
            return [{
                'status': False,
                'message': error_msg,
                'responseCode': '0500'
            }]


def format_and_send_sms(active_students, term, exam_type, message_template):
    """
    Formats the message for each student and sends an SMS to their parents.
    """
    if not message_template:
        return {"error": "Message template is not provided."}

    personalized_messages = []
    for student in active_students:
        try:
            report_card = ReportCard.objects.get(student=student, term=term, exam_type=exam_type)
        except ReportCard.DoesNotExist:
            continue

        student_parent = StudentParent.objects.filter(student=student).first()
        if not student_parent or not student_parent.parent.mobile:
            continue

        try:
            message = message_template.format(
                parent_name=student_parent.parent.first_name,
                student_name=student.first_name,
                total_marks=report_card.total_marks(),
                exam_type=exam_type.name,
                term=term.name
            )
        except KeyError as e:
            return {"error": f"Message formatting error: {e}. Please check your template."}

        personalized_messages.append({
            "phone": student_parent.parent.mobile,
            "message": message
        })

    if not personalized_messages:
        return {"warning": "No valid parents with mobile numbers found to send SMS."}

    # Use the MobileSasaAPI class to send the messages
    api = MobileSasaAPI()
    response = api.send_bulk_personalized_sms(personalized_messages)

    # Handle the response
    if response[0].get('status'):
        return {"success": f"{len(personalized_messages)} SMS sent successfully."}
    else:
        return {"error": f"Failed to send SMS: {response[0].get('message')}"}