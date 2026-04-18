from flask import Flask, render_template_string, request, jsonify, session, redirect
import os, secrets, requests
from collections import Counter
from datetime import datetime

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax')

BOSS_PASSWORD = "8888" 

# ==========================================
# 🔗 [Google 試算表串聯設定]
# ==========================================
G_URL = "https://docs.google.com/forms/d/e/1FAIpQLSe5HJ_rQDNaSXNo6l38DYMFErzna8Rmqjp8X61cgPZ2d8QOqA/formResponse"
G_ENTRY_SUMMARY = "entry.303092604"  
G_ENTRY_PRICE = "entry.157627510"    
G_ENTRY_TIME = "entry.1541194223"     

def sync_to_google(summary, price, info):
    clean_summary = summary.replace('<br>', ' | ')
    payload = {
        G_ENTRY_SUMMARY: clean_summary,
        G_ENTRY_PRICE: str(price),
        G_ENTRY_TIME: f"{datetime.now().strftime('%m/%d %H:%M:%S')} ({info})"
    }
    try:
        requests.post(G_URL, data=payload, timeout=5)
    except:
        pass

# ==========================================
# 🍱 [菜單資料 - 僅保留範例，其餘請保留您原有的內容]
# ==========================================
MENU_DATA = {
    "吃爽組合 (套餐)": [
        {"name": "肉蛋吐司+紅茶", "price": 60},
        {"name": "薯條OR雞塊+飲品", "price": 60, "opts": [["選薯條", "選雞塊"], ["選紅茶", "選冷泡茶"]]}
    ],
    "蛋餅類": [
        {"name": "原味蛋餅", "price": 30, "can_add": True}, 
        {"name": "起司蛋餅", "price": 40, "can_add": True}
    ],
    "飲品 (L)": [
        {"name": "紅茶", "price": 25}, {"name": "鮮奶茶", "price": 45}
    ]
}

history = [] # 儲存待處理訂單
total_income = 0

@app.before_request
def ensure_session():
    if 'cart' not in session: session['cart'] = []
    if 'info' not in session: session['info'] = {"type": "外帶", "table": ""}

# --- [1. 客人手機端 / 老闆幫點餐 共同介面] ---
@app.route("/")
def index():
    cart = session.get('cart', [])
    tid = request.args.get('table')
    if tid: session['info'] = {"type": "內用", "table": tid}
    return render_template_string(INDEX_HTML, menu=MENU_DATA, cart_len=len(cart), total=sum(i['price'] for i in cart), table_id=tid)

@app.route("/add", methods=["POST"])
def add():
    temp = session.get('cart', [])
    temp.append({"id": secrets.token_hex(4), "name": request.form.get("name"), "price": int(request.form.get("price"))})
    session['cart'] = temp
    return jsonify({"count": len(session['cart']), "total": sum(i['price'] for i in session['cart'])})

@app.route("/clear", methods=["POST"])
def clear():
    global total_income
    cart = session.get('cart', [])
    info = session.get('info', {"type": "外帶", "table": ""})
    t = sum(i['price'] for i in cart)
    if t > 0:
        loc = f"{info['type']}" + (f"-{info['table']}桌" if info['table'] else "")
        counts = Counter([i['name'] for i in cart])
        summary_html = "<br>".join([f"{n} x{c}" for n,c in counts.items()])
        total_income += t
        # 存入待處理清單，讓平板顯示
        order = {"id": secrets.token_hex(4), "loc": loc, "price": t, "summary": summary_html, "time": datetime.now()}
        history.append(order)
        session.clear()
        return render_template_string(SUCCESS_HTML) # 僅顯示成功畫面
    return redirect("/")

# --- [2. 老闆平板端 - 接單控制中心] ---
@app.route("/boss")
def boss():
    if request.args.get("pw") != BOSS_PASSWORD: return "<h1>❌</h1>", 403
    return render_template_string(BOSS_HTML, total=total_income, logs=history[::-1])

@app.route("/print_order/<oid>")
def print_order(oid):
    target = next((h for h in history if h['id'] == oid), None)
    if target: return render_template_string(PRINT_HTML, order=target)
    return "訂單不存在", 404

@app.route("/delete_order", methods=["POST"])
def delete_order():
    global history
    oid = request.form.get("id")
    target = next((h for h in history if h['id'] == oid), None)
    if target:
        sync_to_google(target['summary'], target['price'], target['loc'])
        history = [h for h in history if h['id'] != oid]
        return jsonify({"status": "ok"})
    return jsonify({"status": "error"}), 404

# --- HTML 模板區 ---

