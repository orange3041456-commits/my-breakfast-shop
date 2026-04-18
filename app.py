from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
import os, secrets, requests
from collections import Counter
from datetime import datetime

app = Flask(__name__)
app.secret_key = "morning_noodle_pro_v2_boss_mode"
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
# 🍱 [完整菜單資料]
# ==========================================
NOODLE_SUB = "配料：高麗菜、紅蘿蔔、肉絲、蒜碎、洋蔥、蔥花、玉米"

MENU_DATA = {
    "吃爽組合 (套餐)": [
        {"name": "薯條OR雞塊+飲品", "price": 60, "sub": "薯條/雞塊 二選一", "opts": [["選薯條", "選雞塊"], ["選紅茶", "選冷泡茶"]]},
        {"name": "肉蛋吐司+紅茶", "price": 60},
        {"name": "熱狗(3支)+蛋+飲品", "price": 50, "opts": [["選紅茶", "選冷泡茶"]]},
        {"name": "草莓肉鬆吐司+飲品", "price": 50, "opts": [["選紅茶", "選冷泡茶"]]},
        {"name": "巧克力薯餅吐司+飲品", "price": 50, "opts": [["選紅茶", "選冷泡茶"]]}
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
        {"name": "招牌炒泡麵", "price": 70, "can_add": True, "add_meat": True, "can_spicy": True, "sub": NOODLE_SUB}, 
        {"name": "起司魂炒泡麵", "price": 75, "can_add": True, "add_meat": True, "can_spicy": True, "sub": NOODLE_SUB},
        {"name": "椒麻炒泡麵", "price": 75, "can_add": True, "add_meat": True, "can_spicy": True, "sub": NOODLE_SUB},
        {"name": "菜脯辣炒泡麵", "price": 75, "can_add": True, "add_meat": True, "can_spicy": True, "sub": NOODLE_SUB},
        {"name": "經典沙茶炒泡麵", "price": 75, "can_add": True, "add_meat": True, "can_spicy": True, "sub": NOODLE_SUB}
    ],
    "炒麵系列 (200g)": [
        {"name": "蘑菇麵", "price": 55, "can_add": True, "add_meat": True, "can_spicy": True, "sub": "【無肉絲】附基本配料"},
        {"name": "黑胡椒麵", "price": 55, "can_add": True, "add_meat": True, "can_spicy": True, "sub": "【無肉絲】附基本配料"},
        {"name": "招牌爆香炒麵", "price": 70, "can_add": True, "add_meat": True, "can_spicy": True, "sub": NOODLE_SUB}, 
        {"name": "起司魂炒麵", "price": 75, "can_add": True, "add_meat": True, "can_spicy": True, "sub": NOODLE_SUB},
        {"name": "菜脯辣起司炒麵", "price": 75, "can_add": True, "add_meat": True, "can_spicy": True, "sub": NOODLE_SUB},
        {"name": "經典沙茶炒麵", "price": 75, "can_add": True, "add_meat": True, "can_spicy": True, "sub": NOODLE_SUB}
    ],
    "果醬吐司/厚片": [
        {"name": "巧克力吐司", "price": 25, "is_jam": True}, {"name": "巧克力厚片", "price": 30, "is_jam": True},
        {"name": "草莓吐司", "price": 25, "is_jam": True}, {"name": "草莓厚片", "price": 30, "is_jam": True},
        {"name": "花生吐司", "price": 25, "is_jam": True}, {"name": "花生厚片", "price": 30, "is_jam": True},
        {"name": "奶酥吐司", "price": 25, "is_jam": True}, {"name": "奶酥厚片", "price": 30, "is_jam": True}
    ],
    "烤吐司系列": [
        {"name": "煎蛋吐司", "price": 35, "can_add": True, "add_meat": True, "is_toast": True, "sub": "⚠️預設無生菜、番茄"},
        {"name": "火腿吐司", "price": 40, "can_add": True, "add_meat": True, "is_toast": True, "sub": "✅含生菜、番茄"},
        {"name": "培根吐司", "price": 40, "can_add": True, "add_meat": True, "is_toast": True, "sub": "✅含生菜、番茄"},
        {"name": "麥香雞吐司", "price": 40, "can_add": True, "add_meat": True, "is_toast": True, "sub": "✅含生菜、番茄"},
        {"name": "鮪魚吐司", "price": 50, "can_add": True, "add_meat": True, "is_toast": True, "sub": "✅含生菜、番茄"},
        {"name": "薯餅吐司", "price": 40, "can_add": True, "add_meat": True, "is_toast": True, "sub": "✅含生菜、番茄"},
        {"name": "里肌吐司", "price": 55, "can_add": True, "add_meat": True, "is_toast": True, "sub": "✅含生菜、番茄"}, 
        {"name": "卡啦雞腿吐司", "price": 60, "can_add": True, "add_meat": True, "is_toast": True, "sub": "✅含生菜、番茄"}
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
total_income = 0

@app.before_request
def ensure_session():
    if 'cart' not in session: session['cart'] = []
    if 'info' not in session: session['info'] = {"type": "外帶", "table": ""}

@app.route("/")
def index():
    cart = session.get('cart', [])
    tid = request.args.get('table')
    is_boss = request.args.get('mode') == 'boss'
    if tid: session['info'] = {"type": "內用", "table": tid}
    return render_template_string(INDEX_HTML, menu=MENU_DATA, cart_len=len(cart), total=sum(i['price'] for i in cart), table_id=tid, is_boss=is_boss)

@app.route("/update_info", methods=["POST"])
def update_info():
    session['info'] = {"type": request.form.get("type"), "table": request.form.get("table")}
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
    temp = session.get('cart', [])
    session['cart'] = [i for i in temp if i['id'] != target_id]
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
        counts = Counter([i['name'] for i in cart])
        summary_html = "<br>".join([f"{n} x{c}" for n,c in counts.items()])
        total_income += t
        order = {"id": secrets.token_hex(4), "loc": loc, "price": t, "summary": summary_html, "time": datetime.now()}
        history.append(order)
        session['cart'] = [] 
        return render_template_string(SUCCESS_HTML)
    return redirect("/")

@app.route("/boss")
def boss():
    if request.args.get("pw") != BOSS_PASSWORD: return "<h1>❌ 密碼錯誤</h1>", 403
    return render_template_string(BOSS_HTML, total=total_income, logs=history[::-1], pw=BOSS_PASSWORD)

@app.route("/print_order/<oid>")
def print_order(oid):
    target = next((h for h in history if h['id'] == oid), None)
    if target: return render_template_string(PRINT_HTML, order=target)
    return "單據不存在", 404

@app.route("/delete_order", methods=["POST"])
def delete_order():
    global history
    oid = request.form.get("id")
    target = next((h for h in history if h['id'] != oid), None)
    # 這裡邏輯修正：找到要刪除的那筆來同步
    sync_target = next((h for h in history if h['id'] == oid), None)
    if sync_target:
        sync_to_google(sync_target['summary'], sync_target['price'], sync_target['loc'])
        history = [h for h in history if h['id'] != oid]
        return jsonify({"status": "ok"})
    return jsonify({"status": "error"}), 404

# --- [ HTML 模板區 ] ---

INDEX_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<style>
    body { font-family: sans-serif; background: #fdfaf0; margin: 0; padding: 0 10px 100px; font-size: 15px; }
    .header { background: #ffbe00; color: #fff; padding: 15px; text-align: center; border-radius: 0 0 15px 15px; font-weight: bold; font-size: 20px; position: relative; }
    .boss-back { position: absolute; left: 10px; top: 12px; background: #333; color: #fff; padding: 5px 10px; border-radius: 5px; font-size: 14px; text-decoration: none; }
    .setup { background: #fff; margin: 10px 0; padding: 12px; border-radius: 10px; border-left: 6px solid #ffbe00; }
    .btn { padding: 8px 15px; border: 1.5px solid #ddd; border-radius: 20px; background: #f8f9fa; margin: 3px; font-size: 14px; cursor: pointer; }
    .btn.active { background: #ffbe00; color: #000; font-weight: bold; border-color: #ffbe00; }
    .title { background: #5d4037; color: #fff; padding: 10px 15px; border-radius: 5px; margin-top: 15px; font-size: 17px; }
    .card { background: #fff; padding: 15px; margin: 10px 0; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    .row { display: flex; justify-content: space-between; align-items: flex-start; }
    .price { color: #e67e22; font-weight: bold; font-size: 18px; }
    .add { background: #ffbe00; border: none; padding: 10px 20px; border-radius: 25px; font-weight: bold; cursor: pointer; }
    .grid { margin-top: 12px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; border-top: 1px dashed #eee; padding-top: 12px; }
    .opt { background: #fcfcfc; border: 1.5px solid #eee; padding: 8px 3px; border-radius: 8px; font-size: 13px; text-align: center; cursor: pointer; }
    .opt.active { background: #5d4037; color: #fff; border-color: #5d4037; }
    .footer { position: fixed; bottom: 0; left: 0; right: 0; background: #333; color: #fff; padding: 15px; display: flex; justify-content: space-between; align-items: center; z-index: 100; }
    .sub-text { font-size: 12px; color: #888; display: block; }
</style>
<script>
    let opts={}; let curT="{{table_id if table_id else ''}}"; let tmr;
    function start(){tmr=setTimeout(()=>{let p=prompt("密碼:"); if(p)location.href="/boss?pw="+p},2500)}
    function end(){clearTimeout(tmr)}
    function setT(t,b){fetch('/update_info',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:"type="+t+"&table="+curT});document.querySelectorAll('.type-btn').forEach(x=>x.classList.remove('active'));b.classList.add('active');document.getElementById('ts').style.display=(t==='內用')?'block':'none'}
    function setN(n,b){curT=n;fetch('/update_info',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:"type=內用&table="+n});document.querySelectorAll('.table-btn').forEach(x=>x.classList.remove('active'));b.classList.add('active')}
    function buy(n,p,i){
        let fn=n,fp=p;
        Object.keys(opts).forEach(k=>{if(k.indexOf(i+'_')===0){fn+='+'+opts[k].n; fp+=opts[k].p}});
        fetch('/add',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:"name="+encodeURIComponent(fn)+"&price="+fp})
        .then(r=>r.json()).then(d=>{
            document.getElementById('cc').innerText=d.count;
            document.getElementById('ct').innerText=d.total;
            document.querySelectorAll(".opt[data-item='"+i+"']").forEach(x=>x.classList.remove('active'));
            Object.keys(opts).forEach(k=>{if(k.indexOf(i+'_')===0)delete opts[k]});
        })
    }
    function tgl(i,n,p,b,grp){
        if(grp){document.querySelectorAll(".opt[data-grp='"+i+"_"+grp+"']").forEach(x=>{if(x!==b){x.classList.remove('active');delete opts[i+'_'+x.getAttribute('data-val')]}})}
        let k=i+'_'+n; if(opts[k]){delete opts[k];b.classList.remove('active')}else{opts[k]={n:n,p:p};b.classList.add('active')}
    }
</script></head>
<body>
    <div class="header" onmousedown="start()" onmouseup="end()" ontouchstart="start()" ontouchend="end()">
        {% if is_boss %}<a href="/boss?pw=8888" class="boss-back">🔙 返回後台</a>{% endif %}
        🍜 晨食麵所
    </div>
    <div class="setup">
        {% if table_id %}<div style="text-align:center;font-weight:bold;color:#5d4037;">內用桌號：{{table_id}}</div>
        {% else %}
        <div style="padding:5px;">用餐方式：
            <button class="btn type-btn active" onclick="setT('外帶',this)">外帶</button><button class="btn type-btn" onclick="setT('內用',this)">內用</button>
            <div id="ts" style="display:none;margin-top:8px">桌號：{% for n in range(1,6) %}<button class="btn table-btn" onclick="setN('{{n}}',this)">{{n}}</button>{% endfor %}</div>
        </div>
        {% endif %}
    </div>
    {% for cat,items in menu.items() %}
        <div class="title">{{cat}}</div>
        {% for item in items %}
            {% set iid = "id" ~ loop.index ~ cat[0] %}
            <div class="card">
                <div class="row">
                    <div style="flex:1"><strong>{{item.name}}</strong>{% if item.sub %}<span class="sub-text">{{item.sub}}</span>{% endif %}<div class="price">${{item.price}}</div></div>
                    <button class="add" onclick="buy('{{item.name}}',{{item.price}},'{{iid}}')">加入</button>
                </div>
                <div class="grid">
                    {% if item.can_add %}<div class="opt" data-item="{{iid}}" onclick="tgl('{{iid}}','加蛋',15,this)">+蛋 15</div><div class="opt" data-item="{{iid}}" onclick="tgl('{{iid}}','加起司',15,this)">+起司 15</div>{% endif %}
                    {% if item.add_meat %}<div class="opt" data-item="{{iid}}" onclick="tgl('{{iid}}','加里肌',25,this)">+里肌 25</div>{% endif %}
                    {% if item.is_toast or item.is_jam %}<div class="opt" data-item="{{iid}}" onclick="tgl('{{iid}}','酥一點',0,this)">🍞酥一點</div>{% endif %}
                    {% if item.can_spicy %}<div class="opt" data-item="{{iid}}" onclick="tgl('{{iid}}','特製辣',0,this)" style="color:red">🌶️特製辣</div>{% endif %}
                    {% if item.opts %}{% for group in item.opts %}{% set gidx=loop.index %}{% for o in group %}
                        <div class="opt" data-item="{{iid}}" data-grp="{{iid}}_{{gidx}}" data-val="{{o}}" onclick="tgl('{{iid}}','{{o}}',0,this,'{{gidx}}')">{{o}}</div>
                    {% endfor %}{% endfor %}{% endif %}
                </div>
            </div>
        {% endfor %}
    {% endfor %}
    <div class="footer"><span>已點 <span id="cc" style="color:#ffbe00;">{{cart_len}}</span> 項 | $<span id="ct" style="color:#ffbe00;">{{total}}</span></span><a href="/cart" style="background:#ffbe00;color:#000;padding:8px 20px;border-radius:20px;text-decoration:none;font-weight:bold;">去結帳</a></div>
</body></html>
"""

BOSS_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8">
<meta http-equiv="refresh" content="15"> 
<style>
    body{font-family:sans-serif;background:#f4f4f4;padding:15px;margin-bottom:80px;}
    .o{background:#fff;padding:15px;margin-bottom:15px;border-radius:10px;box-shadow:0 4px 10px rgba(0,0,0,0.1);border-left:8px solid #ffbe00;}
    .btn-print{background:#333;color:#fff;padding:12px 25px;border-radius:8px;font-size:18px;font-weight:bold;cursor:pointer;border:none;}
    .btn-done{background:#27ae60;color:#fff;padding:12px 25px;border-radius:8px;font-size:18px;font-weight:bold;cursor:pointer;border:none;margin-left:10px;}
    .boss-nav { position: fixed; top: 0; left: 0; right: 0; background: #fff; padding: 10px 15px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1); z-index: 1000; }
    .btn-order { background: #ffbe00; color: #000; padding: 8px 15px; border-radius: 5px; text-decoration: none; font-weight: bold; }
</style>
<script>
    function prt(id){ window.open('/print_order/'+id, '_blank', 'width=400,height=600'); }
    function del(id,e){ 
        if(confirm('確認出餐完成並存檔？')){
            fetch('/delete_order',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:"id="+id})
            .then(()=>e.closest('.o').remove())
        } 
    }
</script></head>
<body>
    <div class="boss-nav">
        <h3 style="margin:0;">💰 營收：${{total}}</h3>
        <div>
            <a href="/?mode=boss" class="btn-order">➕ 幫客點餐</a>
            <button onclick="location.reload()" style="margin-left:5px;">🔄 刷新</button>
        </div>
    </div>
    <div style="margin-top: 60px;">
    {% for h in logs %}
    <div class="o">
        <span style="float:right;color:#888;">{{h.time.strftime('%H:%M:%S')}}</span>
        <strong style="font-size:22px;">{{h.loc}}</strong>
        <p style="background:#fffbe6;padding:15px;border-radius:8px;font-size:19px;line-height:1.5;margin:10px 0;border:1px solid #ffe58f;">
            {{h.summary|safe}}
        </p>
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <b style="font-size:24px;color:#e67e22;">金額：${{h.price}}</b>
            <div>
                <button class="btn-print" onclick="prt('{{h.id}}')">🖨️ 印單</button>
                <button class="btn-done" onclick="del('{{h.id}}',this)">✔️ 完成</button>
            </div>
        </div>
    </div>
    {% endfor %}
    </div>
</body></html>
"""

# 其他模板 (CART, SUCCESS, PRINT) 保持與之前相同
CART_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><style>body{font-family:sans-serif;padding:20px;background:#fdfaf0;}.item{background:#fff;padding:15px;margin-bottom:10px;border-radius:10px;display:flex;justify-content:space-between;align-items:center;}</style>
<script>function rm(id){fetch('/del_item',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:"id="+id}).then(()=>location.reload())}</script></head>
<body><div style="max-width:500px;margin:auto"><h3>🛒 結帳明細 ({{loc}})</h3>
{% for i in cart %}<div class="item"><div><b>{{i.name}}</b><br><small>${{i.price}}</small></div><button onclick="rm('{{i.id}}')">刪除</button></div>{% endfor %}
<hr><h4>總計: ${{total}}</h4>
<form action="/clear" method="POST"><button type="submit" style="width:100%;background:#ffbe00;padding:15px;border:none;border-radius:10px;font-weight:bold;cursor:pointer;">確認送出訂單</button></form>
<br><a href="/" style="display:block;text-align:center;color:gray;text-decoration:none;">← 返回繼續加點</a></div></body></html>
"""

SUCCESS_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<style>body{font-family:sans-serif;text-align:center;padding-top:100px;background:#fdfaf0;}</style>
<script>setTimeout(()=>location.href='/', 3000)</script></head>
<body><h1 style="color:#27ae60;">✅ 訂單已送出</h1><p>請等候櫃台叫號或送餐</p><br><a href="/">返回點餐首頁</a></body></html>
"""

PRINT_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><style>.t{display:none}@media print{body *{visibility:hidden}.t,.t *{visibility:visible}.t{display:block;position:fixed;left:0;top:0;width:100%;font-size:22px;padding:20px}}</style>
<script>window.onload=()=>{window.print();setTimeout(()=>window.close(),1000)}</script></head>
<body><div class="t"><span style="float:right;">{{order.time.strftime('%H:%M')}}</span><b>{{order.loc}}</b><hr>{{order.summary|safe}}<hr>總額：${{order.price}}</div></body></html>
"""

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
