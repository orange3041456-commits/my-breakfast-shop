from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
import os, secrets, requests, datetime
import pytz
from collections import Counter

app = Flask(__name__)
app.secret_key = "morning_noodle_v87_security_pro"
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax')

# --- 設定區 ---
BOSS_PASSWORD = "8888" 
G_URL = "https://docs.google.com/forms/d/e/1FAIpQLSe5HJ_rQDNaSXNo6l38DYMFErzna8Rmqjp8X61cgPZ2d8QOqA/formResponse"
G_ENTRIES = {"summary": "entry.303092604", "price": "entry.157627510", "time": "entry.1541194223"}

def sync_to_google(summary, price, info, pay_method):
    tw_tz = pytz.timezone('Asia/Taipei')
    time_str = datetime.datetime.now(tw_tz).strftime('%m/%d %H:%M:%S')
    payload = {
        G_ENTRIES["summary"]: summary.replace('<br>', ' | '),
        G_ENTRIES["price"]: str(price),
        G_ENTRIES["time"]: f"{time_str} ({info}-{pay_method})"
    }
    try: requests.post(G_URL, data=payload, timeout=0.8)
    except: pass

# --- 選單數據 ---
MENU_DATA = {
    "吃爽組合 (套餐)": [
        {"name": "薯條OR雞塊+飲品", "price": 60, "sub": "⚠️ 請選品項+飲品", "opts": [["選薯條", "選雞塊"], ["選紅茶", "選冷泡茶", "換奶茶(+5)", "換鮮奶茶(+15)"]], "price_map": {"換奶茶(+5)": 5, "換鮮奶茶(+15)": 15}},
        {"name": "肉蛋吐司+紅茶", "price": 60, "can_no_crust": True},
        {"name": "熱狗(3支)+蛋+飲品", "price": 50, "opts": [["選紅茶", "選冷泡茶", "換奶茶(+5)", "換鮮奶茶(+15)"]], "price_map": {"換奶茶(+5)": 5, "換鮮奶茶(+15)": 15}}
    ],
    "蛋餅類": [
        {"name": "原味蛋餅", "price": 30, "can_add": True, "add_meat": True}, 
        {"name": "蔥香蛋餅", "price": 35, "can_add": True, "add_meat": True},
        {"name": "起司蛋餅", "price": 40, "can_add": True, "add_meat": True}
    ],
    "泡麵系列 (2包)": [
        {"name": "招牌炒泡麵", "price": 70, "can_add": True, "add_meat": True, "can_spicy": True, "can_no_side": True, "has_meat": True, "sub": "高麗菜、紅蘿蔔、肉絲、蒜碎、蔥"}
    ]
}

history = []

@app.before_request
def ensure_session():
    if 'cart' not in session: session['cart'] = []
    if 'info' not in session: session['info'] = {"type": "外帶", "table": ""}

@app.route("/")
def index():
    cart = session.get('cart', [])
    is_boss = session.get('is_boss', False)
    return render_template_string(INDEX_HTML, menu=MENU_DATA, cart_len=len(cart), total=sum(i['price'] for i in cart), is_boss=is_boss)

@app.route("/update_info", methods=["POST"])
def update_info():
    session['info'] = {"type": request.form.get("type"), "table": request.form.get("table", "")}
    return jsonify({"status": "ok"})

@app.route("/add", methods=["POST"])
def add():
    temp = session.get('cart', [])
    temp.append({"id": secrets.token_hex(4), "name": request.form.get("name"), "price": int(request.form.get("price"))})
    session['cart'] = temp
    return jsonify({"count": len(session['cart']), "total": sum(i['price'] for i in session['cart'])})

@app.route("/del_item", methods=["POST"])
def del_item():
    session['cart'] = [i for i in session.get('cart', []) if i['id'] != request.form.get("id")]
    return jsonify({"status": "ok"})

@app.route("/cart")
def view_cart():
    cart = session.get('cart', [])
    info = session.get('info', {"type": "外帶", "table": ""})
    loc = f"{info['type']}" + (f"-{info['table']}桌" if info['table'] else "")
    return render_template_string(CART_HTML, cart=cart, total=sum(i['price'] for i in cart), loc=loc)

@app.route("/clear", methods=["POST"])
def clear():
    cart = session.get('cart', [])
    if not cart: return redirect("/")
    info = session.get('info', {"type": "外帶", "table": ""})
    t = sum(i['price'] for i in cart)
    loc = f"{info['type']}" + (f"-{info['table']}桌" if info['table'] else "")
    summary = "<br>".join([f"{n} x{c}" for n,c in Counter([i['name'] for i in cart]).items()])
    history.append({"id": secrets.token_hex(4), "loc": loc, "price": t, "summary": summary, "time": datetime.datetime.now(pytz.timezone('Asia/Taipei')), "done": False, "pay": "未選"})
    session['cart'] = [] 
    return render_template_string(SUCCESS_HTML)

