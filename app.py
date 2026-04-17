from flask import Flask, render_template_string, request, jsonify, session, redirect
import os
import secrets
import requests
from collections import Counter
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax')

# --- 菜單資料 ---
MENU = {
    "蛋餅類": [{"name": "原味蛋餅", "price": 30, "can_add": True}, {"name": "蔥香蛋餅", "price": 35, "can_add": True}, {"name": "肉鬆蛋餅", "price": 40, "can_add": True}, {"name": "起司/牽絲蛋餅", "price": 40, "can_add": True}, {"name": "蔬菜蛋餅", "price": 40, "can_add": True}, {"name": "火腿蛋餅", "price": 40, "can_add": True}, {"name": "香煎培根蛋餅", "price": 40, "can_add": True}, {"name": "熱狗蛋餅", "price": 40, "can_add": True}, {"name": "塔香蛋餅", "price": 40, "can_add": True}, {"name": "玉米蛋餅", "price": 40, "can_add": True}, {"name": "酥脆薯餅蛋餅", "price": 45, "can_add": True}, {"name": "漢堡排蛋餅", "price": 45, "can_add": True}, {"name": "特調鮪魚蛋餅", "price": 50, "can_add": True}, {"name": "里肌肉蛋餅", "price": 50, "can_add": True}, {"name": "厚切牛肉蛋餅", "price": 60, "can_add": True}, {"name": "辣菜脯里肌蛋餅", "price": 65, "can_add": True}],
    "泡麵 / 炒麵": [{"name": "招牌炒泡麵 (2包泡麵)", "price": 70, "can_add": True}, {"name": "起司魂炒泡麵 (2包泡麵)", "price": 75, "can_add": True}, {"name": "椒麻炒泡麵 (2包泡麵)", "price": 75, "can_add": True}, {"name": "菜脯辣炒泡麵 (2包泡麵)", "price": 75, "can_add": True}, {"name": "經典沙茶炒泡麵 (2包泡麵)", "price": 75, "can_add": True}, {"name": "蘑菇炒麵 (200G)", "price": 55, "can_add": True}, {"name": "黑胡椒炒麵 (200G)", "price": 55, "can_add": True}, {"name": "招牌爆香炒麵 (200G)", "price": 70, "can_add": True}, {"name": "起司魂炒麵 (200G)", "price": 75, "can_add": True}, {"name": "菜脯辣起司炒麵 (200G)", "price": 75, "can_add": True}, {"name": "經典沙茶炒麵 (200G)", "price": 75, "can_add": True}],
    "果醬吐司/厚片": [{"name": "巧克力吐司", "price": 25}, {"name": "巧克力厚片", "price": 30}, {"name": "草莓吐司", "price": 25}, {"name": "草莓厚片", "price": 30}, {"name": "花生吐司", "price": 25}, {"name": "花生厚片", "price": 30}, {"name": "奶酥吐司", "price": 25}, {"name": "奶酥厚片", "price": 30}],
    "烤吐司系列": [{"name": "煎蛋吐司", "price": 35, "can_add": True}, {"name": "火腿吐司", "price": 40, "can_add": True}, {"name": "培根吐司", "price": 40, "can_add": True}, {"name": "麥香雞吐司", "price": 40, "can_add": True}, {"name": "鮪魚吐司", "price": 50, "can_add": True}, {"name": "薯餅吐司", "price": 40, "can_add": True}, {"name": "漢堡排吐司", "price": 45, "can_add": True}, {"name": "里肌吐司", "price": 55, "can_add": True}, {"name": "卡啦雞腿吐司", "price": 60, "can_add": True}, {"name": "厚牛吐司", "price": 60, "can_add": True}],
    "單點小點": [{"name": "荷包蛋", "price": 15}, {"name": "玉米蛋", "price": 35}, {"name": "蔥蛋", "price": 25}, {"name": "熱狗(3支)", "price": 20}, {"name": "薯餅", "price": 25}, {"name": "麥克雞塊", "price": 45}, {"name": "小肉豆", "price": 40}, {"name": "美式脆條", "price": 45}, {"name": "抓餅", "price": 35}, {"name": "港式蘿蔔糕", "price": 35}, {"name": "雞柳條", "price": 50}, {"name": "黃金蝦排", "price": 35}],
    "飲品 (L)": [{"name": "紅茶", "price": 25}, {"name": "香醇奶茶", "price": 30}, {"name": "鮮奶茶", "price": 45}, {"name": "豆漿紅茶", "price": 40}]
}

