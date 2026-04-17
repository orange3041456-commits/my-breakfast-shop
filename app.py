from flask import Flask, render_template_string, request, jsonify, session, redirect
import os
import secrets
from collections import Counter
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

# --- 密碼設定 ---
BOSS_PASSWORD = "8888" 

# --- 菜單資料 (可自行增減) ---
MENU_DATA = {
    "蛋餅類": [
        {"name": "原味蛋餅", "price": 30, "can_add": True}, {"name": "蔥香蛋餅", "price": 35, "can_add": True}, 
        {"name": "肉鬆蛋餅", "price": 40, "can_add": True}, {"name": "里肌肉蛋餅", "price": 50, "can_add": True}
    ],
    "飲品 (L)": [
        {"name": "紅茶", "price": 25}, {"name": "香醇奶茶", "price": 30}
    ]
}

history = []
total_income = 0

@app.before_request
def ensure_session():
    if 'cart' not in session: session['cart'] = []
    if 'order_info' not in session: session['order_info'] = {"type": "外帶", "table": ""}

@app.route("/")
def index():
    cart = session.get('cart', [])
    return render_template_string(INDEX_HTML, menu=MENU_DATA, cart_len=len(cart), total=sum(i['price'] for i in cart))

@app.route("/add", methods=["POST"])
def add():
    temp = session.get('cart', [])
    temp.append({"name": request.form.get("name"), "price": int(request.form.get("price"))})
    session['cart'] = temp
    return jsonify({"count": len(session['cart']), "total": sum(i['price'] for i in session['cart'])})

@app.route("/update_info", methods=["POST"])
def update_info():
    session['order_info'] = {"type": request.form.get("type"), "table": request.form.get("table")}
    return jsonify({"status": "ok"})

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
        now_time = datetime.now().strftime('%H:%M')
        summary = "<br>".join([f"{n} x{c}" for n,c in counts.items()])
        total_income += t
        order_data = {"id": secrets.token_hex(4), "loc": loc, "price": t, "summary": summary, "time": now_time}
        history.append(order_data)
        session.clear()
        # 跳轉到「自動列印」的中間頁面
        return render_template_string(AUTO_PRINT_HTML, order=order_data)
    return redirect("/")

@app.route("/boss")
def boss():
    pw = request.args.get("pw")
    if pw != BOSS_PASSWORD:
        return "<h1>❌ 密碼錯誤</h1>", 403
    return render_template_string(BOSS_HTML, total=total_income, logs=history[::-1], current_pw=BOSS_PASSWORD)

@app.route("/delete_order", methods=["POST"])
def delete_order():
    global history
    order_id = request.form.get("id")
    history = [h for h in history if h['id'] != order_id]
    return jsonify({"status": "deleted"})

# --- HTML 模板 ---

