from flask import Flask, request, abort
import openai
import os

from linebot.v3.webhook import WebhookHandler
from linebot.v3.messaging import MessagingApi, Configuration, ApiClient
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage
from linebot.v3.exceptions import InvalidSignatureError

app = Flask(__name__)

# 🔑 正しい環境変数名で取得
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('+xGonwCTYuF3i4unuBoeL4Do5Ft9KznhLHynQ0Milkpxs9xpZaM9vd3xaiHhg9uUWWj8sVfvSlQXkyo4ajpeZRjfezb8v+m1PVLNTxo7TRyLwfeudMPNhEetgz1nxUBuN+Lmf0tde2rxKaZLuwTxrwdB04t89/1O/w1cDnyilFU=')
LINE_CHANNEL_SECRET = os.environ.get('a443d8275f6ad91333dfeb68edb29b17')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

openai.api_key = OPENAI_API_KEY

configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
def handle_text(event):
    user_message = event.message.text

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "あなたは親切で丁寧な不用品買取スタッフです。お客様の査定相談に対応してください。"},
                {"role": "user", "content": user_message}
            ]
        )
        reply_text = response['choices'][0]['message']['content']
    except Exception as e:
        reply_text = "AIの応答にエラーが発生しました。時間をおいて再度お試しください。"

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
        )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
