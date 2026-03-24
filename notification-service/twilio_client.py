from twilio.rest import Client
import os

def send_sms(to_number: str, message: str):
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token  = os.environ.get("TWILIO_AUTH_TOKEN")
    from_number = os.environ.get("TWILIO_PHONE_NUMBER")

    client = Client(account_sid, auth_token)

    client.messages.create(
        body=message,
        from_=from_number,
        to=to_number
    )
    print(f"[✓] Reminder SMS sent to {to_number}")