from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
import os, secrets, requests, datetime
import pytz
from collections import Counter

app = Flask(__name__)
app.secret_key = "morning_noodle_v93_custom_no_veg"
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax')

# --- 核心參數 ---
BOSS_PASSWORD = "8888" 
G_URL = "https://docs.google.com/forms/d/e/1FAIpQLSe5HJ_rQDNaSXNo6l38DYMFErzna8Rmqjp8X61cgPZ2d8QOqA/formResponse"
G_ENTRIES = {"summary": "entry.303092604", "price": "entry.157627510", "time": "entry.1541194223"}

# 菜單變數
DRINK_OPTS = ["選紅茶", "選冷泡茶", "換奶茶(+5)", "換鮮奶茶(+15)"]
DRINK_PRICE_MAP = {"換奶茶(+5)": 5, "換鮮奶茶(+15)": 15}
NOODLE_SUB = "配料：高麗菜、紅蘿蔔、肉絲、蒜碎、洋蔥、蔥花、玉米"
TOAST_SUB = "✅含生菜、番茄、美乃滋"

# 定義麵類專用的排除選項
NO_VEG_OPTS = ["不要高麗菜", "不要紅蘿蔔", "不要肉絲", "不要蒜碎", "不要洋蔥", "不要蔥花", "不要玉米"]

