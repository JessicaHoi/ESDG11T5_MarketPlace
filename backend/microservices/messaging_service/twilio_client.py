from twilio.rest import Client
import os

def send_sms(to_number: str, message: str):

    # Initialise the Twilio client using credentials from environment variables
    client = Client(
        os.environ.get("TWILIO_ACCOUNT_SID"),
        os.environ.get("TWILIO_AUTH_TOKEN")
    )
    
    # Use the Twilio API to send an SMS message
    client.messages.create(
        body=message,
        from_=os.environ.get("TWILIO_PHONE_NUMBER"),
        to=to_number
    )
    print(f"[✓] SMS sent to {to_number}")