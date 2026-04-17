from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
import os, secrets
from collections import Counter
from datetime import datetime

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax')

BOSS_PASSWORD = "8888" 

MENU_DATA = {
    "吃爽組合 (套餐)": [
        {"name": "薯條OR雞塊+飲品", "price": 60, "opts": [["選薯條", "選雞塊"], ["選紅茶", "選冷泡茶"]]},
        {"name": "肉蛋吐司+紅茶", "price": 60},
        {"name": "熱狗(3支)+蛋+飲品", "price": 50, "opts": [["選紅茶", "選冷泡茶"]]},
        {"name": "草莓肉鬆吐司+飲品", "price": 50, "opts": [["選紅茶", "選冷泡茶"]]},
        {"name": "巧克力薯餅吐司+飲品", "price": 50, "opts": [["選紅茶", "選冷泡茶"]]}
    ],
    "蛋餅類": [
        {"name": "原味蛋餅", "price": 30, "can_add": True},
        {"name": "里肌肉蛋餅", "price": 50, "can_add": True}
    ],
    "麵類系列": [
        {"name": "招牌炒泡麵", "price": 70, "can_add": True, "can_spicy": True}, 
        {"name": "招牌爆香炒麵", "price": 70, "can_add": True, "can_spicy": True}
    ],
    "果醬吐司/厚片": [
        {"name": "巧克力吐司", "price": 25, "is_jam": True}, 
        {"name": "巧克力厚片", "price": 30, "is_jam": True},
        {"name": "花生吐司", "price": 25, "is_jam": True}, 
        {"name": "花生厚片", "price": 30, "is_jam": True}
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

# --- 確保以下字串定義靠左對齊，無多餘縮排 ---

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
        .title{background:#5d4037;color:#fff;padding:6px 15px;font-weight:bold;font-size:12px}
        .card{background:#fff;padding:12px;margin:8px 10px;border-radius:10px;box-shadow:0 1px 3px rgba(0,0,0,0.1)}
        .row{display:flex;justify-content:space-between;align-items:center}
        .add{background:#ffbe00;border:none;padding:6px 15px;border-radius:15px;font-weight:bold;cursor:pointer}
        .grid{margin-top:10px;display:grid;grid-template-columns:repeat(3, 1fr);gap:5px;border-top:1px dashed #eee;padding-top:10px}
        .opt{background:#f8f9fa;border:1px solid #eee;padding:5px;border-radius:5px;font-size:11px;text-align:center;cursor:pointer;color:#666}
        .opt.active{background:#5d4037;color:#fff;border-color:#5d4037}
        .footer{position:fixed;bottom:0;left:0;right:0;background:#333;color:#fff;padding:15px;display:flex;justify-content:space-between;align-items:center}
    </style>
    <script>
        let opts={}; let curT="{{table_id}}";
        function setT(t,b){fetch('/update_info',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:"type="+t+"&table="+curT});document.querySelectorAll('.type-btn').forEach(x=>x.classList.remove('active'));b.classList.add('active');document.getElementById('ts').style.display=(t==='內用')?'block':'none'}
        function setN(n,b){curT=n;fetch('/update_info',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:"type=內用&table="+n});document.querySelectorAll('.table-btn').forEach(x=>x.classList.remove('active'));b.classList.add('active')}
        function buy(n,p,i){
            let fn=n; let fp=p;
            Object.keys(opts).forEach(k => { if(k.indexOf(i+'_')===0){ fn+='+'+opts[k].n; fp+=opts[k].p } });
            fetch('/add',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:"name="+encodeURIComponent(fn)+"&price="+fp})
            .then(r=>r.json()).then(d=>{
                document.getElementById('cc').innerText=d.count;
                document.getElementById('ct').innerText=d.total;
                document.querySelectorAll(".opt[data-item='"+i+"']").forEach(x=>x.classList.remove('active'));
                Object.keys(opts).forEach(k=>{ if(k.indexOf(i+'_')===0) delete opts[k] });
            });
        }
        function tgl(i,n,p,b,grp){
            if(grp){ 
                document.querySelectorAll(".opt[data-grp='"+i+"_"+grp+"']").forEach(x=>{ 
                    if(x!==b){ x.classList.remove('active'); delete opts[i+'_'+x.getAttribute('data-val')]; } 
                }); 
            }
            let k=i+'_'+n; 
            if(opts[k]){ delete opts[k]; b.classList.remove('active'); } 
            else { opts[k]={n:n,p:p}; b.classList.add('active'); }
        }
    </script>
</head>
<body>
    <div class="header">🍜 晨食麵所</div>
    <div class="setup">
        {% if table_id %}<b>內用：{{table_id}}桌</b>
        {% else %}用餐：<button class="btn type-btn active" onclick="setT('外帶',this)">外帶</button><button class="btn type-btn" onclick="setT('內用',this)">內用</button>
        <div id="ts" style="display:none;margin-top:10px">桌號：{% for n in range(1,6) %}<button class="btn table-btn" onclick="setN('{{n}}',this)">{{n}}</button>{% endfor %}</div>{% endif %}
    </div>
    {% for cat,items in menu.items() %}
    <div class="title">{{cat}}</div>
    {% for item in items %}{% set iid = "id" ~ loop.index ~ cat[0] %}
    <div class="card">
        <div class="row"><div><strong>{{item.name}}</strong><br><span style="color:#e67e22">$ {{item.price}}</span></div><button class="add" onclick="buy('{{item.name}}',{{item.price}},'{{iid}}')">加入</button></div>
        <div class="grid">
            {% if item.can_add %}
            <div class="opt" data-item="{{iid}}" onclick="tgl('{{iid}}','加蛋',15,this)">+蛋($15)</div>
            <div class="opt" data-item="{{iid}}" onclick="tgl('{{iid}}','加里肌',25,this)">+里肌($25)</div>
            {% if item.no_v %}<div class="opt" data-item="{{iid}}" onclick="tgl('{{iid}}','不加菜',0,this)" style="color:red">✘不加菜</div>{% endif %}
            {% if item.can_spicy %}<div class="opt" data-item="{{iid}}" onclick="tgl('{{iid}}','加辣',0,this)" style="color:orange">🔥加辣</div>{% endif %}
            {% endif %}
            {% if item.is_jam %}
            <div class="opt" data-item="{{iid}}" onclick="tgl('{{iid}}','酥一點',0,this)">🍞酥一點</div>
            {% endif %}
            {% if item.opts %}{% for group in item.opts %}{% set gidx = loop.index %}
            {% for o in group %}<div class="opt" data-item="{{iid}}" data-grp="{{iid}}_{{gidx}}" data-val="{{o}}" onclick="tgl('{{iid}}','{{o}}',0,this,'{{gidx}}')">{{o}}</div>{% endfor %}
            {% endfor %}{% endif %}
        </div>
    </div>
    {% endfor %}{% endfor %}
    <div class="footer"><span>已點 <span id="cc">{{cart_len}}</span> 份 | $ <span id="ct">{{total}}</span></span><a href="/cart" style="background:#ffbe00;color:#000;padding:8px 15px;border-radius:20px;text-decoration:none;font-weight:bold">結帳</a></div>
</body>
</html>
"""

CART_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><style>body{font-family:sans-serif;padding:20px;background:#fdfaf0}</style></head>
<body><div style="max-width:500px;margin:auto"><h3>🛒 訂單確認</h3><p>用餐：{{loc}}</p>
{% for n,c in counts.items() %}<p>{{n}} <span style="color:red">x {{c}}</span></p>{% endfor %}<hr><h4>總計: ${{total}}</h4>
<form action="/clear" method="POST"><button type="submit" style="width:100%;background:#ffbe00;padding:15px;border:none;border-radius:10px;font-weight:bold;font-size:18px">送出訂單</button></form><br><a href="/" style="color:gray">回菜單</a></div></body></html>
"""

PRINT_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><style>body{text-align:center;padding:50px}</style><script>window.onload=function(){window.print();setTimeout(function(){location.href='/'},1000)}</script></head>
<body><h2>✅ 訂單已完成</h2><p>正在呼叫列印...</p></body></html>
"""

BOSS_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><style>body{font-family:sans-serif;padding:10px}.o{background:#fff;padding:15px;margin-bottom:10px;border-radius:10px;border:1px solid #ddd}</style>
<script>function del(id,e){if(confirm('完成訂單？')){fetch('/delete_order',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:"id="+id}).then(function(){e.closest('.o').style.display='none'})}}</script></head>
<body><div style="display:flex;justify-content:space-between"><h2>💰 總營收：${{total}}</h2><button onclick="location.href='/'">回菜單</button></div>
{% for h in logs %}<div class="o"><b>{{h.loc}}</b> ({{h.time}})<br><p>{{h.summary|safe}}</p><b>${{h.price}}</b><button onclick="del('{{h.id}}',this)" style="float:right;color:green">完成</button></div>{% endfor %}</body></html>
"""

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
