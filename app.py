from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
import os, secrets, requests, datetime
import pytz
from collections import Counter
import json

app = Flask(__name__)
app.secret_key = "morning_noodle_v37_full_menu"
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax')

# --- 後台密碼 ---
BOSS_PASSWORD = "8888" 

# ==========================================
# 🔗 [Google 試算表串聯設定]
# ==========================================
G_URL = "https://docs.google.com/forms/d/e/1FAIpQLSe5HJ_rQDNaSXNo6l38DYMFErzna8Rmqjp8X61cgPZ2d8QOqA/formResponse"
G_ENTRY_SUMMARY = "entry.303092604"  
G_ENTRY_PRICE = "entry.157627510"     
G_ENTRY_TIME = "entry.1541194223"       

def sync_to_google(summary, price, info, pay_method="現金"):
    clean_summary = summary.replace('<br>', ' | ')
    tw_tz = pytz.timezone('Asia/Taipei')
    now_tw = datetime.datetime.now(tw_tz)
    final_info = f"{now_tw.strftime('%m/%d %H:%M:%S')} ({info}-{pay_method})"
    payload = {G_ENTRY_SUMMARY: clean_summary, G_ENTRY_PRICE: str(price), G_ENTRY_TIME: final_info}
    try: requests.post(G_URL, data=payload, timeout=5)
    except: pass

# ==========================================
# 🍱 [完整菜單資料資料庫]
# ==========================================
DRINK_OPTS = ["選紅茶", "選冷泡茶", "換奶茶", "換鮮奶茶"]
DRINK_PRICE_MAP = {"換奶茶": 5, "換鮮奶茶": 15}
NOODLE_SUB = "配料：高麗菜、紅蘿蔔、肉絲、蒜碎、洋蔥、蔥花、玉米"