MENU_DATA = {
    "吃爽組合 (套餐)": [
        {"name": "薯條OR雞塊+飲品", "price": 60, "sub": "⚠️ 請選品項+飲品", "opts": [["選薯條", "選雞塊"], DRINK_OPTS], "price_map": DRINK_PRICE_MAP},
        {"name": "肉蛋吐司+紅茶", "price": 60, "can_no_crust": True},
        {"name": "熱狗(3支)+蛋+飲品", "price": 50, "opts": [DRINK_OPTS], "price_map": DRINK_PRICE_MAP},
        {"name": "草莓肉鬆吐司+飲品", "price": 50, "can_add": True, "can_no_crust": True, "opts": [DRINK_OPTS], "price_map": DRINK_PRICE_MAP},
        {"name": "巧克力薯餅吐司+飲品", "price": 50, "can_add": True, "can_no_crust": True, "opts": [DRINK_OPTS], "price_map": DRINK_PRICE_MAP}
    ],
    "蛋餅類": [
        {"name": "原味蛋餅", "price": 30, "can_add": True, "add_meat": True}, 
        {"name": "蔥香蛋餅", "price": 35, "can_add": True, "add_meat": True}, 
        {"name": "肉鬆蛋餅", "price": 40, "can_add": True, "add_meat": True}, 
        {"name": "起司蛋餅", "price": 40, "can_add": True, "add_meat": True},
        {"name": "蔬菜蛋餅", "price": 40, "can_add": True, "add_meat": True},
        {"name": "火腿蛋餅", "price": 40, "can_add": True, "add_meat": True},
        {"name": "香煎培根蛋餅", "price": 40, "can_add": True, "add_meat": True},
        {"name": "熱狗蛋餅", "price": 40, "can_add": True, "add_meat": True},
        {"name": "塔香蛋餅", "price": 40, "can_add": True, "add_meat": True},
        {"name": "玉米蛋餅", "price": 40, "can_add": True, "add_meat": True},
        {"name": "酥脆薯餅蛋餅", "price": 45, "can_add": True, "add_meat": True},
        {"name": "特調鮪魚蛋餅", "price": 50, "can_add": True, "add_meat": True},
        {"name": "里肌肉蛋餅", "price": 50, "can_add": True, "add_meat": True},
        {"name": "辣菜脯里肌蛋餅", "price": 65, "can_add": True, "add_meat": True}
    ],
    "泡麵系列 (2包)": [
        {"name": "招牌炒泡麵", "price": 70, "can_add": True, "add_meat": True, "can_spicy": True, "has_no_veg": True, "sub": NOODLE_SUB}, 
        {"name": "起司魂炒泡麵", "price": 75, "can_add": True, "add_meat": True, "can_spicy": True, "has_no_veg": True, "sub": NOODLE_SUB},
        {"name": "椒麻炒泡麵", "price": 75, "can_add": True, "add_meat": True, "can_spicy": True, "has_no_veg": True, "sub": NOODLE_SUB},
        {"name": "菜脯辣炒泡麵", "price": 75, "can_add": True, "add_meat": True, "can_spicy": True, "has_no_veg": True, "sub": NOODLE_SUB},
        {"name": "經典沙茶炒泡麵", "price": 75, "can_add": True, "add_meat": True, "can_spicy": True, "has_no_veg": True, "sub": NOODLE_SUB}
    ],
    "炒麵系列 (200g)": [
        {"name": "蘑菇麵", "price": 55, "can_add": True, "add_meat": True, "can_spicy": True, "has_no_veg": True, "sub": "【無肉絲】附基本配料"},
        {"name": "黑胡椒麵", "price": 55, "can_add": True, "add_meat": True, "can_spicy": True, "has_no_veg": True, "sub": "【無肉絲】附基本配料"},
        {"name": "招牌爆香炒麵", "price": 70, "can_add": True, "add_meat": True, "can_spicy": True, "has_no_veg": True, "sub": NOODLE_SUB}, 
        {"name": "起司魂炒麵", "price": 75, "can_add": True, "add_meat": True, "can_spicy": True, "has_no_veg": True, "sub": NOODLE_SUB},
        {"name": "菜脯辣起司炒麵", "price": 75, "can_add": True, "add_meat": True, "can_spicy": True, "has_no_veg": True, "sub": NOODLE_SUB},
        {"name": "經典沙茶炒麵", "price": 75, "can_add": True, "add_meat": True, "can_spicy": True, "has_no_veg": True, "sub": NOODLE_SUB}
    ],
    "果醬吐司/厚片": [
        {"name": "巧克力吐司", "price": 25, "can_crispy": True, "can_no_crust": True}, {"name": "巧克力厚片", "price": 30, "can_crispy": True, "can_no_crust": True},
        {"name": "草莓吐司", "price": 25, "can_crispy": True, "can_no_crust": True}, {"name": "草莓厚片", "price": 30, "can_crispy": True, "can_no_crust": True},
        {"name": "花生吐司", "price": 25, "can_crispy": True, "can_no_crust": True}, {"name": "花生厚片", "price": 30, "can_crispy": True, "can_no_crust": True},
        {"name": "奶酥吐司", "price": 25, "can_crispy": True, "can_no_crust": True}, {"name": "奶酥厚片", "price": 30, "can_crispy": True, "can_no_crust": True}
    ],
    "烤吐司系列": [
        {"name": "煎蛋吐司", "price": 35, "can_add": True, "add_meat": True, "can_no_veg": True, "can_crispy": True, "can_no_crust": True, "sub": "⚠️預設無生菜、番茄"},
        {"name": "火腿吐司", "price": 40, "can_add": True, "add_meat": True, "can_no_veg": True, "can_crispy": True, "can_no_crust": True, "sub": TOAST_SUB},
        {"name": "培根吐司", "price": 40, "can_add": True, "add_meat": True, "can_no_veg": True, "can_crispy": True, "can_no_crust": True, "sub": TOAST_SUB},
        {"name": "麥香雞吐司", "price": 40, "can_add": True, "add_meat": True, "can_no_veg": True, "can_crispy": True, "can_no_crust": True, "sub": TOAST_SUB},
        {"name": "鮪魚吐司", "price": 50, "can_add": True, "add_meat": True, "can_no_veg": True, "can_crispy": True, "can_no_crust": True, "sub": TOAST_SUB},
        {"name": "薯餅吐司", "price": 40, "can_add": True, "add_meat": True, "can_no_veg": True, "can_crispy": True, "can_no_crust": True, "sub": TOAST_SUB},
        {"name": "里肌吐司", "price": 55, "can_add": True, "add_meat": True, "can_no_veg": True, "can_crispy": True, "can_no_crust": True, "sub": TOAST_SUB}, 
        {"name": "卡啦雞腿吐司", "price": 60, "can_add": True, "add_meat": True, "can_no_veg": True, "can_crispy": True, "can_no_crust": True, "sub": TOAST_SUB}
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
order_counter = 1 

@app.before_request
def ensure_session():
    if 'cart' not in session: session['cart'] = []
    if 'info' not in session: session['info'] = {"type": "外帶", "table": ""}

@app.route("/")
def index():
    cart = session.get('cart', [])
    return render_template_string(INDEX_HTML, menu=MENU_DATA, no_veg_list=NO_VEG_OPTS, cart_len=len(cart), total=sum(i['price'] for i in cart))

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

@app.route("/clear", methods=["POST"])
def clear():
    global order_counter
    cart = session.get('cart', [])
    if not cart: return redirect("/")
    
    info = session.get('info', {"type": "外帶", "table": ""})
    loc = f"{info['type']}" + (f"-{info['table']}桌" if info['table'] else "")
    summary = "<br>".join([f"{n} x{c}" for n,c in Counter([i['name'] for i in cart]).items()])
    
    my_no = order_counter
    history.append({
        "no": my_no, "id": secrets.token_hex(4), "loc": loc, "type": info['type'], 
        "price": sum(i['price'] for i in cart), "summary": summary, 
        "time": datetime.datetime.now(pytz.timezone('Asia/Taipei')), "done": False, "pay": "未選"
    })
    order_counter += 1
    session['cart'] = [] 
    return render_template_string(SUCCESS_HTML, order_no=my_no)

@app.route("/boss")
def boss():
    if not session.get('is_boss') and request.args.get("pw") == BOSS_PASSWORD: session['is_boss'] = True
    if not session.get('is_boss'): return "<h3>權限不足</h3>", 403
    done_orders = [h for h in history if h['done']]
    stats = {"money": sum(h['price'] for h in done_orders), "total": len(done_orders)}
    return render_template_string(BOSS_HTML, stats=stats, logs=history[::-1])

@app.route("/finish_order", methods=["POST"])
def finish_order():
    if not session.get('is_boss'): return jsonify({"status": "forbidden"}), 403
    oid, method = request.form.get("id"), request.form.get("method")
    target = next((h for h in history if h['id'] == oid), None)
    if target:
        if method == "RESET": target['done'], target['pay'] = False, "未選"
        else: target['done'], target['pay'] = True, method
        return jsonify({"status": "ok"})
    return jsonify({"status": "error"}), 404

# --- 介面設計 ---

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
    .grid { margin-top: 12px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; border-top: 1px dashed #eee; padding-top: 12px; }
    .opt { background: #fcfcfc; border: 1.5px solid #eee; padding: 8px 2px; border-radius: 8px; font-size: 11px; text-align: center; cursor: pointer; color:#555; }
    .opt.active { background: #5d4037; color: #fff; border-color: #5d4037; }
    .opt.no-veg { color: #e74c3c; border-color: #fbd9d6; }
    .opt.no-veg.active { background: #e74c3c; color: #fff; }
    .footer { position: fixed; bottom: 0; left: 0; right: 0; background: #333; color: #fff; padding: 15px; display: flex; justify-content: space-between; align-items: center; z-index: 100; }
</style>
<script>
    let opts={}; let curT="{{session.info.table}}"; let curType="{{session.info.type}}";
    let pressTimer;
    function startPress(){ pressTimer = window.setTimeout(() => { let p=prompt("管理密碼"); if(p) window.location.href='/boss?pw='+p; }, 3000); }
    function endPress(){ window.clearTimeout(pressTimer); }
    function setT(t,b){curType=t;if(t==='外帶')curT='';fetch('/update_info',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:"type="+t+"&table="+curT});document.querySelectorAll('.type-btn').forEach(x=>x.classList.remove('active'));b.classList.add('active');document.getElementById('ts').style.display=(t==='內用')?'block':'none'}
    function setN(n,b){curT=n;fetch('/update_info',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:"type=內用&table="+n});document.querySelectorAll('.table-btn').forEach(x=>x.classList.remove('active'));b.classList.add('active')}
    function buy(btn){
        let i=btn.dataset.id, n=btn.dataset.name, p=parseInt(btn.dataset.price);
        if(curType==='內用'&&!curT){alert("請選桌號");return;}
        let fn=n, fp=p, pMap=JSON.parse(btn.dataset.pmap||'{}');
        Object.keys(opts).forEach(k=>{ if(k.startsWith(i+'_')){ fn+='+'+opts[k].n; fp+=opts[k].p; if(pMap[opts[k].n])fp+=pMap[opts[k].n]; } });
        fetch('/add',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:"name="+encodeURIComponent(fn)+"&price="+fp})
        .then(r=>r.json()).then(d=>{ document.getElementById('cc').innerText=d.count; document.getElementById('ct').innerText=d.total; });
    }
    function tgl(i,n,p,b,grp){
        if(grp){document.querySelectorAll(".opt[data-grp='"+i+"_"+grp+"']").forEach(x=>{if(x!==b){x.classList.remove('active');delete opts[i+'_'+x.dataset.val]}})}
        let k=i+'_'+n; if(opts[k]){delete opts[k];b.classList.remove('active')}else{opts[k]={n:n,p:p};b.classList.add('active')}
    }
</script></head>
<body>
    <div class="header" onmousedown="startPress()" ontouchstart="startPress()" onmouseup="endPress()" ontouchend="endPress()">🍜 晨食麵所</div>
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
                <div class="row"><div style="flex:1"><strong>{{item.name}}</strong><div style="font-size:11px;color:gray">{{item.sub or ""}}</div><div style="color:#e67e22;font-weight:bold">${{item.price}}</div></div>
                <button class="add" data-id="{{iid}}" data-name="{{item.name}}" data-price="{{item.price}}" data-pmap='{{item.price_map|tojson|safe if item.price_map else "{}"}}' onclick="buy(this)">加入</button></div>
                <div class="grid">
                    {% if item.can_add %}<div class="opt" onclick="tgl('{{iid}}','加蛋',15,this)">+蛋 15</div><div class="opt" onclick="tgl('{{iid}}','加起司',15,this)">+起司 15</div>{% endif %}
                    {% if item.add_meat %}<div class="opt" onclick="tgl('{{iid}}','加里肌',25,this)">+里肌 25</div>{% endif %}
                    {% if item.can_spicy %}<div class="opt" onclick="tgl('{{iid}}','特製辣',0,this)">🌶️ 特製辣</div>{% endif %}
                    {% if item.can_no_crust %}<div class="opt" onclick="tgl('{{iid}}','去邊',0,this)">🍞 去邊</div>{% endif %}
                    {% if item.has_no_veg %}{% for v in no_veg_list %}<div class="opt no-veg" onclick="tgl('{{iid}}','{{v}}',0,this)">{{v}}</div>{% endfor %}{% endif %}
                    {% if item.opts %}{% for grp in item.opts %}{% set gidx=loop.index %}{% for o in grp %}<div class="opt" data-grp="{{iid}}_{{gidx}}" data-val="{{o}}" onclick="tgl('{{iid}}','{{o}}',0,this,'{{gidx}}')">{{o}}</div>{% endfor %}{% endfor %}{% endif %}
                </div>
            </div>
        {% endfor %}
    {% endfor %}
    <div class="footer"><span>已點 <span id="cc">{{cart_len}}</span> 項 | $<span id="ct">{{total}}</span></span><a href="/cart" style="background:#ffbe00;color:#000;padding:10px 20px;border-radius:20px;text-decoration:none;font-weight:bold;">去結帳</a></div>
</body></html>
"""

BOSS_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<style>
    body{font-family:sans-serif;background:#eee;padding:15px;}
    .o{background:#fff;padding:15px;margin-bottom:10px;border-radius:8px;border-left:8px solid #ffbe00;}
    .btn{padding:10px 15px;border:none;border-radius:5px;font-weight:bold;cursor:pointer;margin-top:10px;}
    .cash{background:#2ecc71;color:#fff;}
    @media print { 
        body * { visibility: hidden; } 
        #print-area, #print-area * { visibility: visible; } 
        #print-area { position: absolute; left: 0; top: 0; width: 54mm; font-size: 14px; } 
    }
</style>
<script>
    function finish(no, id, m, loc, time, summary, price) {
        let p = `<div id="print-area"><h1 style="font-size:32px;margin:0;">#${no}</h1><p>${time}</p><b>${loc}</b><hr>${summary}<hr><b>總計: $${price}</b></div>`;
        let div = document.createElement('div'); div.innerHTML = p; document.body.appendChild(div);
        window.print();
        document.body.removeChild(div);
        fetch('/finish_order',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:"id="+id+"&method="+m}).then(()=>location.reload());
    }
</script></head>
<body>
    <div class="no-print"><a href="/">⬅️ 返回首頁</a> | 營收: ${{stats.money}} ({{stats.total}}單)</div>
    {% for h in logs %}<div class="o">
        <div style="display:flex;justify-content:space-between"><b>#{{h.no}}</b><span>{{h.time.strftime('%H:%M')}}</span></div>
        <b>{{h.loc}}</b><br>{{h.summary|safe}}<br><b style="color:orange">${{h.price}}</b>
        <div class="no-print">{% if not h.done %}<button class="btn cash" onclick="finish('{{h.no}}','{{h.id}}','現金','{{h.loc}}','{{h.time.strftime('%m/%d %H:%M')}}','{{h.summary}}','{{h.price}}')">完成/印單</button>{% else %}✅ 已完成{% endif %}</div>
    </div>{% endfor %}
</body></html>
"""

# (其餘 SUCCESS_HTML 與 SUCCESS 邏輯相同，僅微調文字)
SUCCESS_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><script>setTimeout(()=>location.href='/', 8000)</script></head>
<body style="text-align:center;padding-top:50px;font-family:sans-serif;background:#fdfaf0;">
    <div style="background:#fff;margin:20px;padding:30px;border-radius:20px;box-shadow:0 4px 10px rgba(0,0,0,0.1);">
        <h2 style="color:#2ecc71;">✅ 訂單已送出</h2>
        <p>您的取餐編號</p>
        <h1 style="font-size:80px;margin:10px 0;">#{{order_no}}</h1>
        <p style="color:red;font-weight:bold;">請記住編號並至櫃檯結帳</p>
    </div>
</body></html>
"""

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
