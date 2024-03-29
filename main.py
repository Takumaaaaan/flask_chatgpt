from flask import Flask, render_template, jsonify, request, session, redirect,send_file
from datetime import timedelta
# ファイル名をチェックする関数
from werkzeug.utils import secure_filename
import openai
import deepl
from dotenv import load_dotenv
import os
load_dotenv()

#Flaskの設定
app = Flask(__name__, static_folder='./static')
UPLOAD_FOLDER = 'temp'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

"""
環境変数の設定
"""
API_KEY = os.getenv('API_KEY')
if os.getenv("HTTP_PROXY"):
    os.environ['http_proxy'] = os.getenv("HTTP_PROXY")
if os.getenv("HTTP_PROXY"):    
    os.environ['https_proxy'] = os.getenv("HTTPS_PROXY")

#flaskのセッションキー
app.secret_key = os.getenv('SECRET_KEY')
app.permanent_session_lifetime = timedelta(minutes=30)
#deeplのAPIキー
DEEPL_API_KEY = os.environ["DEEPL_API_KEY"]

"""
チャット関数
"""
def completion(new_message_text:str, settings_text:str = '', past_messages:list = [],mode:str = "gpt-3.5-turbo"):
    openai.api_key = API_KEY
    print(settings_text)
    if len(past_messages) == 0 and len(settings_text) != 0:
        system = {"role": "system", "content": settings_text}
        past_messages.append(system)
    new_message = {"role": "user", "content": new_message_text}
    past_messages.append(new_message)

    result = openai.ChatCompletion.create(
        model=mode, #"gpt-3.5-turbo",
        messages=past_messages
    )
    response_message = {"role": "assistant", "content": result.choices[0].message.content}
    
    past_messages.append(response_message)
    response_message_text = result.choices[0].message.content
    
    return response_message_text, past_messages

"""
翻訳の関数(translate_documentは使わない)
"""
def translate_text(text:str,target_lang:str):
    if os.getenv("HTTP_PROXY"):
        translator = deepl.Translator(DEEPL_API_KEY,proxy=os.environ['https_proxy'])
    else:
        translator = deepl.Translator(DEEPL_API_KEY)
    # print(text)
    # print(target_lang)
    result = translator.translate_text(text=text,target_lang=target_lang)
    return result.text

def tranlate_document():
    files = os.listdir(UPLOAD_FOLDER)
    for file in files:
        if "english" in file:
            break
    input_path = UPLOAD_FOLDER + "/" + file
    extension = file.rsplit('.', 1)[1].lower()
    output_path =  UPLOAD_FOLDER + "/" + "japanese." + extension
    if os.getenv("HTTP_PROXY"):
        translator = deepl.Translator(DEEPL_API_KEY,proxy=os.environ['https_proxy'])
    else:
        translator = deepl.Translator(DEEPL_API_KEY)
    try:
        # Using translate_document_from_filepath() with file paths 
        translator.translate_document_from_filepath(
            input_path,
            output_path,
            target_lang="JA"
        )

    except deepl.DocumentTranslationException as error:
        # If an error occurs during document translation after the document was
        # already uploaded, a DocumentTranslationException is raised. The
        # document_handle property contains the document handle that may be used to
        # later retrieve the document from the server, or contact DeepL support.
        doc_id = error.document_handle.id
        doc_key = error.document_handle.key
        print(f"Error after uploading ${error}, id: ${doc_id} key: ${doc_key}")
    except deepl.DeepLException as error:
        # Errors during upload raise a DeepLException
        print(error)
    
    return output_path


"""
翻訳のルータ(translate_fileは使わない)
"""
@app.route('/reload_translate/', methods=['GET'])
def reload_translate():
    if "all_translates" in session:
        session["all_translates"] = []
    if "past_messages" in session:
        session["past_translates"] = []
    return redirect("/translate/")

