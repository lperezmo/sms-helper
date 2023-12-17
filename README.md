# SMS Helper

## Overview
SMS Helper is an AI-powered, function-calling text assistant designed to process and respond to SMS messages. This application is written in Python and hosted through Azure Functions, utilizing Twilio as the SMS texting platform.

## Features
- Backend can call external tools to perform various functions, such as scheduling text and phone reminders. 
    - This functionality is supported through by allowing AI to call [flask-automated-reminders](https://github.com/lperezmo/flask-automated-reminders).
- Azure Functions allow us to write the backend purely in Python & easily deploy changes.
- Uses Twilio for SMS functionalities and integration.

## Deploy on Azure (VS Code)
1. Create an Azure account & create a function with all defaults (Python).
2. Create required environment variables on your function.
    - `ACCOUNT_SID`
    - `AUTH_TOKEN`
    - `TWIL_NUMBER`
    - `TWIL_EXAMPLE_NUMBER`
    - `OPENAI_API_KEY`
    - `SENTRY_DSN`
    
    <img src="images\azure_func_env_variables.png" alt="Setting Env variables in Azure">
2. In VS Code, install the Azure Functions extension (this will make it way easier).

    <img src="images\extension.png" alt="Extension" width="200">

3. Open the folder where this repo is located.
    * **(Optional)** Edit `__init__.py` code to use alternative helper if you want to send less messages per request.
    * **(Optional)** If using the 'schedule reminders' function, edit system message and API call to get the current time and date if you want something different than pacific time.
4. Go to the extension, and under 'Workspace' click on the little thunder sign and select 'Deploy to existing function...'.

    <img src="images\deploy.png" alt="Deploy">

5. Follow the prompts and done. Get your URL endpoint from Azure & load on Twilio.



## Load on Twilio
1. Create Twilio account.
2. Go to Phone Numbers > Manage > Active Numbers > Your number > Messaging configuration.
3. Set when a message comes in to use a webhook with your Azure Function endpoint (see image below)

    <img src="images\messaging_configuration.png" alt="Twilio config">

*Note: Your endpoint will look like this:
`https://YOUR-FUNCTION-NAME.azurewebsites.net/api/sms_helper`*

## Summary
1. Configure Azure & Twilio
2. Create function in Azure
3. Deploy
4. Load on Twilio
5. Text your new SMS bud

## Requirements
The project requires the following dependencies:
- `azure-functions==1.17.0`
- `twilio==8.10.2`
- `openai==1.3.2`
- `sentry-sdk`

## Contributing
Contributions to SMS Helper are welcome. Just submit a pull request and I'll take a look at it.

## License
 GPL-3.0 license 