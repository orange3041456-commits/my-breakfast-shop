from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
import os
import secrets
from collections import Counter
from datetime import datetime

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax')

BOSS_PASSWORD = "8888" 

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
    "炒麵系列 (200g)": [
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
        {"name": "煎蛋吐司 (無生菜番茄)", "price": 35, "can_add": True, "no_veg": False}, 
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

history = []
total_income = 0

@app.before_request
def ensure_session():
    if 'cart' not in session: session['cart'] = []
    if 'order_info' not in session: session['order_info'] = {"type": "外帶", "table": ""}

@app.route("/")
def index():
    cart = session.get('cart', [])
    table_from_url = request.args.get('table')
    if table_from_url:
        session['order_info'] = {"type": "內用", "table": table_from_url}
    return render_template_string(INDEX_HTML, menu=MENU_DATA, cart_len=len(cart), total=sum(i['price'] for i in cart), table_id=table_from_url)

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
        now_time = datetime.now().strftime('%H:%M')
        summary = "<br>".join([f"{n} x{c}" for n,c in counts.items()])
        total_income += t
        order_data = {"id": secrets.token_hex(4), "loc": loc, "price": t, "summary": summary, "time": now_time}
        history.append(order_data)
        session.clear()
        return render_template_string(AUTO_PRINT_HTML, order=order_data)
    return redirect("/")

@app.route("/boss")
def boss():
    pw = request.args.get("pw")
    if pw != BOSS_PASSWORD: return "<h1>❌ 密碼錯誤</h1>", 403
    return render_template_string(BOSS_HTML, total=total_income, logs=history[::-1])

@app.route("/delete_order", methods=["POST"])
def delete_order():
    global history
    order_id = request.form.get("id")
    history = [h for h in history if h['id'] != order_id]
    return jsonify({"status": "deleted"})

INDEX_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no"><title>晨食麵所</title><style>
body{font-family:sans-serif;background:#fdfaf0;margin:0;padding:10px;padding-bottom:80px}
.header{background:#ffbe00;color:#fff;padding:15px;text-align:center;border-radius:0 0 15px 15px;font-weight:bold;user-select:none;-webkit-user-select:none}
.order-setup{background:#fff;margin:10px 0;padding:15px;border-radius:10px;box-shadow:0 2px 5px rgba(0,0,0,0.1);border-left:5px solid #ffbe00}
.type-btn,.table-btn{padding:8px 15px;border:1px solid #ddd;border-radius:20px;background:#f8f9fa;cursor:pointer;margin:5px 5px 0 0;font-size:14px}
.type-btn.active,.table-btn.active{background:#ffbe00;color:#000;font-weight:bold}
.section-title{background:#5d4037;color:#fff;padding:8px 12px;border-radius:4px;margin-top:20px;font-size:16px;font-weight:bold}
.item-card{background:#fff;padding:12px;margin:8px 0;border-radius:10px;box-shadow:0 1px 3px rgba(0,0,0,0.1)}
.item-row{display:flex;justify-content:space-between;align-items:center}
.price{color:#e67e22;font-weight:bold}
.add-btn{background:#ffbe00;border:none;padding:8px 14px;border-radius:15px;font-weight:bold;cursor:pointer}
.opt-grid{margin-top:10px;display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;border-top:1px dashed #eee;padding-top:10px}
.opt-btn{background:#f8f9fa;border:1px solid #ddd;padding:8px 0;border-radius:6px;font-size:11px;text-align:center;cursor:pointer;color:#666}
.opt-btn.active{background:#5d4037;color:#fff}
.footer{position:fixed;bottom:0;left:0;right:0;background:#333;color:#fff;padding:12px;display:flex;justify-content:space-between;align-items:center;z-index:100}
</style>
<script>
let opts={};let curTable="{{table_id if table_id else ''}}";let timer;
function startHold(){timer=setTimeout(()=>{let p=prompt("管理密碼：");if(p)location.href="/boss?pw="+p},3000)}
function endHold(){clearTimeout(timer)}
function setOrderType(t,b){fetch('/update_info',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:`type=${t}&table=${curTable}`});document.querySelectorAll('.type-btn').forEach(x=>x.classList.remove('active'));b.classList.add('active');let ts=document.getElementById('table-select');if(ts)ts.style.display=(t==='內用')?'block':'none'}
function setTable(n,b){curTable=n;fetch('/update_info',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:`type=內用&table=${n}`});document.querySelectorAll('.table-btn').forEach(x=>x.classList.remove('active'));b.classList.add('active')}
function addToCart(n,p,i){let fn=n,fp=p;Object.keys(opts).forEach(k=>{if(k.startsWith(i+'_')){fn+='+'+opts[k].name;fp+=opts[k].price}});fetch('/add',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:`name=${encodeURIComponent(fn)}&price=${fp}`}).then(r=>r.json()).then(d=>{document.getElementById('c-count').innerText=d.count;document.getElementById('c-total').innerText=d.total;document.querySelectorAll(`[data-item="${i}"]`).forEach(x=>x.classList.remove('active'));Object.keys(opts).forEach(k=>{if(k.startsWith(i+'_'))delete opts[k]})})}
function toggleOpt(i,n,p,b){let k=i+'_'+n;if(opts[k]){delete opts[k];b.classList.remove('active')}else{opts[k]={name:n,price:p};b.classList.add('active')}}
</script></head>
<body>
<div class="header" onmousedown="startHold()" onmouseup="endHold()" ontouchstart="startHold()" ontouchend="endHold()">🍜 晨食麵所</div>
<div class="order-setup">
{% if table_id %}<div style="text-align:center;font-weight:bold;color:#5d4037">歡迎內用，桌號：{{table_id}}</div>
{% else %}用餐：<button class="type-btn active" onclick="setOrderType('外帶',this)">外帶</button><button class="type-btn" onclick="setOrderType('內用',this)">內用</button>
<div id="table-select" style="display:none;margin-top:10px">桌號：{% for n in range(1,6) %}<button class="table-btn" onclick="setTable('{{n}}',this)">{{n}}</button>{% endfor %}</div>{% endif %}</div>
{% for cat,items in menu.items() %}<div class="section-title">{{cat}}</div>{% for item in items %}
{% set iid=loop.index0 ~ cat|replace("/","")|replace(" ","")|replace("(","")|replace(")","") %}
<div class="item-card"><div class="item-row"><div><strong>{{item.name}}</strong><br><span class="price">${{item.price}}</span></div><button class="add-btn" onclick="addToCart('{{item.name}}',{{item.price}},'{{iid}}')">加入 +</button></div>
{% if item.can_add %}<div class="opt-grid">
<div class="opt-btn" data-item="{{iid}}" onclick="toggleOpt('{{iid}}','加蛋',15,this)">+ 加蛋 ($15)</div>
<div class="opt-btn" data-item="{{iid}}" onclick="toggleOpt('{{iid}}','加里肌',25,this)">+ 加里肌 ($25)</div>
<div class="opt-btn" data-item="{{iid}}" onclick="toggleOpt('{{iid}}','加起司',15,this)">+ 加起司 ($15)</div>
{% if item.no_veg %}<div class="opt-btn" data-item="{{iid}}" onclick="toggleOpt('{{iid}}','不加生菜',0,this)" style="color:#e74c3c">✘ 不加生菜</div><div class="opt-btn" data-item="{{iid}}" onclick="toggleOpt('{{iid}}','不加番茄',0,this)" style="color:#e74c3c">✘ 不加番茄</div>{% endif %}
</div>{% endif %}</div>{% endfor %}{% endfor %}
<div class="footer"><span>已點 <span id="c-count">{{cart_len}}</span> 項 | $<span id="c-total">{{total}}</span></span><a href="/cart" style="background:#ffbe00;color:#000;padding:8px 15px;border-radius:20px;text-decoration:none;font-weight:bold">去結帳</a></div>
</body></html>
"""

CART_HTML = """
<div style="padding:20px;font-family:sans-serif;max-width:500px;margin:auto"><h3>🛒 訂單確認</h3><p>用餐：{{loc}}</p>
{% for n,c in counts.items() %}<p>{{n}} <span style="color:red">x {{c}}</span></p>{% endfor %}<hr><h4>總計: ${{total}}</h4>
<form action="/clear" method="POST"><button type="submit" style="width:100%;background:#ffbe00;padding:15px;border:none;border-radius:10px;font-weight:bold;font-size:18px">確認送出並列印</button></form><br><a href="/" style="color:gray">返回修改</a></div>
"""

AUTO_PRINT_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><title>列印中</title><style>
body{font-family:sans-serif;text-align:center;padding-top:50px}.ticket{display:none}
@media print{body *{visibility:hidden}.ticket,.ticket *{visibility:visible}.ticket{display:block;position:fixed;left:0;top:0;width:100%;font-size:24px;padding:20px}}
</style><script>window.onload=()=>{window.print();setTimeout(()=>{location.href='/'},1500)}</script></head>
<body><h2>✅ 訂單已完成</h2><div class="ticket"><span style="float:right">{{order.time}}</span><b>{{order.loc}}</b><hr>{{order.summary|safe}}<hr><b>總額：${{order.price}}</b></div></body></html>
"""

BOSS_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><title>後台</title><style>
body{font-family:sans-serif;background:#f4f4f4;padding:10px}.order-item{background:#fff;padding:15px;margin-bottom:10px;border-radius:10px}
</style><script>function del(id,e){if(confirm('完成？')){fetch('/delete_order',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:`id=${id}`}).then(()=>e.closest('.order-item').style.display='none')}}</script></head>
<body><div style="display:flex;justify-content:space-between"><h2>💰 營收：${{total}}</h2><button onclick="location.href='/'">回首頁</button></div>
{% for h in logs %}<div class="order-item"><span style="float:right;color:gray">{{h.time}}</span><b>{{h.loc}}</b><br><p>{{h.summary|safe}}</p><b>${{h.price}}</b><button onclick="del('{{h.id}}',this)" style="float:right;color:green;border:none;background:none;font-weight:bold">[完成]</button></div>{% endfor %}</body></html>
"""

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
