from flask import Flask, request, abort
import openai
import os

from linebot.v3.webhook import WebhookHandler
from linebot.v3.messaging import MessagingApi, Configuration, ApiClient
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage
from linebot.v3.exceptions import InvalidSignatureError

app = Flask(__name__)

# 環境変数からトークンを読み込み
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

# OpenAI APIキーを設定
openai.api_key = OPENAI_API_KEY

# LINEの設定
configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    print("📨 LINEから受信")  # ★追加
    print("📨 署名：", signature)  # ★追加

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("❌ 署名エラー")  # ★追加
        abort(400)

    return 'OK'

# ChatGPTでテキスト返信
@handler.add(MessageEvent, message=TextMessageContent)
def handle_text(event):
    user_message = event.message.text
    print(f"🔵 受信メッセージ: {user_message}")  # ★追加

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "あなたは不用品買取業者の査定スタッフです。"},
                {"role": "user", "content": user_message}
            ]
        )
        reply_text = response['choices'][0]['message']['content']
        print(f"🟢 OpenAI応答: {reply_text}")  # ★追加
    except Exception as e:
        print(f"🔴 OpenAIエラー: {e}")  # ★追加
        reply_text = "申し訳ありません、現在AIの応答に問題が発生しています。"

    # LINEに返信
    try:
        with ApiClient(configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply_text)]
                )
            )
        print("📤 LINEへ返信送信完了")  # ★追加
    except Exception as e:
        print(f"❌ LINE返信エラー: {e}")  # ★追加

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
