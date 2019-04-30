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

def connect_google_sheet():
    GDriveJSON = './google-sheet.json'
    GSpreadSheet = 'line-chatbot'
    try:
        scope = ['https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/drive']
        key = SAC.from_json_keyfile_name(GDriveJSON, scope)
        gc = gspread.authorize(key)
        worksheet = gc.open(GSpreadSheet).worksheet('joke')
        return worksheet
    except Exception as ex:
        print('Error: ', ex)
        return 0

def score(col, content):
    message = TemplateSendMessage(
        alt_text='評分💯',
        template=ButtonsTemplate(
            text=content,
            actions=[
                PostbackTemplateAction(
                    label='笑死😂',
                    text='笑死😂',
                    data='action=response&feedback=5&col=' + str(col)
                ),
                PostbackTemplateAction(
                    label='尷尬🙂',
                    text='尷尬🙂',
                    data='action=response&feedback=3&col=' + str(col)
                ),
                PostbackTemplateAction(
                    label='超爛🤬',
                    text='超爛🤬',
                    data='action=response&feedback=1&col=' + str(col)
                ),
                MessageTemplateAction(
                    label='聽過🙉',
                    text='聽過🙉'
                )
            ]
        )
    )
    return message

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

@handler.add(PostbackEvent)
def handle_postback(event):
    data = event.postback.data.split('&')
    data = [x.split('=') for x in data]
    dic = {}
    for x in data:
        dic[x[0]] = x[1]
    if dic['action'] == 'why':
        worksheet = connect_google_sheet()
        message = score(dic['col'], worksheet.cell(dic['col'], 2).value)
        line_bot_api.reply_message(event.reply_token, message)
        return 0
    if dic['action'] == 'response':
        worksheet = connect_google_sheet()
        worksheet.update_cell(dic['col'], 3, int(worksheet.cell(dic['col'], 3).value) + int(dic['feedback']))
        worksheet.update_cell(dic['col'], 4, int(worksheet.cell(dic['col'], 4).value) + 1)
        message = TemplateSendMessage(
            alt_text='感謝評分😇',
            template=ButtonsTemplate(
                text='感謝你的評分～\n大家的評價是：' + worksheet.cell(dic['col'], 5).value + '分',
                actions=[
                    MessageTemplateAction(
                        label='再來一則笑話吧！',
                        text='再來一則笑話吧！',
                    ),
                    MessageTemplateAction(
                        label='掰掰👋',
                        text='掰掰👋'
                    )
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, message)
        return 0


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text
    print(msg)
    if '笑話' in msg:
        worksheet = connect_google_sheet()
        col = random.randint(1, len(worksheet.col_values(1)))
        content = worksheet.cell(col, 1).value
        include_answer = worksheet.cell(col, 2).value != ''
        if worksheet.cell(col, 2).value != '':
            message = TemplateSendMessage(
                alt_text='笑話😂',
                template=ConfirmTemplate(
                    text=content,
                    actions=[
                        MessageTemplateAction(
                            label='聽過🙉',
                            text='聽過🙉'
                        ),
                        PostbackTemplateAction(
                            label='為啥❓',
                            text='為啥❓',
                            data='action=why&col=' + str(col)
                        )
                    ]
                )
            )

            line_bot_api.reply_message(event.reply_token, message)
        else:
            line_bot_api.reply_message(event.reply_token, score(col, content))
        return 0
    if '聽過' in msg:
        message = TemplateSendMessage(
            alt_text='笑話😂',
            template=ConfirmTemplate(
                text='那要再來一則笑話嗎～？',
                actions=[
                    MessageTemplateAction(
                        label='❌',
                        text='不了 掰掰👋'
                    ),
                    MessageTemplateAction(
                        label='⭕',
                        text='再來一則笑話吧！',
                    )
                ]
            )
        )
        line_bot_api.reply_message(event.reply_token, message)
        return 0
    if '掰掰' in msg:
        message = TextSendMessage(text='想聽笑話的時候再來找我吧～👋！')
        line_bot_api.reply_message(event.reply_token, message)
        return 0


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.environ['PORT'])
