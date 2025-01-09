import requests
from django.conf import settings


class MobileSasaAPI:
    BASE_URL_BULK = "https://api.mobilesasa.com/v1/send/bulk"
    BASE_URL_SINGLE = "https://api.mobilesasa.com/v1/send/message"

    def __init__(self):
        self.api_token = settings.MOBILESASA_API_TOKEN
        self.sender_id = settings.MOBILESASA_SENDER_ID
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

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
        for i in range(0, len(phone_numbers), batch_size):
            batch = phone_numbers[i:i + batch_size]
            phones = ",".join(batch)
            payload = {
                "senderID": self.sender_id,
                "message": message,
                "phones": phones,
            }
            try:
                response = requests.post(self.BASE_URL_BULK, headers=self.headers, json=payload)
                response.raise_for_status()
                responses.append(response.json())
            except requests.RequestException as e:
                responses.append({"status": False, "message": str(e)})
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
        payload = {
            "senderID": self.sender_id,
            "message": message,
            "phone": phone,
        }
        try:
            response = requests.post(self.BASE_URL_SINGLE, headers=self.headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return {"status": False, "message": str(e)}