@app.route('/translate/', methods=['GET','POST'])
def tranlate():
    if "all_translates" not in session:
        session["all_translates"] = []
    all_translates = session["all_translates"]
    if request.method == "GET":
        return render_template('translate.html', messages=all_translates,mode="翻訳モード")
    
    elif request.method == "POST":
        all_translates = session["all_translates"]
        message = request.form['message']
        if message is None:
            return render_template('translate.html', messages=all_translates,mode="翻訳モード")

        english_flag = message.encode('utf-8').isalpha()
        if english_flag:
            response = translate_text(text=message,target_lang="JA")
        else:
            response = translate_text(text=message,target_lang="EN-US")
        response = response.strip().replace("\n","<br>\n")
        message = message.strip().replace("\n","<br>\n")
        all_translates.append(message)
        all_translates.append(response)
        session["all_translates"] = all_translates
        print(response)
        return render_template('translate.html', messages=all_translates,mode="翻訳モード")


@app.route('/translate_file/', methods=['GET','POST'])
def translate_file():
    if request.method == 'GET':
        return render_template('translate_file.html',mode="ファイル翻訳モード")
    # リクエストがポストかどうかの判別
    if request.method == 'POST':
        # ファイルがなかった場合の処理
        if 'file' not in request.files:
            return redirect(request.url)
        # データの取り出し
        file = request.files['file']
        # ファイル名がなかった時の処理
        if file.filename == '':
            return redirect(request.url)
        
        # 危険な文字を削除（サニタイズ処理）
        filename = secure_filename(file.filename)
        extension = filename.rsplit('.', 1)[1].lower()
        # ファイルの保存
        file.save(os.path.join(UPLOAD_FOLDER, "english." + extension))
        output = tranlate_document()
        
        return send_file(output, as_attachment = True)


"""
チャットのルーターの設定
"""
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
        # print(message,response)
        # print(past_messages)
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
        # print(message,response)
        # print(past_messages)
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
        # print(message,response)
        # print(past_messages)
        session["all_messages"] = all_messages
        session["past_messages"] = past_messages
        return render_template('chat.html', messages=all_messages,mode="英語添削モード")

@app.route('/japanese/', methods=['GET',"POST"])
def chat_japanese():
    setting = "あなたはプロの編集者です。私が送る文章全ての誤字、脱字、タイプミスを全て指摘してください。"\
        "全ての指摘した内容を箇条書きで記載し説明してください。"\
        "全ての指摘した内容を正しい日本語に修正し、修正後の文章を全文表示してください。"
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
        # print(message,response)
        # print(past_messages)
        session["all_messages"] = all_messages
        session["past_messages"] = past_messages
        return render_template('chat.html', messages=all_messages,mode="日本語添削モード")
    
@app.route('/chat_gpt4/', methods=['GET',"POST"])
def chat_gpt4():
    if "all_messages" not in session:
        session["all_messages"] = []
    if "past_messages" not in session:
        session["past_messages"] = []

    if request.method == "GET":
        return render_template('gpt4.html',mode="GPT4モード")
    
    elif request.method == "POST":
        all_messages = session["all_messages"]
        past_messages = session["past_messages"]
        message = request.form['message']
        response,past_messages = completion(message,settings_text="",past_messages=past_messages,mode="gpt-4")

        response = response.strip().replace("\n","<br>\n")
        message = message.strip().replace("\n","<br>\n")

        all_messages.append(message)    
        all_messages.append(response)
        # print(message,response)
        # print(past_messages)
        session["all_messages"] = all_messages
        session["past_messages"] = past_messages
        return render_template('gpt4.html', messages=all_messages,mode="GPT4モード")

"""
使い方のルータの設定
"""
@app.route('/help/', methods=['GET'])
def help():
    return render_template('help.html')

"""
ホームの設定(chatに飛ばす)
"""
@app.route('/', methods=['GET'])
def toppage():
    return redirect("/chat/")

"""
main(portは適当)
"""
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5003)