history = []
total_income = 0

def clean_expired_data():
    global history, total_income
    cutoff = datetime.now() - timedelta(hours=24)
    history = [h for h in history if h['time'] > cutoff]
    total_income = sum(h['price'] for h in history)

@app.before_request
def ensure_session():
    clean_expired_data()
    if 'cart' not in session: session['cart'] = []
    if 'order_info' not in session: session['order_info'] = {"type": "外帶", "table": ""}

@app.route("/ping")
def ping(): return "pong", 200

# --- 自動傳送到 Google 表單的邏輯 ---
def send_to_google(loc, total, summary):
    # 這是你的 Google 表單提交網址
    url = "https://docs.google.com/forms/d/e/1FAIpQLSeXInB-6L-v13uG_Y-A-L10Xv_87U-D_p9uBw5H0906-p60-g/formResponse"
    payload = {
        "entry.1408016462": loc,     # 用餐方式
        "entry.1895743452": total,   # 金額
        "entry.550478028": summary   # 明細
    }
    try:
        requests.post(url, data=payload, timeout=5)
    except:
        print("Google 備份失敗，但不影響現場點餐")

@app.route("/get_backup_text")
def get_backup_text():
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    output = f"=== 晨食麵所 營收備份 ({now_str}) ===\\n今日累計總額：${total_income}\\n--------------------------\\n"
    for h in history[::-1]:
        output += f"[{h['time'].strftime('%H:%M')}] {h['loc']} - ${h['price']}\\n明細：{h['summary']}\\n\\n"
    return jsonify({"text": output})

@app.route("/")
def index():
    cart = session.get('cart', [])
    return render_template_string(INDEX_HTML, menu=MENU, cart_len=len(cart), total=sum(i['price'] for i in cart))

@app.route("/update_info", methods=["POST"])
def update_info():
    session['order_info'] = {"type": request.form.get("type"), "table": request.form.get("table")}
    return jsonify({"status": "ok"})

@app.route("/add", methods=["POST"])
def add():
    temp = session.get('cart', [])
    temp.append({"name": request.form.get("name"), "price": int(request.form.get("price"))})
    session['cart'] = temp
    return jsonify({"count": len(session['cart']), "total": sum(i['price'] for i in session['cart'])})

@app.route("/cart")
def view_cart():
    cart = session.get('cart', [])
    info = session.get('order_info', {"type": "外帶", "table": ""})
    t = sum(i['price'] for i in cart)
    counts = Counter([i['name'] for i in cart])
    loc = f"{info['type']}" + (f"-{info['table']}桌" if info['table'] else "")
    return render_template_string(CART_HTML, counts=counts, total=t, loc=loc)

@app.route("/clear", methods=["POST"])
def clear():
    global total_income
    cart = session.get('cart', [])
    info = session.get('order_info', {"type": "外帶", "table": ""})
    t = sum(i['price'] for i in cart)
    if t > 0:
        loc = f"{info['type']}" + (f"-{info['table']}桌" if info['table'] else "")
        counts = Counter([i['name'] for i in cart])
        summary = ", ".join([f"{n}x{c}" for n,c in counts.items()])
        
        # 核心：送出訂單時自動發送到 Google
        send_to_google(loc, t, summary)
        
        total_income += t
        history.append({"id": secrets.token_hex(4), "loc": loc, "price": t, "summary": summary, "time": datetime.now()})
        session.clear()
        return "<div style='text-align:center; padding:50px;'><h2>🎉 訂單已送出並自動備份至雲端！</h2><br><a href='/'>回首頁</a></div>"
    return redirect("/")

@app.route("/delete_order", methods=["POST"])
def delete_order():
    global history
    order_id = request.form.get("id")
    history = [h for h in history if h['id'] != order_id]
    return jsonify({"status": "deleted"})

@app.route("/boss")
def boss():
    clean_expired_data()
    return render_template_string(BOSS_HTML, total=total_income, logs=history[::-1])

# --- 此處省略 INDEX_HTML, CART_HTML, BOSS_HTML 模板內容，請沿用之前的版本 ---
# ... (請將之前版本中的 HTML 內容完整貼回此處) ...

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
