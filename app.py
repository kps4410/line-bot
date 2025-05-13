from flask import Flask, request, abort
import openai
import os

from linebot.v3.webhook import WebhookHandler
from linebot.v3.messaging import MessagingApi, Configuration, ApiClient
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.messaging.models import ReplyMessageRequest, TextMessage
from linebot.v3.exceptions import InvalidSignatureError

app = Flask(__name__)

# ✅ 環境変数から安全にキーを読み込み
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

# ✅ OpenAI APIキー設定
openai.api_key = OPENAI_API_KEY

# ✅ LINE Bot 設定
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

# ✅ メッセージを受けてChatGPTで返信
@handler.add(MessageEvent, message=TextMessageContent)
def handle_text(event):
    user_message = event.message.text

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # または "gpt-4"
            messages=[
                {"role": "system", "content": "あなたは不用品買取業者のスタッフです。親切丁寧に査定の相談にのってください。"},
                {"role": "user", "content": user_message}
            ]
        )
        reply_text = response['choices'][0]['message']['content']
    except Exception as e:
        reply_text = "申し訳ありません、現在AIの応答に問題が発生しています。"

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
