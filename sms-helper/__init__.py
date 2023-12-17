import os
import logging
import sentry_sdk
import azure.functions as func
import __app__.helper as helper
# Use alternative helper to send less messages
# import __app__.alternative_helper as alternative_helper
from sentry_sdk.integrations.serverless import serverless_function

#------------------------------------#
# Sentry for debugging
#------------------------------------#
SENTRY = os.environ["SENTRY_DSN"]
sentry_sdk.init(
    dsn=SENTRY,
    # For initial testing capture 100% of transactions for monitoring
    traces_sample_rate=1.0,
)

#------------------------------------#
# Main function
#------------------------------------#
@serverless_function
def main(req: func.HttpRequest) -> func.HttpResponse:
    # These variables are from the Twilio request.
    send_to = req.params["From"]
    send_from = req.params["To"]
    incoming_message = req.params["Body"].lower().strip()

    # Reply to the user based on the incoming message
    helper.process_incoming_message(os.environ["SECURITY_PIN"], 
                                        send_to, 
                                        send_from, 
                                        incoming_message)

    return func.HttpResponse(
        "You can text this number again if you need more information. (LPM)", status_code=200
    )
    
    #--------------------------------------------------------------------------#
    # To reduce the number of messages you could use the 'alternative_helper'
    # This one returns the response message as the HttpResponse. 
    #--------------------------------------------------------------------------#
    
    # response_for_user = alternative_helper.process_incoming_message(os.environ["SECURITY_PIN"],
    #                                                                     send_to,
    #                                                                     send_from,
    #                                                                     incoming_message)
    # return func.HttpResponse(response_for_user, status_code=200)