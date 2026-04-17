from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
import os, secrets
from collections import Counter
from datetime import datetime

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax')

BOSS_PASSWORD = "8888" 

# --- 菜單資料 ---
MENU_DATA = {
    "吃爽組合 (套餐)": [
        {"name": "薯條OR雞塊+飲品", "price": 60, "sub": "薯條/雞塊 二選一", "opts": [["選薯條", "選雞塊"], ["選紅茶", "選冷泡茶"]]},
        {"name": "肉蛋吐司+紅茶", "price": 60},
        {"name": "熱狗(3支)+蛋+飲品", "price": 50, "opts": [["選紅茶", "選冷泡茶"]]},
        {"name": "草莓肉鬆吐司+飲品", "price": 50, "opts": [["選紅茶", "選冷泡茶"]]},
        {"name": "巧克力薯餅吐司+飲品", "price": 50, "opts": [["選紅茶", "選冷泡茶"]]}
    ],
    "蛋餅類": [
        {"name": "原味蛋餅", "price": 30, "can_add": True}, 
        {"name": "蔥香蛋餅", "price": 35, "can_add": True}, 
        {"name": "肉鬆蛋餅", "price": 40, "can_add": True}, 
        {"name": "起司蛋餅", "price": 40, "can_add": True},
        {"name": "蔬菜蛋餅", "price": 40, "can_add": True},
        {"name": "火腿蛋餅", "price": 40, "can_add": True},
        {"name": "香煎培根蛋餅", "price": 40, "can_add": True},
        {"name": "熱狗蛋餅", "price": 40, "can_add": True},
        {"name": "塔香蛋餅", "price": 40, "can_add": True},
        {"name": "玉米蛋餅", "price": 40, "can_add": True},
        {"name": "酥脆薯餅蛋餅", "price": 45, "can_add": True},
        {"name": "特調鮪魚蛋餅", "price": 50, "can_add": True},
        {"name": "里肌肉蛋餅", "price": 50, "can_add": True},
        {"name": "辣菜脯里肌蛋餅", "price": 65, "can_add": True}
    ],
    "泡麵系列 (2包)": [
        {"name": "招牌炒泡麵", "price": 70, "can_add": True, "can_spicy": True}, 
        {"name": "起司魂炒泡麵", "price": 75, "can_add": True, "can_spicy": True},
        {"name": "椒麻炒泡麵", "price": 75, "can_add": True, "can_spicy": True},
        {"name": "菜脯辣炒泡麵", "price": 75, "can_add": True, "can_spicy": True},
        {"name": "經典沙茶炒泡麵", "price": 75, "can_add": True, "can_spicy": True}
    ],
    "炒麵系列 (200g)": [
        {"name": "蘑菇麵", "price": 55, "can_add": True},
        {"name": "黑胡椒麵", "price": 55, "can_add": True},
        {"name": "招牌爆香炒麵", "price": 70, "can_add": True, "can_spicy": True}, 
        {"name": "起司魂炒麵", "price": 75, "can_add": True, "can_spicy": True},
        {"name": "菜脯辣起司炒麵", "price": 75, "can_add": True, "can_spicy": True},
        {"name": "經典沙茶炒麵", "price": 75, "can_add": True, "can_spicy": True}
    ],
    "果醬吐司/厚片": [
        {"name": "巧克力吐司", "price": 25, "is_jam": True}, {"name": "巧克力厚片", "price": 30, "is_jam": True},
        {"name": "草莓吐司", "price": 25, "is_jam": True}, {"name": "草莓厚片", "price": 30, "is_jam": True},
        {"name": "花生吐司", "price": 25, "is_jam": True}, {"name": "花生厚片", "price": 30, "is_jam": True},
        {"name": "奶酥吐司", "price": 25, "is_jam": True}, {"name": "奶酥厚片", "price": 30, "is_jam": True}
    ],
    "烤吐司系列": [
        {"name": "煎蛋吐司", "price": 35, "can_add": True, "no_v": True},
        {"name": "火腿吐司", "price": 40, "can_add": True, "no_v": True},
        {"name": "培根吐司", "price": 40, "can_add": True, "no_v": True},
        {"name": "麥香雞吐司", "price": 40, "can_add": True, "no_v": True},
        {"name": "鮪魚吐司", "price": 50, "can_add": True, "no_v": True},
        {"name": "薯餅吐司", "price": 40, "can_add": True, "no_v": True},
        {"name": "里肌吐司", "price": 55, "can_add": True, "no_v": True}, 
        {"name": "卡啦雞腿吐司", "price": 60, "can_add": True, "no_v": True}
    ],
    "單點小點": [
        {"name": "荷包蛋", "price": 15}, {"name": "玉米蛋", "price": 35},
        {"name": "熱狗(3支)", "price": 20}, {"name": "蔥蛋", "price": 25},
        {"name": "薯餅", "price": 25}, {"name": "麥克雞塊", "price": 45},
        {"name": "小肉豆", "price": 40}, {"name": "美式脆條", "price": 45},
        {"name": "雞柳條", "price": 50}, {"name": "黃金蝦排", "price": 35}
    ],
    "飲品 (L)": [
        {"name": "紅茶", "price": 25}, {"name": "香醇奶茶", "price": 30}, 
        {"name": "冷泡茶", "price": 25}, {"name": "鮮奶茶", "price": 45}
    ]
}

history = []
total_income = 0

@app.before_request
def ensure_session():
    if 'cart' not in session: session['cart'] = []
    if 'info' not in session: session['info'] = {"type": "外帶", "table": ""}

@app.route("/")
def index():
    cart = session.get('cart', [])
    tid = request.args.get('table')
    if tid: session['info'] = {"type": "內用", "table": tid}
    return render_template_string(INDEX_HTML, menu=MENU_DATA, cart_len=len(cart), total=sum(i['price'] for i in cart), table_id=tid)

@app.route("/update_info", methods=["POST"])
def update_info():
    session['info'] = {"type": request.form.get("type"), "table": request.form.get("table")}
    return jsonify({"status": "ok"})

@app.route("/add", methods=["POST"])
def add():
    temp = session.get('cart', [])
    temp.append({"id": secrets.token_hex(4), "name": request.form.get("name"), "price": int(request.form.get("price"))})
    session['cart'] = temp
    return jsonify({"count": len(session['cart']), "total": sum(i['price'] for i in session['cart'])})

@app.route("/del_item", methods=["POST"])
def del_item():
    target_id = request.form.get("id")
    temp = session.get('cart