# --- 後台與列印邏輯 ---
@app.route("/boss")
def boss():
    pw = request.args.get("pw")
    # 如果密碼正確，就給予 session 權限
    if pw == BOSS_PASSWORD:
        session['is_boss'] = True
    
    if not session.get('is_boss'):
        return "權限不足，請重新登入", 403

    stats = {"total_money": sum(h['price'] for h in history if h['done']), "total_count": sum(1 for h in history if h['done'])}
    return render_template_string(BOSS_HTML, stats=stats, logs=history[::-1])

@app.route("/boss_logout")
def boss_logout():
    session.pop('is_boss', None)
    return redirect(url_for('index'))

@app.route("/finish_order", methods=["POST"])
def finish_order():
    if not session.get('is_boss'): return jsonify({"status": "error"}), 403
    oid, method = request.form.get("id"), request.form.get("method")
    target = next((h for h in history if h['id'] == oid), None)
    if target:
        if method == "RESET": 
            target['done'], target['pay'] = False, "未選"
        else:
            target['done'], target['pay'] = True, method
            sync_to_google(target['summary'], target['price'], target['loc'], method)
        return jsonify({"status": "ok"})
    return jsonify({"status": "error"}), 404

# --- 頁面模板 ---
INDEX_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,user-scalable=no">
<style>
    body { font-family: sans-serif; background: #fdfaf0; margin: 0; padding: 0 10px 100px; }
    .header { background: #ffbe00; color: #fff; padding: 15px; text-align: center; border-radius: 0 0 15px 15px; font-weight: bold; font-size: 20px; }
    .setup { background: #fff; margin: 10px 0; padding: 12px; border-radius: 10px; border-left: 6px solid #ffbe00; }
    .btn { padding: 8px 15px; border: 1.5px solid #ddd; border-radius: 20px; background: #f8f9fa; margin: 3px; cursor: pointer; }
    .btn.active { background: #ffbe00; font-weight: bold; border-color: #ffbe00; }
    .title { background: #5d4037; color: #fff; padding: 10px 15px; border-radius: 5px; margin-top: 15px; }
    .card { background: #fff; padding: 15px; margin: 10px 0; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    .row { display: flex; justify-content: space-between; align-items: center; }
    .add { background: #ffbe00; border: none; padding: 10px 20px; border-radius: 25px; font-weight: bold; cursor: pointer; }
    .grid { margin-top: 12px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; border-top: 1px dashed #eee; padding-top: 12px; }
    .opt { background: #fcfcfc; border: 1.5px solid #eee; padding: 8px 3px; border-radius: 8px; font-size: 13px; text-align: center; cursor: pointer; }
    .opt.active { background: #5d4037; color: #fff; border-color: #5d4037; }
    .footer { position: fixed; bottom: 0; left: 0; right: 0; background: #333; color: #fff; padding: 15px; display: flex; justify-content: space-between; align-items: center; z-index: 100; }
    .boss-link { position: fixed; top: 10px; right: 10px; background: #e74c3c; color: #fff; padding: 5px 10px; border-radius: 5px; text-decoration: none; font-size: 12px; z-index: 101; animation: blink 2s infinite; }
    @keyframes blink { 50% { opacity: 0.5; } }
</style>
<script>
    let opts={}; let curT="{{session.info.table}}"; let curType="{{session.info.type}}";
    let pressTimer;
    function startPress(){ pressTimer = window.setTimeout(() => { let p=prompt("後台密碼"); if(p) window.location.href='/boss?pw='+p; }, 2000); }
    function endPress(){ window.clearTimeout(pressTimer); }
    function setT(t,b){curType=t;if(t==='外帶')curT='';fetch('/update_info',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:"type="+t+"&table="+curT});document.querySelectorAll('.type-btn').forEach(x=>x.classList.remove('active'));b.classList.add('active');document.getElementById('ts').style.display=(t==='內用')?'block':'none'}
    function setN(n,b){curT=n;fetch('/update_info',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:"type=內用&table="+n});document.querySelectorAll('.table-btn').forEach(x=>x.classList.remove('active'));b.classList.add('active')}
    function buy(btn){
        let n=btn.dataset.name, p=parseInt(btn.dataset.price);
        if(curType==='內用'&&!curT){alert("請選桌號");return;}
        fetch('/add',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:"name="+encodeURIComponent(n)+"&price="+p})
        .then(r=>r.json()).then(d=>{ document.getElementById('cc').innerText=d.count; document.getElementById('ct').innerText=d.total; });
    }
</script></head>
<body>
    {% if is_boss %}<a href="/boss" class="boss-link">⚙️ 返回後台</a>{% endif %}
    <div class="header" onmousedown="startPress()" onmouseup="endPress()" ontouchstart="startPress()" ontouchend="endPress()">🍜 晨食麵所</div>
    <div class="setup">
        方式：<button class="btn type-btn {{ 'active' if session.info.type == '外帶' else '' }}" onclick="setT('外帶',this)">外帶</button>
        <button class="btn type-btn {{ 'active' if session.info.type == '內用' else '' }}" onclick="setT('內用',this)">內用</button>
        <div id="ts" style="display:{{ 'block' if session.info.type == '內用' else 'none' }};margin-top:8px">
            桌號：{% for n in range(1,6) %}<button class="btn table-btn {{ 'active' if session.info.table == n|string else '' }}" onclick="setN('{{n}}',this)">{{n}}</button>{% endfor %}
        </div>
    </div>
    {% for cat, items in menu.items() %}
        <div class="title">{{cat}}</div>
        {% for item in items %}
            <div class="card"><div class="row"><div><b>{{item.name}}</b><br><span style="color:#e67e22;">${{item.price}}</span></div><button class="add" data-name="{{item.name}}" data-price="{{item.price}}" onclick="buy(this)">加入</button></div></div>
        {% endfor %}
    {% endfor %}
    <div class="footer"><span>已點 <span id="cc">{{cart_len}}</span> 項 | $<span id="ct">{{total}}</span></span><a href="/cart" style="background:#ffbe00;color:#000;padding:8px 20px;border-radius:20px;text-decoration:none;font-weight:bold;">去結帳</a></div>
</body></html>
"""

BOSS_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<style>
    body{font-family:sans-serif;background:#eee;padding:15px;}
    .o{background:#fff;padding:15px;margin-bottom:10px;border-radius:8px;border-left:8px solid #ffbe00;}
    .o.done{border-left-color:#2ecc71;opacity:0.7;}
    .btn{padding:10px 15px;border:none;border-radius:5px;font-weight:bold;cursor:pointer;margin-top:10px;}
    .cash{background:#2ecc71;color:#fff;}.line{background:#00b900;color:#fff;}.reset{background:#e74c3c;color:#fff;font-size:12px;}
    @media print { body * { visibility: hidden; } #print-area, #print-area * { visibility: visible; } #print-area { position: absolute; left: 0; top: 0; width: 54mm; font-size: 14px; } }
</style>
<script>
    function finish(id, m, loc, time, summary, price) {
        if(m==='RESET'){ fetch('/finish_order',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:"id="+id+"&method=RESET"}).then(()=>location.reload()); return; }
        let p = `<div id="print-area"><h3>晨食麵所</h3><p>${time}</p><b>區域: ${loc}</b><hr>${summary}<hr><b>總計: $${price} (${m})</b><br>.<br>.</div>`;
        let div = document.createElement('div'); div.innerHTML = p; document.body.appendChild(div);
        window.print();
        fetch('/finish_order',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:"id="+id+"&method="+m}).then(()=>location.reload());
    }
</script></head>
<body>
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <a href="/" style="text-decoration:none; color:#333;">⬅️ 前台下單頁</a>
        <a href="/boss_logout" style="color:red; font-size:12px;">登出後台</a>
    </div>
    <h3>營收: ${{stats.total_money}} ({{stats.total_count}}單)</h3><hr>
    {% for h in logs %}<div class="o {{ 'done' if h.done else '' }}">
        <b>{{h.loc}}</b> | {{h.time.strftime('%H:%M:%S')}}
        <div style="padding:5px 0;">{{h.summary|safe}}</div>
        <b>${{h.price}}</b><br>
        {% if not h.done %}
            <button class="btn cash" onclick="finish('{{h.id}}','現金','{{h.loc}}','{{h.time.strftime('%H:%M:%S')}}','{{h.summary}}','{{h.price}}')">現金</button>
            <button class="btn line" onclick="finish('{{h.id}}','LINE Pay','{{h.loc}}','{{h.time.strftime('%H:%M:%S')}}','{{h.summary}}','{{h.price}}')">LINE Pay</button>
        {% else %}
            ✅ ({{h.pay}}) <button class="btn reset" onclick="finish('{{h.id}}','RESET')">重設</button>
        {% endif %}
    </div>{% endfor %}
</body></html>
"""

CART_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><style>body{font-family:sans-serif;padding:20px;background:#fdfaf0;}.item{background:#fff;padding:15px;margin-bottom:10px;border-radius:10px;display:flex;justify-content:space-between;}</style></head>
<body><h3>🛒 結帳明細 ({{loc}})</h3>{% for i in cart %}<div class="item"><div><b>{{i.name}}</b><br>${{i.price}}</div><button onclick="fetch('/del_item',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'id={{i.id}}'}).then(()=>location.reload())">刪除</button></div>{% endfor %}
<hr><h4>總計: ${{total}}</h4><form action="/clear" method="POST"><button type="submit" style="width:100%;background:#ffbe00;padding:15px;border:none;border-radius:10px;font-weight:bold;">確認送出訂單</button></form><br><a href="/" style="display:block;text-align:center;color:gray;text-decoration:none;">返回繼續加點</a></body></html>
"""

SUCCESS_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><script>setTimeout(()=>location.href='/', 3000)</script></head><body style="text-align:center;padding-top:100px;"><h1>✅ 訂單已送出</h1><p>請至櫃檯結帳</p></body></html>
"""

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
