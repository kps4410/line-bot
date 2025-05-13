from flask import Flask, request, abort
import openai
import os
import sys

from linebot.v3.webhook import WebhookHandler
from linebot.v3.messaging import MessagingApi, Configuration, ApiClient
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage
from linebot.v3.exceptions import InvalidSignatureError

app = Flask(__name__)

# ── 環境変数読み込み ─────────────────────────
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET       = os.getenv('LINE_CHANNEL_SECRET')
OPENAI_API_KEY            = os.getenv('OPENAI_API_KEY')

print("===== BOT STARTUP =====", file=sys.stderr)
print(f"LINE_TOKEN set? {'Yes' if LINE_CHANNEL_ACCESS_TOKEN else 'No'}", file=sys.stderr)
print(f"LINE_SECRET set? {'Yes' if LINE_CHANNEL_SECRET else 'No'}", file=sys.stderr)
print(f"OPENAI_KEY set? {'Yes' if OPENAI_API_KEY else 'No'}", file=sys.stderr)
print("========================", file=sys.stderr)

# OpenAI 設定
openai.api_key = OPENAI_API_KEY

# LINE Bot 設定
configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/callback", methods=['POST'])
def callback():
    print("🔔 /callback invoked", file=sys.stderr)
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    print(f"🟢 Signature: {signature}", file=sys.stderr)
    print(f"🟢 Body: {body}", file=sys.stderr)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("❌ Invalid signature", file=sys.stderr)
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
def handle_text(event):
    user_message = event.message.text
    print(f"🔵 Received message: {user_message}", file=sys.stderr)

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "あなたは不用品買取業者の査定スタッフです。"},
                {"role": "user",   "content": user_message}
            ],
            temperature=0.7,
        )
        reply_text = response.choices[0].message.content
        print(f"🟢 OpenAI response: {reply_text}", file=sys.stderr)
    except Exception as e:
        print(f"🔴 OpenAI error: {e}", file=sys.stderr)
        reply_text = "申し訳ありません、現在AIの応答に問題が発生しています。"

    with ApiClient(configuration) as api_client:
        messaging_api = MessagingApi(api_client)
        messaging_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
        )
    print("✅ Replied to LINE", file=sys.stderr)

if __name__ == "__main__":
    # port は Render 環境変数 PORT でも取得できます (省略可)
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "10000")))
