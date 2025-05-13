# ChatGPTでテキスト返信
@handler.add(MessageEvent, message=TextMessageContent)
def handle_text(event):
    user_message = event.message.text
    print(f"🔵 受信メッセージ: {user_message}")  # 受信ログ出力

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "あなたは不用品買取業者の査定スタッフです。"},
                {"role": "user", "content": user_message}
            ]
        )
        print(f"🟡 OpenAIレスポンス全文: {response}")  # ←ここを追加！

        reply_text = response['choices'][0]['message']['content']
        print(f"🟢 OpenAI応答: {reply_text}")  # 応答内容表示
    except Exception as e:
        print(f"🔴 OpenAIエラー: {e}")  # エラー内容表示
        reply_text = "申し訳ありません、現在AIの応答に問題が発生しています。"

    # LINEへ返答
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=reply_text)]
            )
        )