INDEX_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no"><title>晨食麵所</title><style>
body{font-family:sans-serif;background:#fdfaf0;margin:0;padding:10px;padding-bottom:80px}
.header{background:#ffbe00;color:#fff;padding:15px;text-align:center;border-radius:0 0 15px 15px;font-weight:bold}
.order-setup{background:#fff;margin:10px 0;padding:15px;border-radius:10px;box-shadow:0 2px 5px rgba(0,0,0,0.1);border-left:5px solid #ffbe00}
.type-btn, .table-btn{padding:8px 15px;border:1px solid #ddd;border-radius:20px;background:#f8f9fa;cursor:pointer;margin-right:5px;font-size:14px;margin-bottom:5px}
.type-btn.active, .table-btn.active{background:#ffbe00;color:#000;font-weight:bold}
.section-title{background:#5d4037;color:white;padding:8px 12px;border-radius:4px;margin-top:20px;font-size:16px;font-weight:bold}
.item-card{background:white;padding:12px;margin:8px 0;border-radius:10px;box-shadow:0 1px 3px rgba(0,0,0,0.1)}
.item-row{display:flex;justify-content:space-between;align-items:center}
.price{color:#e67e22;font-weight:bold}
.add-btn{background:#ffbe00;border:none;padding:8px 14px;border-radius:15px;font-weight:bold}
.footer{position:fixed;bottom:0;left:0;right:0;background:#333;color:white;padding:12px;display:flex;justify-content:space-between;align-items:center}
</style>
<script>
let currentTable = "";
function goToBoss(){ let p = prompt("請輸入管理員密碼："); if(p) location.href="/boss?pw="+p; }
function setOrderType(t,b){ fetch('/update_info',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:`type=${t}&table=${currentTable}`}); document.querySelectorAll('.type-btn').forEach(x=>x.classList.remove('active')); b.classList.add('active'); document.getElementById('table-select').style.display=(t==='內用')?'block':'none'; updateDisplay(); }
function setTable(n,b){ currentTable=n; fetch('/update_info',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:`type=內用&table=${n}`}); document.querySelectorAll('.table-btn').forEach(x=>x.classList.remove('active')); b.classList.add('active'); updateDisplay(); }
function updateDisplay(){ document.getElementById('display-table').innerText = currentTable ? ` (第 ${currentTable} 桌)` : ""; }
function addToCart(n,p){ fetch('/add',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:`name=${encodeURIComponent(n)}&price=${p}`}).then(r=>r.json()).then(d=>{ document.getElementById('c-count').innerText=d.count; document.getElementById('c-total').innerText=d.total; }); }
</script></head>
<body>
<div class="header" onclick="goToBoss()">🍜 晨食麵所</div>
<div class="order-setup">用餐方式：<button class="type-btn active" onclick="setOrderType('外帶', this)">🥡 外帶</button><button class="type-btn" onclick="setOrderType('內用', this)">🍽️ 內用</button>
<div id="table-select" style="display:none;margin-top:10px;">桌號：{% for n in range(1, 11) %}<button class="table-btn" onclick="setTable('{{n}}', this)">{{n}}</button>{% endfor %}</div></div>
{% for cat, items in menu.items() %}<div class="section-title">{{ cat }}</div>{% for item in items %}
<div class="item-card"><div class="item-row"><div><strong>{{ item.name }}</strong><br><span class="price">${{ item.price }}</span></div><button class="add-btn" onclick="addToCart('{{ item.name }}', {{ item.price }})">加入 +</button></div></div>
{% endfor %}{% endfor %}
<div class="footer"><span>已點 <span id="c-count">{{ cart_len }}</span> 項 | $<span id="c-total">{{ total }}</span> <span id="display-table"></span></span><a href="/cart" style="background:#ffbe00; color:#000; padding:8px 15px; border-radius:20px; text-decoration:none; font-weight:bold;">去結帳</a></div>
</body></html>
"""

CART_HTML = """
<div style="padding:20px; font-family:sans-serif; max-width:500px; margin:auto;"><h3>🛒 訂單確認</h3><p>用餐：{{ loc }}</p>
{% for name, count in counts.items() %}<p>{{ name }} <span style="color:red;">x {{ count }}</span></p>{% endfor %}<hr><h4>總計: ${{ total }}</h4>
<form action="/clear" method="POST"><button type="submit" style="width:100%; background:#ffbe00; padding:15px; border:none; border-radius:10px; font-weight:bold; font-size:18px;">確認送出並列印</button></form><br><a href="/" style="color:gray;">返回修改</a></div>
"""

# --- 關鍵：自動列印頁面 ---
AUTO_PRINT_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>列印訂單</title>
<style>
    body{font-family:sans-serif; text-align:center; padding-top:50px;}
    .ticket{ display:none; }
    @media print {
        body * { visibility: hidden; }
        .ticket, .ticket * { visibility: visible; }
        .ticket { display: block; position: fixed; left: 0; top: 0; width: 100%; font-size: 22px; padding: 10px; text-align: left; }
    }
</style>
<script>
    window.onload = function() {
        window.print(); // 自動彈出列印選單
        setTimeout(function(){ location.href='/'; }, 2000); // 列印完自動回首頁
    }
</script></head>
<body>
    <h2>✅ 訂單已送出</h2>
    <p>正在呼叫列印選單...</p>
    <div class="ticket">
        <span style="float:right;">{{ order.time }}</span>
        <b style="font-size:26px;">{{ order.loc }}</b><hr>
        <div style="margin:15px 0;">{{ order.summary | safe }}</div><hr>
        <b>總金額：${{ order.price }}</b>
    </div>
</body></html>
"""

BOSS_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>老闆後台</title><style>
body{font-family:sans-serif;background:#f4f4f4;padding:10px}
.order-item{background:white;padding:15px;margin-bottom:10px;border-radius:10px}
</style><script>
function del(id,e){ if(confirm('完成？')){ fetch('/delete_order',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:`id=${id}`}).then(()=>e.closest('.order-item').style.display='none'); }}
</script></head>
<body>
<div style="display:flex; justify-content:space-between; align-items:center;"><h2>今日營收：${{ total }}</h2><button onclick="location.href='/'">回點餐頁</button></div>
{% for h in logs %}<div class="order-item">
<span style="float:right;">{{ h.time }}</span><b>{{ h.loc }}</b><br>
<p>{{ h.summary | safe }}</p><b>額：${{ h.price }}</b>
<button onclick="del('{{h.id}}',this)" style="float:right; color:green; border:none; background:none; font-weight:bold;">[✔ 完成]</button>
</div>{% endfor %}</body></html>
"""

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
