from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
import os, secrets
from collections import Counter
from datetime import datetime

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax')

BOSS_PASSWORD = "8888" 

# --- 菜單資料 ---
MENU_DATA = {
    "吃爽組合 (套餐)": [
        {"name": "薯條OR雞塊+飲品", "price": 60, "sub": "薯條/雞塊 二選一", "opts": [["選薯條", "選雞塊"], ["選紅茶", "選冷泡茶"]]},
        {"name": "肉蛋吐司+紅茶", "price": 60},
        {"name": "熱狗(3支)+蛋+飲品", "price": 50, "opts": [["選紅茶", "選冷泡茶"]]},
        {"name": "草莓肉鬆吐司+飲品", "price": 50, "opts": [["選紅茶", "選冷泡茶"]]},
        {"name": "巧克力薯餅吐司+飲品", "price": 50, "opts": [["選紅茶", "選冷泡茶"]]}
    ],
    "蛋餅類": [
        {"name": "原味蛋餅", "price": 30, "can_add": True}, 
        {"name": "蔥香蛋餅", "price": 35, "can_add": True}, 
        {"name": "肉鬆蛋餅", "price": 40, "can_add": True}, 
        {"name": "起司蛋餅", "price": 40, "can_add": True},
        {"name": "蔬菜蛋餅", "price": 40, "can_add": True},
        {"name": "火腿蛋餅", "price": 40, "can_add": True},
        {"name": "香煎培根蛋餅", "price": 40, "can_add": True},
        {"name": "熱狗蛋餅", "price": 40, "can_add": True},
        {"name": "塔香蛋餅", "price": 40, "can_add": True},
        {"name": "玉米蛋餅", "price": 40, "can_add": True},
        {"name": "酥脆薯餅蛋餅", "price": 45, "can_add": True},
        {"name": "特調鮪魚蛋餅", "price": 50, "can_add": True},
        {"name": "里肌肉蛋餅", "price": 50, "can_add": True},
        {"name": "辣菜脯里肌蛋餅", "price": 65, "can_add": True}
    ],
    "泡麵系列 (2包)": [
        {"name": "招牌炒泡麵", "price": 70, "can_add": True, "can_spicy": True}, 
        {"name": "起司魂炒泡麵", "price": 75, "can_add": True, "can_spicy": True},
        {"name": "椒麻炒泡麵", "price": 75, "can_add": True, "can_spicy": True},
        {"name": "菜脯辣炒泡麵", "price": 75, "can_add": True, "can_spicy": True},
        {"name": "經典沙茶炒泡麵", "price": 75, "can_add": True, "can_spicy": True}
    ],
    "炒麵系列 (200g)": [
        {"name": "蘑菇麵", "price": 55, "can_add": True},
        {"name": "黑胡椒麵", "price": 55, "can_add": True},
        {"name": "招牌爆香炒麵", "price": 70, "can_add": True, "can_spicy": True}, 
        {"name": "起司魂炒麵", "price": 75, "can_add": True, "can_spicy": True},
        {"name": "菜脯辣起司炒麵", "price": 75, "can_add": True, "can_spicy": True},
        {"name": "經典沙茶炒麵", "price": 75, "can_add": True, "can_spicy": True}
    ],
    "果醬吐司/厚片": [
        {"name": "巧克力吐司", "price": 25, "is_jam": True}, {"name": "巧克力厚片", "price": 30, "is_jam": True},
        {"name": "草莓吐司", "price": 25, "is_jam": True}, {"name": "草莓厚片", "price": 30, "is_jam": True},
        {"name": "花生吐司", "price": 25, "is_jam": True}, {"name": "花生厚片", "price": 30, "is_jam": True},
        {"name": "奶酥吐司", "price": 25, "is_jam": True}, {"name": "奶酥厚片", "price": 30, "is_jam": True}
    ],
    "烤吐司系列": [
        {"name": "煎蛋吐司", "price": 35, "can_add": True, "no_v": True},
        {"name": "火腿吐司", "price": 40, "can_add": True, "no_v": True},
        {"name": "培根吐司", "price": 40, "can_add": True, "no_v": True},
        {"name": "麥香雞吐司", "price": 40, "can_add": True, "no_v": True},
        {"name": "鮪魚吐司", "price": 50, "can_add": True, "no_v": True},
        {"name": "薯餅吐司", "price": 40, "can_add": True, "no_v": True},
        {"name": "里肌吐司", "price": 55, "can_add": True, "no_v": True}, 
        {"name": "卡啦雞腿吐司", "price": 60, "can_add": True, "no_v": True}
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
    if tid: session['info'] = {"type": "內用", "table": tid}
    return render_template_string(INDEX_HTML, menu=MENU_DATA, cart_len=len(cart), total=sum(i['price'] for i in cart), table_id=tid)

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
        now = datetime.now()
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

# --- HTML 模板 ---

INDEX_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
    <style>
        body { font-family: sans-serif; background: #fdfaf0; margin: 0; padding: 0 10px 100px; line-height: 1.4; }
        .header { background: #ffbe00; color: #fff; padding: 18px; text-align: center; border-radius: 0 0 15px 15px; font-weight: bold; font-size: 26px; }
        .setup { background: #fff; margin: 12px 0; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); border-left: 8px solid #ffbe00; font-size: 20px; }
        .btn { padding: 10px 18px; border: 1.5px solid #ddd; border-radius: 25px; background: #f8f9fa; cursor: pointer; margin: 5px; font-size: 18px; }
        .btn.active { background: #ffbe00; color: #000; font-weight: bold; border-color: #ffbe00; }
        .title { background: #5d4037; color: #fff; padding: 12px 18px; border-radius: 6px; margin-top: 20px; font-weight: bold; font-size: 22px; }
        .card { background: #fff; padding: 18px; margin: 15px 0; border-radius: 12px; box-shadow: 0 2px 6px rgba(0,0,0,0.1); }
        .row { display: flex; justify-content: space-between; align-items: center; }
        .price { color: #e67e22; font-weight: bold; font-size: 24px; margin-top: 5px; }
        .add { background: #ffbe00; border: none; padding: 15px 30px; border-radius: 30px; font-weight: bold; cursor: pointer; font-size: 22px; }
        .grid { margin-top: 15px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; border-top: 1px dashed #eee; padding-top: 15px; }
        .opt { background: #f8f9fa; border: 1.5px solid #eee; padding: 12px 5px; border-radius: 10px; font-size: 16px; text-align: center; color: #333; cursor: pointer; }
        .opt.active { background: #5d4037; color: #fff; border-color: #5d4037; font-weight: bold; }
        .footer { position: fixed; bottom: 0; left: 0; right: 0; background: #333; color: #fff; padding: 20px; display: flex; justify-content: space-between; align-items: center; z-index: 100; font-size: 22px; }
        .sub-text { font-size: 15px; color: #777; display: block; margin-top: 4px; }
    </style>
    <script>
        let opts={}; let curT="{{table_id if table_id else ''}}"; let tmr;
        function start(){tmr=setTimeout(function(){let p=prompt("密碼:"); if(p)location.href="/boss?pw="+p},3000)}
        function end(){clearTimeout(tmr)}
        function setT(t,b){fetch('/update_info',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:"type="+t+"&table="+curT});document.querySelectorAll('.type-btn').forEach(x=>x.classList.remove('active'));b.classList.add('active');let s=document.getElementById('ts');if(s)s.style.display=(t==='內用')?'block':'none'}
        function setN(n,b){curT=n;fetch('/update_info',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:"type=內用&table="+n});document.querySelectorAll('.table-btn').forEach(x=>x.classList.remove('active'));b.classList.add('active')}
        function buy(n,p,i){let fn=n,fp=p;Object.keys(opts).forEach(function(k){if(k.indexOf(i+'_')===0){fn+='+'+opts[k].n; fp+=opts[k].p}});fetch('/add',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:"name="+encodeURIComponent(fn)+"&price="+fp}).then(r=>r.json()).then(d=>{document.getElementById('cc').innerText=d.count;document.getElementById('ct').innerText=d.total;document.querySelectorAll(".opt[data-item='"+i+"']").forEach(x=>x.classList.remove('active'));Object.keys(opts).forEach(k=>{if(k.indexOf(i+'_')===0)delete opts[k]})})}
        function tgl(i,n,p,b,grp){if(grp){document.querySelectorAll(".opt[data-grp='"+i+"_"+grp+"']").forEach(function(x){if(x!==b){x.classList.remove('active'); delete opts[i+'_'+x.getAttribute('data-val')]}})}let k=i+'_'+n;if(opts[k]){delete opts[k]; b.classList.remove('active')}else{opts[k]={n:n,p:p}; b.classList.add('active')}}
    </script>
</head>
<body>
    <div class="header" onmousedown="start()" onmouseup="end()" ontouchstart="start()" ontouchend="end()">🍜 晨食麵所</div>
    <div class="setup">
        {% if table_id %}
            <div style="text-align:center;font-weight:bold;color:#5d4037;font-size:24px">內用：{{table_id}}號桌</div>
        {% else %}
            <span>用餐方式：</span>
            <button class="btn type-btn active" onclick="setT('外帶',this)">外帶</button>
            <button class="btn type-btn" onclick="setT('內用',this)">內用</button>
            <div id="ts" style="display:none;margin-top:10px">
                點選桌號：
                {% for n in range(1,11) %}
                    <button class="btn table-btn" onclick="setN('{{n}}',this)">{{n}}</button>
                {% endfor %}
            </div>
        {% endif %}
    </div>
    {% for cat,items in menu.items() %}
        <div class="title">{{cat}}</div>
        {% for item in items %}
            {% set iid = "id" ~ loop.index ~ cat[0] %}
            <div class="card">
                <div class="row">
                    <div style="flex:1">
                        <strong style="font-size:24px">{{item.name}}</strong>
                        {% if item.sub %}<span class="sub-text">{{item.sub}}</span>{% endif %}
                        <div class="price">${{item.price}}</div>
                    </div>
                    <button class="add" onclick="buy('{{item.name}}',{{item.price}},'{{iid}}')">加入</button>
                </div>
                <div class="grid">
                    {% if item.can_add %}
                        <div class="opt" data-item="{{iid}}" onclick="tgl('{{iid}}','加蛋',15,this)">+蛋 15</div>
                        <div class="opt" data-item="{{iid}}" onclick="tgl('{{iid}}','加里肌',25,this)">+里肌 25</div>
                        <div class="opt" data-item="{{iid}}" onclick="tgl('{{iid}}','加起司',15,this)">+起司 15</div>
                        {% if item.no_v %}
                            <div class="opt" data-item="{{iid}}" onclick="tgl('{{iid}}','✘生菜',0,this)" style="color:#e67e22">✘生菜</div>
                            <div class="opt" data-item="{{iid}}" onclick="tgl('{{iid}}','✘番茄',0,this)" style="color:#e67e22">✘番茄</div>
                        {% endif %}
                        {% if item.can_spicy %}
                            <div class="opt" data-item="{{iid}}" onclick="tgl('{{iid}}','特製辣',0,this)" style="color:#d35400; font-weight:bold;">🌶️特製辣</div>
                        {% endif %}
                    {% endif %}
                    {% if item.is_jam %}
                        <div class="opt" data-item="{{iid}}" onclick="tgl('{{iid}}','酥一點',0,this)">🍞酥一點</div>
                    {% endif %}
                    {% if item.opts %}
                        {% for group in item.opts %}
                            {% set gidx=loop.index %}
                            {% for o in group %}
                                <div class="opt" data-item="{{iid}}" data-grp="{{iid}}_{{gidx}}" data-val="{{o}}" onclick="tgl('{{iid}}','{{o}}',0,this,'{{gidx}}')">{{o}}</div>
                            {% endfor %}
                        {% endfor %}
                    {% endif %}
                </div>
            </div>
        {% endfor %}
    {% endfor %}
    <div class="footer">
        <span>已點 <span id="cc">{{cart_len}}</span> | $<span id="ct">{{total}}</span></span>
        <a href="/cart" style="background:#ffbe00;color:#000;padding:12px 25px;border-radius:30px;text-decoration:none;font-weight:bold;font-size:22px">去結帳</a>
    </div>
</body>
</html>
"""

CART_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"><style>body{font-family:sans-serif;padding:20px;background:#fdfaf0; font-size:22px}.item{background:#fff;padding:20px;margin-bottom:15px;border-radius:12px;display:flex;justify-content:space-between;align-items:center;box-shadow:0 2px 4px rgba(0,0,0,0.1)}.del-btn{color:#ff4444;border:2px solid #ff4444;background:none;padding:12px 20px;border-radius:10px;font-size:18px;font-weight:bold;cursor:pointer}</style>
<script>function removeItem(id, btn){fetch('/del_item',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:"id="+id}).then(()=>{location.reload();})}</script></head>
<body><div style="max-width:500px;margin:auto"><h3>🛒 訂單確認</h3><p>用餐方式：<b>{{loc}}</b></p>
{% for item in cart %}
<div class="item">
    <div><b>{{item.name}}</b><br><span style="color:#e67e22;font-weight:bold">${{item.price}}</span></div>
    <button class="del-btn" onclick="removeItem('{{item.id}}', this)">刪除</button>
</div>
{% endfor %}
<hr><h4>總計金額: <span style="color:#e67e22;font-size:32px">${{total}}</span></h4>
<form action="/clear" method="POST"><button type="submit" style="width:100%;background:#ffbe00;padding:20px;border:none;border-radius:15px;font-weight:bold;font-size:24px;cursor:pointer">確認送出訂單</button></form>
<br><a href="/" style="color:gray;text-decoration:none;display:block;text-align:center;font-size:20px">← 返回繼續加點</a></div></body></html>
"""

PRINT_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><style>body{font-family:sans-serif;text-align:center;padding-top:50px}.t{display:none}@media print{body *{visibility:hidden}.t,.t *{visibility:visible}.t{display:block;position:fixed;left:0;top:0;width:100%;font-size:26px;padding:20px}}</style><script>window.onload=function(){window.print();setTimeout(function(){location.href='/'},2000)}</script></head>
<body><h2>✅ 訂單傳送成功！</h2><div class="t"><span style="float:right">{{order.time.strftime('%H:%M')}}</span><b>{{order.loc}}</b><hr>{{order.summary|safe}}<hr><b>總額：${{order.price}}</b></div></body></html>
"""

BOSS_HTML = """
<!DOCTYPE html><html><head><meta charset="UTF-8"><style>body{font-family:sans-serif;background:#f4f4f4;padding:15px}.o{background:#fff;padding:20px;margin-bottom:15px;border-radius:12px;font-size:22px;box-shadow:0 2px 5px rgba(0,0,0,0.1)}</style><script>function del(id,e){if(confirm('確認完成？')){fetch('/delete_order',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:"id="+id}).then(function(){e.closest('.o').style.display='none'})}}</script></head>
<body><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px"><h2>💰 今日營收：${{total}}</h2><button onclick="location.href='/'" style="padding:12px 20px;font-size:18px">回點餐頁</button></div>{% for h in logs %}<div class="o"><span style="float:right;color:gray;font-size:18px">{{h.time.strftime('%H:%M')}}</span><b>{{h.loc}}</b><br><p style="background:#fffbe6;padding:12px;border-radius:8px">{{h.summary|safe}}</p><b>金額：${{h.price}}</b><button onclick="del('{{h.id}}',this)" style="float:right;color:green;border:2px solid green;background:none;padding:12px 30px;border-radius:10px;font-weight:bold;cursor:pointer">完成出餐</button><div style="clear:both"></div></div>{% endfor %}</body></html>
"""

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
