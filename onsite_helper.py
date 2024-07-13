import os
import json
import boto3
import logging
import requests
from openai import OpenAI
import azure.functions as func
from twilio.rest import Client

#------------------------------------#
# Load environment variables
#------------------------------------#
ACCOUNT_SID = os.environ["ACCOUNT_SID"]
AUTH_TOKEN = os.environ["AUTH_TOKEN"]
SEC_PIN = os.environ["SECURITY_PIN"]

#------------------------------------#
# Twilio Client
#------------------------------------#
CLIENT = Client(ACCOUNT_SID, AUTH_TOKEN)

#------------------------------------#
# Initialize SQS client
#------------------------------------#
sqs = boto3.client('sqs')
queue_url = os.environ["AMAZON_QUEUE_ENDPOINT"]

def save_sms_to_sqs(sender, message, date_sent=None):
    """
    Save SMS message details into SQS queue.
    """
    try:
        message_body = {
            'sender': sender,
            'message': message,
            'date_sent': date_sent if date_sent else datetime.utcnow().isoformat()
        }
        response = sqs.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message_body)
        )
        return f"Message from {sender} saved successfully."
    except Exception as e:
        logging.error(f"Error saving message to SQS: {e}")
        return f"Error saving message. {e}"

#------------------------------------#
# Security check
#------------------------------------#
def process_incoming_message(PIN, incoming_message, send_to, send_from):
    """
    Generate a reply based on the incoming message.
    
    Parameters
    ----------
    PIN : str
        Security PIN
    incoming_message : str
        Incoming message from Twilio
    
    Returns
    -------
    message : str
        Reply message
    """
    if incoming_message.strip() == PIN:
        return """Welcome to the new internal Hess Services SMS AI service.
  - I can lookup general information about jobs, parts, sales orders,
  - among others.
  - Text 'about' to see this message again"""
    else:
        messages = CLIENT.messages.list(from_=send_to, to=send_from)
        sent_pin = False
        for message in messages:
            if message.body.strip() == PIN:
                sent_pin = True
        if sent_pin:
            follow_up_reply = get_follow_up_text(send_to=send_to,
                                    send_from=send_from,
                                    incoming_message=incoming_message)
            return follow_up_reply
        else:
            return f"Please provide security PIN to continue."

#------------------------------------#
# Follow up text
#------------------------------------#
def get_follow_up_text(send_to, send_from, incoming_message):
    """Send follow up text
    
    Parameters
    ----------
    send_to : str
        Phone number to send text to
    send_from : str
        Phone number to send text from
    incoming_message : str
        Incoming message from Twilio
        
    Returns
    -------
    message : str
        Response from the AI to the user
    """
    if incoming_message == 'about':
        return """Welcome to the new Luis AI reminder assistant.
    - I can schedule calls and text reminders for you.
    - I can answer any questions, within reason.
    - Text 'about' to see this message again"""
    else:
        result = save_sms_to_sqs(send_to, incoming_message)
        return 'Processing reply...'