MENU_DATA = {
    "吃爽組合 (套餐)": [
        {"name": "薯條OR雞塊+飲品", "price": 60, "sub": "⚠️ 請選品項+飲品", "opts": [["選薯條", "選雞塊"], DRINK_OPTS], "price_map": DRINK_PRICE_MAP},
        {"name": "肉蛋吐司+紅茶", "price": 60},
        {"name": "熱狗(3支)+蛋+飲品", "price": 50, "opts": [DRINK_OPTS], "price_map": DRINK_PRICE_MAP},
        {"name": "草莓肉鬆吐司+飲品", "price": 50, "can_add": True, "opts": [DRINK_OPTS], "price_map": DRINK_PRICE_MAP},
        {"name": "巧克力薯餅吐司+飲品", "price": 50, "can_add": True, "opts": [DRINK_OPTS], "price_map": DRINK_PRICE_MAP}
    ],
    "蛋餅類": [
        {"name": "原味蛋餅", "price": 30, "can_add": True, "add_meat": True, "can_spicy": True}, 
        {"name": "蔥香蛋餅", "price": 35, "can_add": True, "add_meat": True, "can_spicy": True}, 
        {"name": "肉鬆蛋餅", "price": 40, "can_add": True, "add_meat": True, "can_spicy": True}, 
        {"name": "起司蛋餅", "price": 40, "can_add": True, "add_meat": True, "can_spicy": True},
        {"name": "蔬菜蛋餅", "price": 40, "can_add": True, "add_meat": True, "can_spicy": True},
        {"name": "火腿蛋餅", "price": 40, "can_add": True, "add_meat": True, "can_spicy": True},
        {"name": "香煎培根蛋餅", "price": 40, "can_add": True, "add_meat": True, "can_spicy": True},
        {"name": "熱狗蛋餅", "price": 40, "can_add": True, "add_meat": True, "can_spicy": True},
        {"name": "塔香蛋餅", "price": 40, "can_add": True, "add_meat": True, "can_spicy": True},
        {"name": "玉米蛋餅", "price": 40, "can_add": True, "add_meat": True, "can_spicy": True},
        {"name": "酥脆薯餅蛋餅", "price": 45, "can_add": True, "add_meat": True, "can_spicy": True},
        {"name": "特調鮪魚蛋餅", "price": 50, "can_add": True, "add_meat": True, "can_spicy": True},
        {"name": "里肌肉蛋餅", "price": 50, "can_add": True, "add_meat": True, "can_spicy": True},
        {"name": "辣菜脯里肌蛋餅", "price": 65, "can_add": True, "add_meat": True, "can_spicy": True}
    ],
    "泡麵系列 (2包)": [
        {"name": "招牌炒泡麵", "price": 70, "can_add": True, "add_meat": True, "can_spicy": True, "can_no_side": True, "sub": NOODLE_SUB}, 
        {"name": "起司魂炒泡麵", "price": 75, "can_add": True, "add_meat": True, "can_spicy": True, "can_no_side": True, "sub": NOODLE_SUB},
        {"name": "椒麻炒泡麵", "price": 75, "can_add": True, "add_meat": True, "can_spicy": True, "can_no_side": True, "sub": NOODLE_SUB},
        {"name": "菜脯辣炒泡麵", "price": 75, "can_add": True, "add_meat": True, "can_spicy": True, "can_no_side": True, "sub": NOODLE_SUB},
        {"name": "經典沙茶炒泡麵", "price": 75, "can_add": True, "add_meat": True, "can_spicy": True, "can_no_side": True, "sub": NOODLE_SUB}
    ],
    "炒麵系列 (200g)": [
        {"name": "蘑菇麵", "price": 55, "can_add": True, "add_meat": True, "can_spicy": True, "can_no_side": True, "no_meat_opt": True, "sub": "【無肉絲】附基本配料"},
        {"name": "黑胡椒麵", "price": 55, "can_add": True, "add_meat": True, "can_spicy": True, "can_no_side": True, "no_meat_opt": True, "sub": "【無肉絲】附基本配料"},
        {"name": "招牌爆香炒麵", "price": 70, "can_add": True, "add_meat": True, "can_spicy": True, "can_no_side": True, "sub": NOODLE_SUB}, 
        {"name": "起司魂炒麵", "price": 75, "can_add": True, "add_meat": True, "can_spicy": True, "can_no_side": True, "sub": NOODLE_SUB},
        {"name": "菜脯辣起司炒麵", "price": 75, "can_add": True, "add_meat": True, "can_spicy": True, "can_no_side": True, "sub": NOODLE_SUB},
        {"name": "經典沙茶炒麵", "price": 75, "can_add": True, "add_meat": True, "can_spicy": True, "can_no_side": True, "sub": NOODLE_SUB}
    ],
    "果醬吐司/厚片": [
        {"name": "巧克力吐司", "price": 25}, {"name": "巧克力厚片", "price": 30},
        {"name": "草莓吐司", "price": 25}, {"name": "草莓厚片", "price": 30},
        {"name": "花生吐司", "price": 25}, {"name": "花生厚片", "price": 30},
        {"name": "奶酥吐司", "price": 25}, {"name": "奶酥厚片", "price": 30}
    ],
    "烤吐司系列": [
        {"name": "煎蛋吐司", "price": 35, "can_add": True, "add_meat": True, "can_spicy": True, "can_crispy": True, "sub": "⚠️預設無生菜、番茄"},
        {"name": "火腿吐司", "price": 40, "can_add": True, "add_meat": True, "can_spicy": True, "can_crispy": True, "can_no_veg": True, "can_no_side": True, "sub": "✅含生菜、番茄"},
        {"name": "培根吐司", "price": 40, "can_add": True, "add_meat": True, "can_spicy": True, "can_crispy": True, "can_no_veg": True, "can_no_side": True, "sub": "✅含生菜、番茄"},
        {"name": "麥香雞吐司", "price": 40, "can_add": True, "add_meat": True, "can_spicy": True, "can_crispy": True, "can_no_veg": True, "can_no_side": True, "sub": "✅含生菜、番茄"},
        {"name": "鮪魚吐司", "price": 50, "can_add": True, "add_meat": True, "can_spicy": True, "can_crispy": True, "can_no_veg": True, "can_no_side": True, "sub": "✅含生菜、番茄"},
        {"name": "薯餅吐司", "price": 40, "can_add": True, "add_meat": True, "can_spicy": True, "can_crispy": True, "can_no_veg": True, "can_no_side": True, "sub": "✅含生菜、番茄"},
        {"name": "里肌吐司", "price": 55, "can_add": True, "add_meat": True, "can_spicy": True, "can_crispy": True, "can_no_veg": True, "can_no_side": True, "sub": "✅含生菜、番茄"}, 
        {"name": "卡啦雞腿吐司", "price": 60, "can_add": True, "add_meat": True, "can_spicy": True, "can_crispy": True, "can_no_veg": True, "can_no_side": True, "sub": "✅含生菜、番茄"}
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
    return render_template_string(INDEX_HTML, menu=MENU_DATA, cart_len=len(cart), total=sum(i['price'] for i in cart))

@app.route("/update_info", methods=["POST"])
def update_info():
    t, table = request.form.get("type"), request.form.get("table", "")
    session['info'] = {"type": t, "table": table}
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
    session['cart'] = [i for i in session.get('cart', []) if i['id'] != target_id]
    return jsonify({"status": "ok"})

@app.route("/cart")
def view_cart():
    cart = session.get('cart', [])
    info = session.get('info', {"type": "外帶", "table": ""})
    t = sum(i['price'] for i in cart)
    loc = f"{info['type']}" + (f"-{info['table']}桌" if info['table'] else "")
    return render_template_string(CART_HTML, cart=cart, total=t, loc=loc)

@app.route("/clear", methods=["POST"])
def clear():
    global total_income
    cart = session.get('cart', [])
    info = session.get('info', {"type": "外帶", "table": ""})
    t = sum(i['price'] for i in cart)
    if t > 0:
        loc = f"{info['type']}" + (f"-{info['table']}桌" if info['table'] else "")
        summary_html = "<br>".join([f"{n} x{c}" for n,c in Counter([i['name'] for i in cart]).items()])
        total_income += t
        history.append({"id": secrets.token_hex(4), "loc": loc, "price": t, "summary": summary_html, "time": datetime.datetime.now(pytz.timezone('Asia/Taipei')), "done": False, "pay": "未選"})
        session['cart'] = [] 
        return render_template_string(SUCCESS_HTML)
    return redirect("/")

@app.route("/boss")
def boss():
    if request.args.get("pw") != BOSS_PASSWORD: return "Error", 403
    return render_template_string(BOSS_HTML, total=total_income, logs=history[::-1])

@app.route("/finish_order", methods=["POST"])
def finish_order():
    oid, method = request.form.get("id"), request.form.get("method", "現金")
    target = next((h for h in history if h['id'] == oid), None)
    if target:
        sync_to_google(target['summary'], target['price'], target['loc'], method)
        target['done'], target['pay'] = True, method
        return jsonify({"status": "ok"})
    return jsonify({"status": "error"}), 404

# --- [ INDEX_HTML ] ---
INDEX_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,user-scalable=no">
<style>
    body { font-family: sans-serif; background: #fdfaf0; margin: 0; padding: 0 10px 100px; }
    .header { background: #ffbe00; color: #fff; padding: 15px; text-align: center; border-radius: 0 0 15px 15px; font-weight: bold; font-size: 20px; user-select: none; transition: 0.2s; cursor: pointer; }
    .header:active { transform: scale(0.95); opacity: 0.8; }
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
    .opt.no-side { border-color: #e74c3c; color: #e74c3c; font-weight: bold; }
    .opt.no-side.active { background: #e74c3c; color: #fff; }
    .footer { position: fixed; bottom: 0; left: 0; right: 0; background: #333; color: #fff; padding: 15px; display: flex; justify-content: space-between; align-items: center; }
</style>
<script>
    let opts={}; let curT="{{session.info.table}}"; let curType="{{session.info.type}}";
    let timer;
    function startPress(){ timer = setTimeout(() => { window.location.href='/boss?pw=8888'; }, 3000); }
    function endPress(){ clearTimeout(timer); }

    function setT(t,b){curType=t;if(t==='外帶')curT='';fetch('/update_info',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:"type="+t+"&table="+curT});document.querySelectorAll('.type-btn').forEach(x=>x.classList.remove('active'));b.classList.add('active');document.getElementById('ts').style.display=(t==='內用')?'block':'none'}
    function setN(n,b){curT=n;fetch('/update_info',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:"type=內用&table="+n});document.querySelectorAll('.table-btn').forEach(x=>x.classList.remove('active'));b.classList.add('active')}
    
    function buy(btn){
        let n=btn.getAttribute('data-name'), p=parseInt(btn.getAttribute('data-price')), i=btn.getAttribute('data-id'), req=parseInt(btn.getAttribute('data-req')||'0'), pMap=JSON.parse(btn.getAttribute('data-pmap')||'{}');
        if(curType==='內用'&&!curT){alert("內用請先選桌號");return;}
        let fn=n, fp=p, sel=0;
        Object.keys(opts).forEach(k=>{ if(k.startsWith(i+'_')){ let o=opts[k]; fn+='+'+o.n; fp+=o.p; if(pMap[o.n])fp+=pMap[o.n]; if(o.n.includes('選')||o.n.includes('換'))sel++; } });
        if(req>0){ if(n.includes("薯條OR雞塊")&&sel<2){alert("請選品項與飲品");return;} if(!n.includes("薯條OR雞塊")&&sel<1){alert("請選飲品");return;} }
        fetch('/add',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:"name="+encodeURIComponent(fn)+"&price="+fp})
        .then(r=>r.json()).then(d=>{
            document.getElementById('cc').innerText=d.count; document.getElementById('ct').innerText=d.total;
            document.querySelectorAll(".opt[data-item='"+i+"']").forEach(x=>x.classList.remove('active'));
            Object.keys(opts).forEach(k=>{if(k.startsWith(i+'_'))delete opts[k]});
        });
    }
    function tgl(i,n,p,b,grp){
        if(grp){document.querySelectorAll(".opt[data-grp='"+i+"_"+grp+"']").forEach(x=>{if(x!==b){x.classList.remove('active');delete opts[i+'_'+x.getAttribute('data-val')]}})}
        let k=i+'_'+n; if(opts[k]){delete opts[k];b.classList.remove('active')}else{opts[k]={n:n,p:p};b.classList.add('active')}
    }
</script></head>
<body>
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
            {% set iid = cat[0] ~ loop.index0 %}
            <div class="card">
                <div class="row">
                    <div style="flex:1"><strong>{{item.name}}</strong>{% if item.sub %}<div style="font-size:12px;color:gray">{{item.sub}}</div>{% endif %}<div style="color:#e67e22;font-weight:bold">${{item.price}}</div></div>
                    <button class="add" data-id="{{iid}}" data-name="{{item.name}}" data-price="{{item.price}}" data-req="{{1 if item.opts else 0}}" data-pmap='{{item.price_map|tojson|safe if item.price_map else "{}"}}' onclick="buy(this)">加入</button>
                </div>
                <div class="grid">
                    {% if item.can_add %}<div class="opt" data-item="{{iid}}" onclick="tgl('{{iid}}','加蛋',15,this)">+蛋 15</div><div class="opt" data-item="{{iid}}" onclick="tgl('{{iid}}','加起司',15,this)">+起司 15</div>{% endif %}
                    {% if item.add_meat %}<div class="opt" data-item="{{iid}}" onclick="tgl('{{iid}}','加里肌',25,this)">+里肌 25</div>{% endif %}
                    {% if item.can_spicy %}<div class="opt" data-item="{{iid}}" onclick="tgl('{{iid}}','特製辣',0,this)">特製辣</div>{% endif %}
                    {% if item.can_crispy %}<div class="opt" data-item="{{iid}}" onclick="tgl('{{iid}}','酥一點',0,this)">酥一點</div>{% endif %}
                    {% if item.can_no_veg %}<div class="opt" data-item="{{iid}}" onclick="tgl('{{iid}}','不加生菜',0,this)">不加生菜</div><div class="opt" data-item="{{iid}}" onclick="tgl('{{iid}}','不加番茄',0,this)">不加番茄</div>{% endif %}
                    
                    {% if item.can_no_side %}
                        <div class="opt no-side" data-item="{{iid}}" onclick="tgl('{{iid}}','配料都不要',0,this)">配料都不要</div>
                        {% if '系列' in cat %} {# 泡麵/炒麵專用配料 #}
                            <div class="opt" data-item="{{iid}}" onclick="tgl('{{iid}}','不加高麗菜',0,this)">不加高麗菜</div>
                            <div class="opt" data-item="{{iid}}" onclick="tgl('{{iid}}','不加紅蘿蔔',0,this)">不加紅蘿蔔</div>
                            {% if not item.no_meat_opt %}<div class="opt" data-item="{{iid}}" onclick="tgl('{{iid}}','不加肉絲',0,this)">不加肉絲</div>{% endif %}
                            <div class="opt" data-item="{{iid}}" onclick="tgl('{{iid}}','不加蒜碎',0,this)">不加蒜碎</div>
                            <div class="opt" data-item="{{iid}}" onclick="tgl('{{iid}}','不加洋蔥',0,this)">不加洋蔥</div>
                            <div class="opt" data-item="{{iid}}" onclick="tgl('{{iid}}','不加蔥花',0,this)">不加蔥花</div>
                            <div class="opt" data-item="{{iid}}" onclick="tgl('{{iid}}','不加玉米',0,this)">不加玉米</div>
                        {% endif %}
                    {% endif %}

                    {% if item.opts %}{% for grp in item.opts %}{% set gidx=loop.index %}{% for o in grp %}
                        {% set ex = item.price_map.get(o, 0) if item.price_map else 0 %}
                        <div class="opt" data-item="{{iid}}" data-grp="{{iid}}_{{gidx}}" data-val="{{o}}" onclick="tgl('{{iid}}','{{o}}',0,this,'{{gidx}}')">{{o}}{% if ex>0 %}+{{ex}}{% endif %}</div>
                    {% endfor %}{% endfor %}{% endif %}
                </div>
            </div>
        {% endfor %}
    {% endfor %}
    <div class="footer"><span>已點 <span id="cc">{{cart_len}}</span> 項 | $<span id="ct">{{total}}</span></span><a href="/cart" style="background:#ffbe00;color:#000;padding:8px 20px;border-radius:20px;text-decoration:none;font-weight:bold;">去結帳</a></div>
</body></html>
"""

CART_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><style>body{font-family:sans-serif;padding:20px;background:#fdfaf0;}.item{background:#fff;padding:15px;margin-bottom:10px;border-radius:10px;display:flex;justify-content:space-between;}</style>
<script>function rm(id){fetch('/del_item',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:"id="+id}).then(()=>location.reload())}</script></head>
<body><h3>🛒 結帳明細 ({{loc}})</h3>
{% for i in cart %}<div class="item"><div><b>{{i.name}}</b><br>${{i.price}}</div><button onclick="rm('{{i.id}}')">刪除</button></div>{% endfor %}
<hr><h4>總計: ${{total}}</h4>
<form action="/clear" method="POST"><button type="submit" style="width:100%;background:#ffbe00;padding:15px;border:none;border-radius:10px;font-weight:bold;">確認送出訂單</button></form>
<br><a href="/" style="display:block;text-align:center;color:gray;text-decoration:none;">返回繼續加點</a></body></html>
"""

BOSS_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><style>body{font-family:sans-serif;padding:15px;}.o{background:#fff;padding:15px;margin-bottom:15px;border-radius:10px;box-shadow:0 2px 5px rgba(0,0,0,0.1);border-left:8px solid #ffbe00;}</style>
<script>function finish(id, m){fetch('/finish_order',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:"id="+id+"&method="+m}).then(()=>location.reload())}</script></head>
<body><h2>總額: ${{total}}</h2><button onclick="window.location.href='/'">回首頁</button>
{% for h in logs %}<div class="o"><b>{{h.loc}}</b> ({{h.time.strftime('%H:%M:%S')}})<p>{{h.summary|safe}}</p><b>${{h.price}}</b>
{% if not h.done %}<button onclick="finish('{{h.id}}','現金')">現金</button><button onclick="finish('{{h.id}}','LINE Pay')">LINE Pay</button>{% else %} [{{h.pay}}已付]{% endif %}</div>{% endfor %}
</body></html>
"""

SUCCESS_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><script>setTimeout(()=>location.href='/', 3000)</script></head>
<body style="text-align:center;padding-top:100px;"><h1>✅ 訂單已送出</h1><p>請至櫃檯結帳</p></body></html>
"""

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
