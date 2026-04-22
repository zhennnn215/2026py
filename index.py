import requests
from bs4 import BeautifulSoup

import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter

if not firebase_admin._apps:
    if os.path.exists('serviceAccountKey.json'):
        # 本地環境
        cred = credentials.Certificate('serviceAccountKey.json')
    else:
        # 雲端環境 (Vercel)
        firebase_config = os.getenv('FIREBASE_CONFIG')
        if firebase_config:
            try:
                cred_dict = json.loads(firebase_config)
                cred = credentials.Certificate(cred_dict)
            except Exception as e:
                print(f"JSON 解析錯誤: {e}")
        else:
            print("找不到環境變數 FIREBASE_CONFIG")
    
    # 執行初始化
    try:
        firebase_admin.initialize_app(cred)
    except Exception as e:
        print(f"Firebase 初始化失敗: {e}")


from flask import Flask, render_template, request
from datetime import datetime
import random

app = Flask(__name__)

@app.route("/")
def index():
    homepage = "<h1>歡迎進入王鐸蓁Python網頁</h1>"
    homepage += "<a href=/mis>MIS</a><br><hr>"
    homepage += "<a href=/today>顯示日期時間</a><br><hr>"
    homepage += "<a href=/welcome?nick=tcyang>傳送使用者暱稱</a><br><hr>"
    homepage += "<a href=/account>網頁表單傳值</a><br><hr>"
    homepage += "<a href=/about>鐸蓁簡介網頁</a><br><hr>"
    homepage += "<a href=/math>數學運算</a><hr>" 
    homepage += "<a href=/cup>擲茭</a><hr>"
    homepage += "<a href=/read>讀取Firestore資料</a><hr>"
    homepage += "<a href=/search>靜宜資管老師查詢</a><hr>"
    homepage += "<a href=/sp1>爬蟲結果</a><hr>"
    homepage += "<a href=/movie>查詢即將上映電影</a>"
    return homepage

@app.route("/sp1")
def sp1():
    R = ""
    url = "https://tcyang2026-a.vercel.app/about"
    Data = requests.get(url)
    Data.encoding = "utf-8"
    #print(Data.text)
    sp = BeautifulSoup(Data.text, "html.parser")
    result=sp.select("td a")

    for item in result:
        R += item.text + "<br>" + item.get("href") + "<br><br>"
    return R

@app.route("/movie")
def movie():
    url = "http://www.atmovies.com.tw/movie/next/"
    
    headers = {"User-Agent": "Mozilla/5.0"}
    Data = requests.get(url, headers=headers)
    Data.encoding = "utf-8"
    
    sp = BeautifulSoup(Data.text, "html.parser")
    result = sp.select(".filmListAllX li")
    R = "<h1>近期上映電影</h1>"

    for item in result:
        img_tag = item.find("img")
        title = img_tag.get("alt") if img_tag else "無標題"

        a_tag = item.find("a")
        href = a_tag.get("href") if a_tag else "#"
        link = "http://www.atmovies.com.tw" + href if not href.startswith("http") else href
        
        R += f"<a href='{link}' target='_blank'>{title}</a><br>"

    return R

@app.route("/search", methods=["GET", "POST"])
def search():
    db = firestore.client()
    results = []
    keyword = ""
    
    if request.method == "POST":
        keyword = request.form.get("keyword")
        collection_ref = db.collection("靜宜資管")
        docs = collection_ref.get()

        for doc in docs:
            user = doc.to_dict()
            if keyword in user["name"]:
                results.append({
                    "name": user["name"],
                    "lab": user["lab"]
                })

    return render_template("search.html", results=results, keyword=keyword)


@app.route("/read")
def read():
    db = firestore.client()
    Temp = ""
    collection_ref = db.collection("靜宜資管")
    docs = collection_ref.order_by("lab", direction=firestore.Query.DESCENDING).limit(4).get()
    for doc in docs:
        Temp += str(doc.to_dict()) + "<br>"

    return Temp


@app.route("/mis")
def course():
    return "<h1>資訊管理導論</h1><a href=/>回到網站首頁</a>"

@app.route("/today")
def today():
    now = datetime.now()
    return render_template("today.html", datetime = str(now))

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/welcome", methods=["GET"])
def welcome():
    x = request.values.get("u")
    y = request.values.get("dep")
    return render_template("welcome.html", name=x, dep=y)

@app.route("/account", methods=["GET", "POST"])
def account():
    if request.method == "POST":
        user = request.form["user"]
        pwd = request.form["pwd"]
        result = "您輸入的帳號是：" + user + "; 密碼為：" + pwd 
        return result
    else:
        return render_template("account.html")
    
@app.route("/math", methods=["GET", "POST"])
def math():
    if request.method == "POST":
        x = int(request.form["x"])
        opt = request.form["opt"]
        y = int(request.form["y"])      
        result = "您輸入的是：" + str(x) + opt + str(y)
        
        if (opt == "/" and y == 0):
            result += "，除數不能為0"
        else:
            match opt:
                case "+":
                    r = x + y
                case "-":
                    r = x - y
                case "*":
                    r = x * y
                case "/":
                    r = x / y
                case _:
                    return "未知運算符號"
            result += "=" + str(r)  + "<br><a href=/>返回首頁</a>"          
        return result
    else:
        return render_template("math.html")
    
@app.route('/cup', methods=["GET"])
def cup():
    # 檢查網址是否有 ?action=toss
    #action = request.args.get('action')
    action = request.values.get("action")
    result = None
    
    if action == 'toss':
        # 0 代表陽面，1 代表陰面
        x1 = random.randint(0, 1)
        x2 = random.randint(0, 1)
        
        # 判斷結果文字
        if x1 != x2:
            msg = "聖筊：表示神明允許、同意，或行事會順利。"
        elif x1 == 0:
            msg = "笑筊：表示神明一笑、不解，或者考慮中，行事狀況不明。"
        else:
            msg = "陰筊：表示神明否定、憤怒，或者不宜行事。"
            
        result = {
            "cup1": "/static/" + str(x1) + ".jpg",
            "cup2": "/static/" + str(x2) + ".jpg",
            "message": msg
        }
        
    return render_template('cup.html', result=result)


if __name__ == "__main__":
    app.run()
