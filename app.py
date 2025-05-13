# 必要なモジュールを呼び出し
from flask import Flask, request, abort
import os
from openai import OpenAI
from linebot.v3.webhook import WebhookHandler
from linebot.v3.messaging import MessagingApi, Configuration, ApiClient
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage
from linebot.v3.exceptions import InvalidSignatureError

app = Flask(__name__)

# 環境変数から読み込む
LINE_CHANNEL_ACCESS_TOKEN = os.environ['LINE_CHANNEL_ACCESS_TOKEN']
LINE_CHANNEL_SECRET = os.environ['LINE_CHANNEL_SECRET']
OPENAI_API_KEY = os.environ['OPENAI_API_KEY']

# OpenAI と LINE をセットアップ
client = OpenAI(api_key=OPENAI_API_KEY)
configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# ① Webhook 受信
@app.route('/callback', methods=['POST'])
def callback():
    sig = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, sig)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# ② テキストが来たら OpenAI 呼び出し
@handler.add(MessageEvent, message=TextMessageContent)
def handle_text(event):
    user_text = event.message.text
    try:
        resp = client.chat.completions.create(
            model='gpt-3.5-turbo',
            messages=[
                {'role':'system','content':'あなたは買取スタッフです。'},
                {'role':'user','content':user_text}
            ]
        )
        reply = resp.choices[0].message.content
    except:
        reply = 'すみません、今応答できません。'
    # 返信
    with ApiClient(configuration) as api:
        MessagingApi(api).reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply)]
            )
        )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT',10000)))