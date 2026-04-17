from flask import Flask, render_template_string, request, jsonify, session, redirect
import os
import secrets
import requests
from collections import Counter
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax')

# --- 菜單資料 (含加料價格標示) ---
MENU_DATA = {
    "蛋餅類": [
        {"name": "原味蛋餅", "price": 30, "can_add": True}, {"name": "蔥香蛋餅", "price": 35, "can_add": True}, 
        {"name": "肉鬆蛋餅", "price": 40, "can_add": True}, {"name": "起司/牽絲蛋餅", "price": 40, "can_add": True}, 
        {"name": "蔬菜蛋餅", "price": 40, "can_add": True}, {"name": "火腿蛋餅", "price": 40, "can_add": True},
        {"name": "香煎培根蛋餅", "price": 40, "can_add": True}, {"name": "熱狗蛋餅", "price": 40, "can_add": True}, 
        {"name": "塔香蛋餅", "price": 40, "can_add": True}, {"name": "玉米蛋餅", "price": 40, "can_add": True}, 
        {"name": "酥脆薯餅蛋餅", "price": 45, "can_add": True}, {"name": "漢堡排蛋餅", "price": 45, "can_add": True},
        {"name": "特調鮪魚蛋餅", "price": 50, "can_add": True}, {"name": "里肌肉蛋餅", "price": 50, "can_add": True}, 
        {"name": "厚切牛肉蛋餅", "price": 60, "can_add": True}, {"name": "辣菜脯里肌蛋餅", "price": 65, "can_add": True}
    ],
    "泡麵系列 (2包泡麵)": [
        {"name": "招牌炒泡麵", "price": 70, "can_add": True}, {"name": "起司魂炒泡麵", "price": 75, "can_add": True}, 
        {"name": "椒麻炒泡麵", "price": 75, "can_add": True}, {"name": "菜脯辣炒泡麵", "price": 75, "can_add": True}, 
        {"name": "經典沙茶炒泡麵", "price": 75, "can_add": True}
    ],
    "炒麵系列 (200G)": [
        {"name": "蘑菇炒麵", "price": 55, "can_add": True}, {"name": "黑胡椒炒麵", "price": 55, "can_add": True}, 
        {"name": "招牌爆香炒麵", "price": 70, "can_add": True}, {"name": "起司魂炒麵", "price": 75, "can_add": True}, 
        {"name": "菜脯辣起司炒麵", "price": 75, "can_add": True}, {"name": "經典沙茶炒麵", "price": 75, "can_add": True}
    ],
    "果醬吐司/厚片": [
        {"name": "巧克力吐司", "price": 25}, {"name": "巧克力厚片", "price": 30}, {"name": "草莓吐司", "price": 25}, 
        {"name": "草莓厚片", "price": 30}, {"name": "花生吐司", "price": 25}, {"name": "花生厚片", "price": 30}, 
        {"name": "奶酥吐司", "price": 25}, {"name": "奶酥厚片", "price": 30}
    ],
    "烤吐司系列": [
        {"name": "煎蛋吐司", "price": 35, "can_add": True}, 
        {"name": "火腿吐司 (有生菜、番茄)", "price": 40, "can_add": True, "no_veg": True}, 
        {"name": "培根吐司 (有生菜、番茄)", "price": 40, "can_add": True, "no_veg": True}, 
        {"name": "麥香雞吐司 (有生菜、番茄)", "price": 40, "can_add": True, "no_veg": True}, 
        {"name": "鮪魚吐司 (有生菜、番茄)", "price": 50, "can_add": True, "no_veg": True}, 
        {"name": "薯餅吐司 (有生菜、番茄)", "price": 40, "can_add": True, "no_veg": True},
        {"name": "漢堡排吐司 (有生菜、番茄)", "price": 45, "can_add": True, "no_veg": True}, 
        {"name": "里肌吐司 (有生菜、番茄)", "price": 55, "can_add": True, "no_veg": True}, 
        {"name": "卡啦雞腿吐司 (有生菜、番茄)", "price": 60, "can_add": True, "no_veg": True}, 
        {"name": "厚牛吐司 (有生菜、番茄)", "price": 60, "can_add": True, "no_veg": True}
    ],
    "單點小點": [
        {"name": "荷包蛋", "price": 15}, {"name": "玉米蛋", "price": 35}, {"name": "蔥蛋", "price": 25},
        {"name": "熱狗(3支)", "price": 20}, {"name": "薯餅", "price": 25}, {"name": "麥克雞塊", "price": 45},
        {"name": "小肉豆", "price": 40}, {"name": "美式脆條", "price": 45}, {"name": "抓餅", "price": 35},
        {"name": "港式蘿蔔糕", "price": 35}, {"name": "雞柳條", "price": 50}, {"name": "黃金蝦排", "price": 35}
    ],
    "飲品 (L)": [
        {"name": "紅茶", "price": 25}, {"name": "香醇奶茶", "price": 30}, {"name": "鮮奶茶", "price": 45}, {"name": "豆漿紅茶", "price": 40}
    ]
}

# 全域變數
history = []
total_income = 0

def clean_expired_data():
    global history
    # 清理 24 小時前的歷史，但保留 total_income 不重算，以達到刪除明細不扣錢的效果
    cutoff = datetime.now() - timedelta(hours=24)
    history = [h for h in history if h['time'] > cutoff]

@app.before_request
def ensure_session():
    clean_expired_data()
    if 'cart' not in session: session['cart'] = []
    if 'order_info' not in session: session['order_info'] = {"type": "外帶", "table": ""}

@app.route("/ping")
def ping(): return "pong", 200

def send_to_google(loc, total, summary):
    # 請確保此 URL 與 Entry ID 正確
    url = "https://docs.google.com/forms/d/e/1FAIpQLSe5HJ_rQDNaSXNo6l38DYMFErzna8Rmqjp8X61cgPZ2d8QOqA/formResponse"
    payload = {
        "entry.303092604": loc,
        "entry.157627510": total,
        "entry.1541194223": summary
    }
    try: requests.post(url, data=payload, timeout=5)
    except: pass

@app.route("/get_backup_text")
def get_backup_text():
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    output = f"=== 營收備份 ({now_str}) ===\\n今日累計：${total_income}\\n"
    for h in history[::-1]:
        output += f"[{h['time'].strftime('%H:%M')}] {h['loc']} - ${h['price']}\\n明細：{h['summary']}\\n\\n"
    return jsonify({"text": output})

@app.route("/")
def index():
    cart = session.get('cart', [])
    return render_template_string(
