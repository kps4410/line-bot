from flask import Flask, request, abort
import os
from openai import OpenAI

from linebot.v3.webhook import WebhookHandler
from linebot.v3.messaging import MessagingApi, Configuration, ApiClient
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage
from linebot.v3.exceptions import InvalidSignatureError

app = Flask(__name__)

# 環境変数から読み込み
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET       = os.getenv('LINE_CHANNEL_SECRET')
OPENAI_API_KEY            = os.getenv('OPENAI_API_KEY')

# OpenAI クライアント初期化
os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY
client = OpenAI()

# LINE SDK 設定
configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature','')
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
def handle_text(event):
    user_text = event.message.text
    print(f"🔵 Received: {user_text}")

    try:
        # 最新インターフェースで呼び出し
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role":"system","content":"あなたは不用品買取のスタッフです。"},
                {"role":"user","content":user_text}
            ]
        )
        reply_text = resp.choices[0].message.content
        print(f"🟢 OpenAI reply: {reply_text}")
    except Exception as e:
        print(f"🔴 OpenAI error: {e}")
        reply_text = "申し訳ありません、現在AIの応答に問題が発生しています。"

    with ApiClient(configuration) as client_api:
        line_api = MessagingApi(client_api)
        line_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
        )
    print("📤 Reply sent")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv('PORT',10000)))
