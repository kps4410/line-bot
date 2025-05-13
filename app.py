from flask import Flask, request, abort
import os
from openai import OpenAI

from linebot.v3.webhook import WebhookHandler
from linebot.v3.messaging import MessagingApi, Configuration, ApiClient
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage
from linebot.v3.exceptions import InvalidSignatureError

app = Flask(__name__)

# ── 環境変数読み込み ───────────────────────────
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET       = os.getenv('LINE_CHANNEL_SECRET')
OPENAI_API_KEY            = os.getenv('OPENAI_API_KEY')

print("===== BOT STARTUP =====")
print(f"LINE_TOKEN set? {'Yes' if LINE_CHANNEL_ACCESS_TOKEN else 'No'}")
print(f"LINE_SECRET set? {'Yes' if LINE_CHANNEL_SECRET else 'No'}")
print(f"OPENAI_KEY set? {'Yes' if OPENAI_API_KEY else 'No'}")
print("========================")

# OpenAI クライアント初期化
os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY or ""
client = OpenAI()

# LINE SDK 設定
configuration = Configuration(access_token=LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature','')
    body = request.get_data(as_text=True)
    print("🔔 /callback invoked")
    try:
        handler.handle(body, signature)
    except InvalidSignatureError as e:
        print(f"🔴 Signature error: {e}")
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessageContent)
def handle_text(event):
    user_text = event.message.text
    print(f"🔵 Received: {user_text!r}")

    try:
        print("🟡 Calling OpenAI...")
        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role":"system","content":"あなたは不用品買取のスタッフです。"},
                {"role":"user","content":user_text}
            ]
        )
        print(f"🟡 Raw resp: {resp}")
        # 選択肢の取り出し
        choice = resp.choices[0]
        # pydanticオブジェクトなら .message.content
        reply_text = getattr(choice.message, "content", None) or choice["message"]["content"]
        print(f"🟢 OpenAI reply: {reply_text!r}")
    except Exception as e:
        print(f"🔴 OpenAI error: {type(e).__name__}: {e}")
        reply_text = "申し訳ありません、現在AIの応答に問題が発生しています。"

    # LINEに返信
    try:
        with ApiClient(configuration) as client_api:
            line_api = MessagingApi(client_api)
            line_api.reply_message(
                ReplyMessageRequest(
                    reply_token=event.reply_token,
                    messages=[TextMessage(text=reply_text)]
                )
            )
        print("📤 Reply sent")
    except Exception as ex:
        print(f"🔴 LINE reply error: {type(ex).__name__}: {ex}")

if __name__ == "__main__":
    port = int(os.getenv('PORT', 10000))
    app.run(host="0.0.0.0", port=port)