# [客人點餐介面 - 與原先雷同但優化手機體驗]
INDEX_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<style>
    body { font-family: sans-serif; background: #fdfaf0; margin: 0; padding-bottom: 80px; }
    .header { background: #ffbe00; padding: 15px; text-align: center; font-weight: bold; font-size: 1.2rem; }
    .title { background: #5d4037; color: white; padding: 8px 15px; margin-top: 10px; }
    .card { background: white; margin: 10px; padding: 15px; border-radius: 10px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    .btn-add { background: #ffbe00; border: none; padding: 10px 20px; border-radius: 20px; font-weight: bold; cursor: pointer; }
    .footer { position: fixed; bottom: 0; left: 0; right: 0; background: #333; color: white; padding: 15px; display: flex; justify-content: space-between; align-items: center; }
</style>
<script>
    function buy(n, p) {
        fetch('/add', {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body:"name="+encodeURIComponent(n)+"&price="+p})
        .then(r=>r.json()).then(d=>{ document.getElementById('cc').innerText=d.count; document.getElementById('ct').innerText=d.total; });
    }
</script></head>
<body>
    <div class="header">🍜 晨食麵所 (點餐)</div>
    <div style="text-align:center; padding:10px;"><b>{{table_id if table_id else '外帶'}}</b></div>
    {% for cat,items in menu.items() %}
        <div class="title">{{cat}}</div>
        {% for item in items %}
            <div class="card">
                <div><b>{{item.name}}</b><br><span style="color:#e67e22;">${{item.price}}</span></div>
                <button class="btn-add" onclick="buy('{{item.name}}', {{item.price}})">加入</button>
            </div>
        {% endfor %}
    {% endfor %}
    <div class="footer">
        <span>已點 <span id="cc">0</span> 項 | $<span id="ct">0</span></span>
        <a href="/cart" style="background:#ffbe00; color:black; padding:8px 20px; border-radius:20px; text-decoration:none; font-weight:bold;">去結帳</a>
    </div>
</body></html>
"""

# [客人點完餐看到的成功畫面]
SUCCESS_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<style>body{font-family:sans-serif; text-align:center; padding-top:100px; background:#fdfaf0;}</style>
<script>setTimeout(()=>location.href='/', 5000);</script></head>
<body><h1 style="color:#2ecc71;">✅ 訂單已送出</h1><p>請告知櫃台您的桌號，感謝您的耐心等待！</p></body></html>
"""

# [老闆平板專用介面]
BOSS_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<style>
    body{font-family:sans-serif; background:#f4f4f4; padding:20px;}
    .order-card{background:white; padding:20px; border-radius:15px; margin-bottom:20px; border-left:10px solid #ffbe00; box-shadow:0 4px 10px rgba(0,0,0,0.1);}
    .btn-print{background:#2980b9; color:white; padding:15px 25px; border-radius:10px; border:none; font-weight:bold; font-size:1.1rem;}
    .btn-done{background:#27ae60; color:white; padding:15px 25px; border-radius:10px; border:none; font-weight:bold; font-size:1.1rem; margin-left:10px;}
</style>
<script>
    // 每 30 秒自動更新，檢查有沒有新訂單
    setInterval(()=>location.reload(), 30000);
    function doPrint(id){ window.open('/print_order/'+id, '_blank', 'width=350,height=600'); }
    function doFinish(id, btn){
        if(confirm('確認完成並寫入試算表？')){
            fetch('/delete_order', {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'}, body:"id="+id})
            .then(()=>btn.closest('.order-card').remove());
        }
    }
</script></head>
<body>
    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
        <h2>💰 今日累計：${{total}}</h2>
        <div>
            <button onclick="location.href='/'" style="padding:10px 20px; border-radius:10px; background:#5d4037; color:white; border:none; font-weight:bold;">幫客人點餐</button>
            <button onclick="location.reload()" style="padding:10px 20px; border-radius:10px; margin-left:10px;">🔄 重新整理</button>
        </div>
    </div>
    {% for h in logs %}
    <div class="order-card">
        <span style="float:right; color:gray;">{{h.time.strftime('%H:%M:%S')}}</span>
        <h2 style="margin:0 0 10px 0;">{{h.loc}}</h2>
        <div style="background:#f9f9f9; padding:15px; border-radius:10px; font-size:1.2rem; line-height:1.6; margin-bottom:15px;">
            {{h.summary|safe}}
        </div>
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <b style="font-size:1.8rem; color:#e67e22;">${{h.price}}</b>
            <div>
                <button class="btn-print" onclick="doPrint('{{h.id}}')">🖨️ 列印</button>
                <button class="btn-done" onclick="doFinish('{{h.id}}', this)">✔️ 完成</button>
            </div>
        </div>
    </div>
    {% endfor %}
</body></html>
"""

# [列印格式 - 老闆平板點擊列印後彈出的視窗]
PRINT_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><style>
    body{font-family:sans-serif; width:280px; padding:5px;}
    .h{font-size:1.5rem; font-weight:bold; border-bottom:2px dashed #000; padding-bottom:5px;}
    .i{font-size:1.2rem; line-height:1.5; margin:10px 0;}
</style><script>window.onload=function(){window.print();setTimeout(()=>window.close(),500)}</script></head>
<body>
    <div class="h">{{order.loc}} <span style="font-size:0.8rem; float:right;">{{order.time.strftime('%H:%M')}}</span></div>
    <div class="i">{{order.summary|safe}}</div>
    <div style="border-top:2px dashed #000; padding-top:5px; text-align:right; font-weight:bold; font-size:1.3rem;">總計：${{order.price}}</div>
</body></html>
"""

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
