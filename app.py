from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
import os, secrets
from collections import Counter
from datetime import datetime

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax')

BOSS_PASSWORD = "8888" 

MENU_DATA = {
    "吃爽組合": [
        {"name": "薯條OR雞塊+飲品", "price": 60, "opts": [["選薯條", "選雞塊"], ["選紅茶", "選冷泡茶"]]},
        {"name": "肉蛋吐司+紅茶", "price": 60},
        {"name": "熱狗(3支)+蛋+飲品", "price": 50, "opts": [["選紅茶", "選冷泡茶"]]}
    ],
    "蛋餅類": [
        {"name": "原味蛋餅", "price": 30, "can_add": True},
        {"name": "里肌肉蛋餅", "price": 50, "can_add": True}
    ],
    "麵類系列": [
        {"name": "招牌炒泡麵", "price": 70, "can_add": True, "can_spicy": True}, 
        {"name": "招牌爆香炒麵", "price": 70, "can_add": True, "can_spicy": True}
    ],
    "烤吐司系列": [
        {"name": "煎蛋吐司", "price": 35, "can_add": True}, 
        {"name": "里肌吐司", "price": 55, "can_add": True, "no_v": True}
    ],
    "單點/飲品": [
        {"name": "薯餅", "price": 25},
        {"name": "紅茶(L)", "price": 25},
        {"name": "冷泡茶(L)", "price": 25}
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
    temp.append({"name": request.form.get("name"), "price": int(request.form.get("price"))})
    session['cart'] = temp
    return jsonify({"count": len(session['cart']), "total": sum(i['price'] for i in session['cart'])})

@app.route("/cart")
def view_cart():
    cart = session.get('cart', [])
    info = session.get('info', {"type": "外帶", "table": ""})
    t = sum(i['price'] for i in cart)
    counts = Counter([i['name'] for i in cart])
    loc = f"{info['type']}" + (f"-{info['table']}桌" if info['table'] else "")
    return render_template_string(CART_HTML, counts=counts, total=t, loc=loc)

@app.route("/clear", methods=["POST"])
def clear():
    global total_income
    cart = session.get('cart', [])
    info = session.get('info', {"type": "外帶", "table": ""})
    t = sum(i['price'] for i in cart)
    if t > 0:
        loc = f"{info['type']}" + (f"-{info['table']}桌" if info['table'] else "")
        counts = Counter([i['name'] for i in cart])
        now = datetime.now().strftime('%H:%M')
        summary = "<br>".join([f"{n} x{c}" for n,c in counts.items()])
        total_income += t
        order = {"id": secrets.token_hex(4), "loc": loc, "price": t, "summary": summary, "time": now}
        history.append(order)
        session.clear()
        return render_template_string(PRINT_HTML, order=order)
    return redirect("/")

@app.route("/boss")
def boss():
    if request.args.get("pw") != BOSS_PASSWORD: return "<h1>❌</h1>", 403
    return render_template_string(BOSS_HTML, total=total_income, logs=history[::-1])

@app.route("/delete_order", methods=["POST"])
def delete_order():
    global history
    oid = request.form.get("id")
    history = [h for h in history if h['id'] != oid]
    return jsonify({"status": "ok"})

# ------------------------------------------------------------------
# HTML TEMPLATES
# ------------------------------------------------------------------

INDEX_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width,initial-scale=1.0">
    <style>
        body{font-family:sans-serif;background:#fdfaf0;margin:0;padding:0 0 80px}
        .header{background:#ffbe00;color:#fff;padding:15px;text-align:center;font-weight:bold}
        .setup{background:#fff;margin:10px;padding:12px;border-radius:10px;box-shadow:0 2px 5px rgba(0,0,0,0.1)}
        .btn{padding:6px 12px;border:1px solid #ddd;border-radius:20px;background:#f8f9fa;margin:5px 5px 0 0}
        .btn.active{background:#ffbe00;color:#000;font-weight:bold}
        .title{background:#
