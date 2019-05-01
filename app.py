import os
import configparser
import random
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
    """Return the google worksheet."""
    google_sheet = './google-sheet.json'
    sheet = 'line-chatbot'
    try:
        scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        key = SAC.from_json_keyfile_name(google_sheet, scope)
        gc = gspread.authorize(key)
        worksheet = gc.open(sheet).worksheet('joke')
        return worksheet
    except Exception as ex:
        print('Error: ', ex)
        return 0

def main_message():
    message = TemplateSendMessage(
        alt_text='主選單👩',
        template=CarouselTemplate(
            columns=[
                CarouselColumn(
                    thumbnail_image_url='https://images.pexels.com/photos/1831234/pexels-photo-1831234.jpeg',
                    title='笑話',
                    text='🔸心情不美麗就來則笑話吧～！\n🔸也可以輸入數字聽指定笑話',
                    actions=[
                        MessageTemplateAction(
                            label='想聽笑話',
                            text='來一則笑話吧～！'
                        ),
                        MessageTemplateAction(
                            label='分享笑話',
                            text='我想跟你分享笑話'
                        )
                    ]
                ),
                CarouselColumn(
                    thumbnail_image_url='https://images.pexels.com/photos/19670/pexels-photo.jpg',
                    title='尚未開放',
                    text='🙈',
                    actions=[
                        MessageTemplateAction(
                            label='1⃣',
                            text='尚未開放～'
                        ),
                        MessageTemplateAction(
                            label='2⃣',
                            text='尚未開放～'
                        )
                    ]
                )
            ]
        )
    )
    return message

def joke_message(col=None):
    """Return the joke message."""
    worksheet = connect_google_sheet()
    count = len(worksheet.col_values(1))
    if not col:
        col = random.randint(1, count)
    if col < 1 or col > count:
        return TextSendMessage(text='超出範圍了～')
    content = worksheet.cell(col, 1).value
    include_answer = worksheet.cell(col, 2).value != ''
    if worksheet.cell(col, 2).value != '':
        message = TemplateSendMessage(
            alt_text='笑話😂',
            template=ConfirmTemplate(
                text=content,
                actions=[
                    MessageTemplateAction(
                        label='🔄',
                        text='再來一則笑話吧！'
                    ),
                    PostbackTemplateAction(
                        label='❓',
                        text='❓',
                        data='action=why&col=' + str(col)
                    )
                ]
            )
        )

        return message
    return score_message(col, content)

def score_message(col, content):
    """Return the score message."""
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
                    text='再來一則笑話吧！'
                )
            ]
        )
    )
    return message

@app.route('/callback', methods=['POST'])
def callback():
    """Callback event."""
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
    """Postback event."""
    data = event.postback.data.split('&')
    data = [x.split('=') for x in data]
    dic = {}
    for x in data:
        dic[x[0]] = x[1]
    if dic['action'] == 'why':
        worksheet = connect_google_sheet()
        message = score_message(dic['col'], worksheet.cell(dic['col'], 2).value)
        line_bot_api.reply_message(event.reply_token, message)
        return 0
    if dic['action'] == 'response':
        worksheet = connect_google_sheet()
        score = int(worksheet.cell(dic['col'], 3).value) + int(dic['feedback'])
        count = int(worksheet.cell(dic['col'], 4).value) + 1
        worksheet.update_cell(dic['col'], 3, score)
        worksheet.update_cell(dic['col'], 4, count)
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

@handler.add(FollowEvent)
def handle_follow(event):
    message = TextSendMessage(text='Hi 😜\n呼叫臻臻就可以秀出主選單喔！')
    line_bot_api.reply_message(event.reply_token, [message, main_message()])
    return 0

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """Handle with users' message."""
    msg = event.message.text
    print(msg)
    if msg.isnumeric():
        message = joke_message(int(msg))
        line_bot_api.reply_message(event.reply_token, message)
        return 0

    if '臻臻' in msg:
        line_bot_api.reply_message(event.reply_token, main_message())
        return 0

    if '分享笑話' in msg:
        message = TextSendMessage(text='目前還沒有開放這個功能😓')
        line_bot_api.reply_message(event.reply_token, message)
        return 0

    if '笑話' in msg:
        message = joke_message()
        line_bot_api.reply_message(event.reply_token, message)
        return 0

    if '掰掰' in msg:
        message = TextSendMessage(text='想聽笑話的時候再來找我吧～👋！')
        line_bot_api.reply_message(event.reply_token, message)
        return 0

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.environ['PORT'])
