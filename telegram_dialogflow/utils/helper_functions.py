import os
import tempfile
import json

from google.cloud import dialogflow
from dotenv import load_dotenv, find_dotenv
import requests
from flask import request

load_dotenv(find_dotenv())

CREDENTIALS = json.loads(os.getenv('CREDENTIALS'))
PROJECT_ID = os.getenv('PROJECT_ID')

CREDENTIAL_FILE_PATH = os.path.join(
    tempfile.gettempdir(),
    'credentials.json'
)

if os.path.exists(CREDENTIAL_FILE_PATH):
    pass
else:
    with open(CREDENTIAL_FILE_PATH, 'w') as file:
        json.dump(CREDENTIALS, file)

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = CREDENTIAL_FILE_PATH

session_client = dialogflow.SessionsClient()


def detect_intent(session_id: str, query: str, language_code: str):
    session = session_client.session_path(PROJECT_ID, session_id)
    text_input = dialogflow.TextInput(text=query, language_code=language_code)
    query_input = dialogflow.QueryInput(text=text_input)
    response = session_client.detect_intent(
        request={'session': session, 'query_input': query_input}
    )
    return response.query_result.fulfillment_text


def detect_and_translate(query: str, target_language) -> tuple:
    url = 'https://api-free.deepl.com/v2/translate'
    payload = f'text={query}&target_lang={target_language}'.encode('utf-8')
    headers = {
        'Authorization': f'DeepL-Auth-Key {os.getenv("DEEPL_API_KEY")}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    response = requests.request('POST', url, data=payload, headers=headers)
    response = json.loads(response.text)
    detected_language = response['translations'][0]['detected_source_language']
    translation = response['translations'][0]['text']
    return detected_language, translation

def process_request(body: dict) -> dict:
    '''
    Process the incoming data of the Telegram request

    Parameters:
        - body(dict)

    Returns:
        - dict of these key and value 
        {
            'is_text': is_text,
            'is_chat_deleted': is_chat_deleted,
            'sender_id': sender_id,
            'message': message,
            'secret_token': secret_token,
            'first_name': first_name
        }
    '''
    body = request.get_json()
    message = ''
    is_bot = True
    is_text = False
    sender_id = None
    if 'message' in body.keys():
        sender_id = body['message']['from']['id']
        is_bot = body['message']['from']['is_bot']
        if 'text' in body['message'].keys():
            message += body['message']['text']
            is_text = True
    return {
        'is_text': is_text,
        'sender_id': sender_id,
        'message': message,
        'is_bot': is_bot
    }


def generate_response(query: str, sender_id: str) -> str:
    '''
    Process the incoming message for different command and generate a response string

    Parameters:
        - message(str): incoming message from Telegram

    Returns:
        - str: formated response for the command
    '''
    session_id = f'abcdefgh-{sender_id}'
    detected_language, translation = detect_and_translate(query, 'EN-US')
    dialogflow_response = detect_intent(session_id, translation, 'en-US')
    _, translation = detect_and_translate(dialogflow_response, detected_language)
    return translation
