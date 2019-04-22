import os
import configparser
import random
from response import *
from flask import Flask, request, abort
from linebot import (LineBotApi, WebhookHandler)
from linebot.exceptions import (InvalidSignatureError)
from linebot.models import *

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
    if '真真' in msg:
        content = random.choice(wrong_name)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=content))
        return 0
    if msg == '臻臻':
        message = TemplateSendMessage(
            alt_text='來聊聊天吧！',
            template=ButtonsTemplate(
                title=random.choice(greeting_title),
                text='想聊點什麼嗎～？',
                actions=[
                    MessageTemplateAction(
                        label='關於臻臻',
                        text=random.choice(about_me)
                    ),
                    MessageTemplateAction(
                        label='打發時間',
                        text=random.choice(feel_bored)
                    )
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, message)
        return 0

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.environ['PORT'])
