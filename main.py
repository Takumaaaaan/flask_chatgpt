from flask import Flask, render_template, jsonify, request, session, redirect
from datetime import timedelta
import openai
from dotenv import load_dotenv

load_dotenv()
# 環境変数を参照
import os
API_KEY = os.getenv('API_KEY')

app = Flask(__name__, static_folder='./static')

app.secret_key = os.getenv('SECRET_KEY')
app.permanent_session_lifetime = timedelta(minutes=30)

def completion(new_message_text:str, settings_text:str = '', past_messages:list = []):
    openai.api_key = API_KEY
    print(settings_text)
    if len(past_messages) == 0 and len(settings_text) != 0:
        system = {"role": "system", "content": settings_text}
        past_messages.append(system)
    new_message = {"role": "user", "content": new_message_text}
    past_messages.append(new_message)

    result = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=past_messages
    )
    response_message = {"role": "assistant", "content": result.choices[0].message.content}
    
    past_messages.append(response_message)
    response_message_text = result.choices[0].message.content
    
    return response_message_text, past_messages


@app.route('/reload/', methods=['GET'])
def reload():
    if "all_messages" in session:
        session["all_messages"] = []
    if "past_messages" in session:
        session["past_messages"] = []
    return redirect("/chat/")

@app.route('/chat/', methods=['GET',"POST"])
def chat():
    if "all_messages" not in session:
        session["all_messages"] = []
    if "past_messages" not in session:
        session["past_messages"] = []

    if request.method == "GET":
        return render_template('chat.html',mode="通常モード")
    
    elif request.method == "POST":
        all_messages = session["all_messages"]
        past_messages = session["past_messages"]
        message = request.form['message']
        response,past_messages = completion(message,settings_text="",past_messages=past_messages)

        response = response.strip().replace("\n","<br>\n")
        message = message.strip().replace("\n","<br>\n")

        all_messages.append(message)
        all_messages.append(response)
        print(message,response)
        print(past_messages)
        session["all_messages"] = all_messages
        session["past_messages"] = past_messages
        return render_template('chat.html', messages=all_messages,mode="通常モード")
    
@app.route('/menter/', methods=['GET',"POST"])
def chat_menter():
    setting = "あなたは心理カウンセラーです。相談に親身に乗ってあげてください。モチベーションを上げ、不安を取り除いてください。"
    if "all_messages" not in session:
        session["all_messages"] = []
    if "past_messages" not in session:
        session["past_messages"] = []

    if request.method == "GET":
        if "all_messages" in session:
            session["all_messages"] = []
        if "past_messages" in session:
            session["past_messages"] = []
        return render_template('chat.html',mode="メンタモード")
    
    elif request.method == "POST":
        all_messages = session["all_messages"]
        past_messages = session["past_messages"]
        message = request.form['message']
        response,past_messages = completion(message,settings_text=setting,past_messages=past_messages)

        response = response.strip().replace("\n","<br>\n")
        message = message.strip().replace("\n","<br>\n")

        all_messages.append(message)
        all_messages.append(response)
        print(message,response)
        print(past_messages)
        session["all_messages"] = all_messages
        session["past_messages"] = past_messages
        return render_template('chat.html', messages=all_messages,mode="メンタモード")
    
@app.route('/english/', methods=['GET',"POST"])
def chat_english():
    setting = "あなたは優秀なプロの英語講師です。私は英語初級者です。私が送る英文の文法間違いやより適切な表現があれば訂正し、"\
        "その理由を小学生にもわかりやすく説明してください。また、訂正前と訂正後を比較して訂正箇所をわかりやすく表示してください。"
    if "all_messages" not in session:
        session["all_messages"] = []
    if "past_messages" not in session:
        session["past_messages"] = []

    if request.method == "GET":
        if "all_messages" in session:
            session["all_messages"] = []
        if "past_messages" in session:
            session["past_messages"] = []
        return render_template('chat.html',mode="英語添削モード")
    
    elif request.method == "POST":
        all_messages = session["all_messages"]
        past_messages = session["past_messages"]
        message = request.form['message']
        response,past_messages = completion(message,settings_text=setting,past_messages=past_messages)

        response = response.strip().replace("\n","<br>\n")
        message = message.strip().replace("\n","<br>\n")

        all_messages.append(message)
        all_messages.append(response)
        print(message,response)
        print(past_messages)
        session["all_messages"] = all_messages
        session["past_messages"] = past_messages
        return render_template('chat.html', messages=all_messages,mode="英語添削モード")

@app.route('/japanese/', methods=['GET',"POST"])
def chat_japanese():
    setting = "あなたは優秀なプロの編集者です。私が送る日本語の誤字、脱字、タイプミス、文法ミス、不自然な表現を全て指摘し、"\
        "適切な表現に全て訂正してください。全ての訂正箇所を小学生にもわかるように一つずつ箇条書きで説明してください。"\
        "また、訂正後の文章を全文表示してください。"
    if "all_messages" not in session:
        session["all_messages"] = []
    if "past_messages" not in session:
        session["past_messages"] = []

    if request.method == "GET":
        if "all_messages" in session:
            session["all_messages"] = []
        if "past_messages" in session:
            session["past_messages"] = []
        return render_template('chat.html',mode="日本語添削モード")
    
    elif request.method == "POST":
        all_messages = session["all_messages"]
        past_messages = session["past_messages"]
        message = request.form['message']
        response,past_messages = completion(message,settings_text=setting,past_messages=past_messages)

        response = response.strip().replace("\n","<br>\n")
        message = message.strip().replace("\n","<br>\n")

        all_messages.append(message)
        all_messages.append(response)
        print(message,response)
        print(past_messages)
        session["all_messages"] = all_messages
        session["past_messages"] = past_messages
        return render_template('chat.html', messages=all_messages,mode="日本語添削モード")

@app.route('/', methods=['GET'])
def toppage():
    return redirect("/chat/")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5003)

