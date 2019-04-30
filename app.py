import os
import configparser
import random
import datetime
import gspread
from flask import Flask, request, abort
from linebot import (LineBotApi, WebhookHandler)
from linebot.exceptions import (InvalidSignatureError)
from linebot.models import *
from oauth2client.service_account import ServiceAccountCredentials as SAC

app = Flask(__name__)

config = configparser.ConfigParser()
config.read('config.ini')

line_bot_api = LineBotApi(config['line_bot']['channel_access_token'])
handler = WebhookHandler(config['line_bot']['channel_secret'])

@app.route('/callback', methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info('Request body: ' + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'ok'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text
    print(msg)
    if '笑話' in msg:
        GDriveJSON = './line-chatbot-02e7b5e6bb4f.json'
        GSpreadSheet = 'line-chatbot'
        try:
            scope = ['https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/drive']
            key = SAC.from_json_keyfile_name(GDriveJSON, scope)
            gc = gspread.authorize(key)
            worksheet = gc.open(GSpreadSheet).worksheet('joke')
        except Exception as ex:
            print('Error: ', ex)
            return 0
        col = random.randint(1, len(worksheet.col_values(1)))
        content = worksheet.cell(col, 1).value
        line_bot_api.reply_message(event.reply_token,TextSendMessage(text=content))
        return 0

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.environ['PORT'])
