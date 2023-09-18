import os

from flask import Flask, request

from telegram_dialogflow.utils.telegram_api import send_message, set_webhook
from telegram_dialogflow.utils.helper_functions import process_request, generate_response


app = Flask(__name__)


@app.route('/')
def home():
    return 'All is well...'


@app.route('/telegram', methods=['POST'])
def telegram_api():
    try:
        if request.is_json:
            body = request.get_json()
            data = process_request(body)
            # Make sure the request has text and is not from a Telegram bot
            if data['is_text'] and not data['is_bot']:
                response = generate_response(data['message'], data['sender_id'])
                _ = send_message(data['sender_id'], response)
            # Message is from bot, send myself an alert
            elif data['is_bot']:
                response = 'I know you are a bot.'
                _ = send_message(data['sender_id'], response)
            # For everything else coming to the bot, IGNORE
            else:
                pass
            return 'OK', 200
        else:
            _ = send_message(os.getenv('ME'), 'Fire in the whole.')
    except:
        pass
    return 'OK', 200


@app.route('/set-telegram-webhook', methods=['POST'])
def set_telegram_webhook():
    if request.is_json:
        body = request.get_json()
        flag = set_webhook(body['url'], body['secret_token'])
        if flag:
            return 'OK', 200
        else:
            return 'BAD REQUEST', 400
    else:
        return 'BAD REQUEST', 400
