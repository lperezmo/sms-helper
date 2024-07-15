import os
import logging
import sentry_sdk
import azure.functions as func
# import __app__.helper as helper
# import __app__.alternative_helper as alternative_helper
import __app__.onsite_helper as onsite_helper
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


    #--------------------------------------------------------------------------#
    # Uncomment for use with onsite_helper.py
    # This saves messages to AWS database, and then the messages are
    # processed internally at HSI. This way we can reply with internal
    # info + use local AI models + secure databases.
    #--------------------------------------------------------------------------#
    # Extracting media URLs from Twilio request
    num_media = int(req.params.get("NumMedia", 0))
    image_urls = []
    audio_urls = []

    for i in range(num_media):
        media_content_type = req.params.get(f"MediaContentType{i}")
        media_url = req.params.get(f"MediaUrl{i}")
        
        if media_content_type and media_url:
            if media_content_type.startswith("image/"):
                image_urls.append(media_url)
            elif media_content_type.startswith("audio/"):
                audio_urls.append(media_url)

    pin = onsite_helper.SEC_PIN
    res = onsite_helper.process_incoming_message(
                PIN=pin,
                incoming_message=incoming_message,
                send_to=send_to,
                send_from=send_from,
                image_urls=image_urls,
                audio_urls=audio_urls
        )
    return func.HttpResponse(res, status_code=200)


    #--------------------------------------------------------------------------#
    # Uncomment for use with helper.py
    #--------------------------------------------------------------------------#
    # helper.process_incoming_message(os.environ["SECURITY_PIN"], 
    #                                     send_to, 
    #                                     send_from, 
    #                                     incoming_message)

    # return func.HttpResponse(
    #     "You can text this number again if you need more information. (LPM)", status_code=200
    # )
    
    #--------------------------------------------------------------------------#
    # Uncomment for use with alternative_helper.py
    # Reduces the number of messages send, returns the response message 
    # as the HttpResponse. 
    #--------------------------------------------------------------------------#
    # pin = alternative_helper.SEC_PIN
    # res = alternative_helper.process_incoming_message(PIN=pin,
    #             incoming_message=incoming_message,
    #             send_to=send_to,
    #             send_from=send_from)
    # return func.HttpResponse(res, status_code=200)