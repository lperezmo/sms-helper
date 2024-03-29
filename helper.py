import os
import json
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

#------------------------------------#
# OpenAI and Twilio Clients
#------------------------------------#
ai_client = OpenAI()
CLIENT = Client(ACCOUNT_SID, AUTH_TOKEN)

#------------------------------------#
# Security check
#------------------------------------#
def process_incoming_message(PIN, send_to, send_from, incoming_message):
    """
    Process incoming message & generate a reply.
    
    Parameters
    ----------
    PIN : str
        Security PIN
    send_to : str
        Phone number to send text to
    send_from : str
        Phone number to send text from
    incoming_message : str
        Incoming message from Twilio
    
    Returns
    -------
    Send message using Twilio
    """
    if incoming_message.strip() == PIN:
        send_initial_text(send_to, send_from)
    else:
        messages = CLIENT.messages.list(from_=send_to, to=send_from)
        sent_pin = False
        for message in messages:
            if message.body.strip() == PIN:
                sent_pin = True
        if sent_pin:
            send_follow_up_text(send_to, send_from, incoming_message)
        else:
            send_message("Please provide security PIN to continue", send_to, send_from)

#------------------------------------#
# Welcome text
#------------------------------------#
def send_initial_text(send_to, send_from):
    outgoing_message = f"""Welcome to Hess Services new AI assistant.
        - I can schedule calls and text reminders for you.
        - I can answer any questions, within reason.
        - Text 'hess' to see this message again"""
    send_message(outgoing_message, send_to, send_from)


#------------------------------------#
# Current time
#------------------------------------#
def get_time():
    """Robustly get the current time from an API."""
    max_retries = 3
    attempts = 0
    while attempts < max_retries:
        try:
            response = requests.get('http://worldtimeapi.org/api/timezone/America/Los_Angeles')
            response.raise_for_status()  # This will raise an exception for HTTP error codes

            res = response.json()
            datetime = res.get('datetime')
            abbreviation = res.get('abbreviation')
            day_of_week = res.get('day_of_week')

            if datetime and abbreviation and day_of_week is not None:
                return f"{datetime} {abbreviation} day of the week {day_of_week}"
            else:
                raise ValueError("Incomplete time data received")
            
        except (requests.RequestException, ValueError) as e:
            attempts += 1
            if attempts == max_retries:
                return "Failed to get time after several attempts."

#-----------------------------------------#
# Generate JSON body to schedule reminder
#-----------------------------------------#
def schedule_reminder(natural_language_request, number_from):
    """Generate JSON body to schedule reminder"""
    sys_prompt = """Your job is to create the JSON body for an API call to schedule texts and calls. Then , you will schedule the text or call for the user will request based on pacific time (given in pacific time). If user asks for a reminder today at 6 pm that is 18:00 (24 hour notation). Set the 'to_number' to the users number. Always set twilio = True.

    Example JSON:
    {
    "time": "18:20",
    "day": "2023-11-27",
    "message_body": "This is the reminder body!",
    "call": "True",
    "twilio": "True",
    "to_number": "+15554443333"
    }

    Another example:
    {
        "time":"23:46",
        "day":"2023-11-27",
        "message_body":"text reminder to check email",
        "to_number":"+15554443333",
        "twilio":"True",
        "call":"False"
    }
    """
    curr_time = get_time()
    ai_client = OpenAI()
    completion = ai_client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=[
                {"role": "system", "content": f"{sys_prompt}"},
                {"role": "user", "content": f"{natural_language_request}. <User's number> {number_from} <Current Time>: {curr_time}"},
            ],
            response_format={ "type": "json_object" },
        )
    
    return json.loads(completion.choices[0].message.content)

#------------------------------------#
# Follow up text
#------------------------------------#
def send_follow_up_text(send_to, send_from, incoming_message):
    """Send follow up text
    
    Parameters
    ----------
    send_to : str
        Phone number to send text to
    send_from : str
        Phone number to send text from
    incoming_message : str
        Incoming message from Twilio
    """
    if incoming_message == 'hess':
        send_initial_text(send_to, send_from)
    else:
        tools = [
                    {
                        "type": "function",
                        "function": {
                        "name": "schedule_reminder",
                        "description": "Schedule a reminder using natural language",
                        "parameters": {
                            "type": "object",
                            "properties": {
                            "natural_language_request": {
                                "type": "string",
                                "description": "Requested reminder in natural language. Example: 'Remind me to call mom tomorrow at 6pm' or 'Send me a message with a Matrix quote on wednesday at 8am'",
                                },
                            "number_from": {
                                "type": "string",
                                "description": "Phone number to send text from. Example: '+15554443333'"
                                }
                            },
                            "required": ["natural_language_request"],
                        },
                        }
                    }
                ]
        #----------------------------------------------------#
        # AI w/tools - reply or use tools to schedule reminder
        #----------------------------------------------------#
        completion = ai_client.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=[
                {"role": "system", "content": f"You are an AI assistant that can schedule reminders (like calls and texts) if asked to do so. Be informative, funny, and helpful, and keep your messages clear and short. To schedule reminder just pass a natural language request to the function 'schedule_reminder'"},
                {"role": "user", "content": f"{incoming_message}"}
            ],
            tools=tools,
            tool_choice="auto"
        )
        message = completion.choices[0].message.content
        if message==None:
            message = "Just a minute while I schedule your reminder."
        send_message(message, send_to, send_from)
        
        #----------------------------------------------------#
        # If tools are called, call the tools function
        #----------------------------------------------------#
        if completion.choices[0].message.tool_calls:
            if completion.choices[0].message.tool_calls[0].function.name == 'schedule_reminder':
                args = completion.choices[0].message.tool_calls[0].function.arguments
                args_dict = json.loads(args)
                try:
                    json_body = schedule_reminder(**args_dict)
                    url_endpoint = os.environ["AMAZON_ENDPOINT"]
                    headers = {'Content-Type': 'application/json'}
                    
                    #--------------------------------#
                    # Schedule reminder
                    #--------------------------------#
                    response = requests.post(url_endpoint, headers=headers, data=json.dumps(json_body))
                    if response.status_code == 200:
                        send_message("Your reminder has been scheduled.", send_to, send_from)
                except Exception as e:
                    logging.error(f"Error: {e}")

#------------------------------------#
# Send message using Twilio
#------------------------------------#
def send_message(outgoing_message, send_to, send_from):
    message = CLIENT.messages.create(
        body=outgoing_message, from_=send_from, to=send_to,
    )
    return func.HttpResponse(
        "", status_code=200
    )
