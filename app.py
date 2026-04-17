from flask import Flask, render_template_string, request, jsonify, session, redirect
import os
import secrets
from collections import Counter

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax')

# --- 菜單資料 ---
MENU = {
    "蛋餅類": [
        {"name": "原味蛋餅", "price": 30, "add": True}, {"name": "蔥香蛋餅", "price": 35, "add": True}, 
        {"name": "肉鬆蛋餅", "price": 40, "add": True}, {"name": "起司/牽絲蛋餅", "price": 40, "add": True}, 
        {"name": "蔬菜蛋餅", "price": 40, "add": True}, {"name": "火腿蛋餅", "price": 40, "add": True},
        {"name": "香煎培根蛋餅", "price": 40, "add": True}, {"name": "熱狗蛋餅", "price": 40, "add": True}, 
        {"name": "塔香蛋餅", "price": 40, "add": True}, {"name": "玉米蛋餅", "price": 40, "add": True}, 
        {"name": "酥脆薯餅蛋餅", "price": 45, "add": True}, {"name": "漢堡排蛋餅", "price": 45, "add": True},
        {"name": "特調鮪魚蛋餅", "price": 50, "add": True}, {"name": "里肌肉蛋餅", "price": 50, "add": True}, 
        {"name": "厚切牛肉蛋餅", "price": 60, "add": True}, {"name": "辣菜脯里肌蛋餅", "price": 65, "add": True}
    ],
    "泡麵/炒麵(200g)": [
        {"name": "招牌炒泡麵", "price": 70, "add": True}, {"name": "起司魂炒泡麵", "price": 75, "add": True}, 
        {"name": "椒麻炒泡麵", "price": 75, "add": True}, {"name": "菜脯辣炒泡麵", "price": 75, "add": True}, 
        {"name": "經典沙茶炒泡麵", "price": 75, "add": True}, {"name": "蘑菇炒麵", "price": 55, "add": True}, 
        {"name": "黑胡椒炒麵", "price": 55, "add": True}, {"name": "招牌爆香炒麵", "price": 70, "add": True},
        {"name": "起司魂炒麵", "price": 75, "add": True}, {"name": "菜脯辣起司炒麵", "price": 75, "add": True}, 
        {"name": "經典沙茶炒麵", "price": 75, "add": True}
    ],
    "果醬吐司/厚片": [
        {"name": "巧克力吐司", "price": 25}, {"name": "巧克力厚片", "price": 30}, {"name": "草莓吐司", "price": 25}, 
        {"name": "草莓厚片", "price": 30}, {"name": "花生吐司", "price": 25}, {"name": "花生厚片", "price": 30}, 
        {"name": "奶酥吐司", "price": 25}, {"name": "奶酥厚片", "price": 30}
    ],
    "烤吐司系列": [
        {"name": "煎蛋吐司", "price": 35, "add": True}, {"name": "火腿吐司", "price": 40, "add": True}, 
        {"name": "培根吐司", "price": 40, "add": True}, {"name": "麥香雞吐司", "price": 40, "add": True}, 
        {"name": "鮪魚吐司", "price": 50, "add": True}, {"name": "薯餅吐司", "price": 40, "add": True},
        {"name": "漢堡排吐司", "price": 45, "add": True}, {"name": "里肌吐司", "price": 55, "add": True}, 
        {"name": "卡啦雞腿吐司", "price": 60, "add": True}, {"name": "厚牛吐司", "price": 60, "add": True}
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
    session.modified = True

# --- 主頁面 ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>晨食麵所</title>
    <style>
        body { font-family: sans-serif; background: #fdfaf0; margin: 0; padding: 10px; padding-bottom: 80px; }
        .header { background: #ffbe00; color: #fff; padding: 15px; text-align: center; border-radius: 0 0 15px 15px; font-weight: bold; }
        .section-title { background: #5d4037; color: white; padding: 5px 12px; border-radius: 4px; margin-top: 15px; font-size: 14px; }
        .item-card { background: white; padding: 12px; margin: 8px 0; border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .item-row { display: flex; justify-content: space-between; align-items: center; }
        .price { color: #e67e22; font-weight: bold; }
        .add-btn { background: #ffbe00; border: none; padding: 8px 14px; border-radius: 15px; font-weight: bold; cursor: pointer; }
        .opt-grid { margin-top: 10px; display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; border-top: 1px dashed #eee; padding-top: 10px; }
        .quick-add { background: #f8f9fa; border: 1px solid #ddd; padding: 8px 4px; border-radius: 6px; font-size: 11px; text-align: center; cursor: pointer; font-weight: bold; }
        .footer { position: fixed; bottom: 0; left: 0; right: 0; background: #333; color: white; padding: 12px; display: flex; justify-content: space-between; align-items: center; z-index: 100; }
        .msg { position: fixed; top: 10px; left: 50%; transform: translateX(-50%); background: #2ecc71; color: white; padding: 8px 16px; border-radius: 20px; display: none; z-index: 999; }
    </style>
    <script>
        function directAdd(name, price) {
            fetch('/add', {
                method: 'POST',
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                body: `name=${encodeURIComponent(name)}&price=${price}`
            }).then(r => r.json()).then(data => {
                document.getElementById('c-count').innerText = data.count;
                document.getElementById('c-total').innerText = data.total;
                const m = document.getElementById('msg-box');
                m.innerText = '已加：' + name;
                m.style.display = 'block';
                setTimeout(() => { m.style.display = 'none'; }, 800);
            });
        }
    </script>
</head>
<body>
    <div id="msg-box" class="msg"></div>
    <div class="header">🍜 晨食麵所</div>
    {% for cat, items in menu.items() %}
    <div class="section-title">{{ cat }}</div>
    {% for item in items %}
    <div class="item-card">
        <div class="item-row">
            <div><strong>{{ item.name }}</strong><br><span class="price">${{ item.price }}</span></div>
            <button class="add-btn" onclick="directAdd('{{ item.name }}', {{ item.price }})">原味加入</button>
        </div>
        {% if item.add %}
        <div class="opt-grid">
            <div class="quick-add" onclick="directAdd('{{ item.name }}+蛋', {{ item.price + 15 }})">+ 加蛋</div>
            <div class="quick-add" onclick="directAdd('{{ item.name }}+里肌', {{ item.price + 25 }})">+ 加里肌</div>
            <div class="quick-add" onclick="directAdd('{{ item.name }}+起司', {{ item.price + 15 }})">+ 加起司</div>
        </div>
        {% endif %}
    </div>
    {% endfor %}
    {% endfor %}
    <div class="footer">
        <span>已點 <span id="c-count">{{ cart_len }}</span> 項 | $<span id="c-total">{{ total }}</span></span>
        <a href="/cart" style="background:#ffbe00; color:000; padding:8px 15px; border-radius:20px; text-decoration:none; font-weight:bold;">去結帳</a>
    </div>
</body>
</html>
"""

@app.route("/")
def index():
    cart = session.get('cart', [])
    return render_template_string(HTML_TEMPLATE, menu=MENU, cart_len=len(cart), total=sum(i['price'] for i in cart))

@app.route("/add", methods=["POST"])
def add():
    temp = session.get('cart', [])
    temp.append({"name": request.form.get("name"), "price": int(request.form.get("price"))})
    session['cart'] = temp
    return jsonify({"count": len(session['cart']), "total": sum(i['price'] for i in session['cart'])})

@app.route("/cart")
def view_cart():
    cart = session.get('cart', [])
    t = sum(i['price'] for i in cart)
    # 統計相同品項數量
    counts = Counter([i['name'] for i in cart])
    return render_template_string("""
    <div style="padding:20px; font-family:sans-serif; max-width:500px; margin:auto;">
        <h3>🛒 訂單清單</h3>
        {% for name, count in counts.items() %}
        <p style="font-size:18px;"><strong>{{ name }}</strong> <span style="color:red;"> x {{ count }}</span></p>
        {% endfor %}
        <hr>
        <form action="/clear" method="POST">
            <h4>1. 用餐方式：</h4>
            <label><input type="radio" name="order_type" value="外帶" checked onclick="document.getElementById('ts').style.display='none'"> 🥡 外帶</label>
            <label><input type="radio" name="order_type" value="內用" onclick="document.getElementById('ts').style.display='block'"> 🍽️ 內用</label>
            <div id="ts" style="display:none; margin-top:10px; background:#f9f9f9; padding:10px; border-radius:5px;">
                <p>2. 桌號：</p>
                {% for n in range(1, 8) %}
                <label style="margin-right:10px;"><input type="radio" name="table_num" value="{{ n }}"> {{ n }}桌</label>
                {% endfor %}
            </div>
            <h4 style="text-align:right;">總計: ${{ total }}</h4>
            <button type="submit" style="width:100%; background:#ffbe00; padding:15px; border:none; border-radius:10px; font-weight:bold; font-size:18px;">送出訂單</button>
        </form>
    </div>
    """, counts=counts, total=t)

@app.route("/clear", methods=["POST"])
def clear():
    global total_income
    cart = session.get('cart', [])
    t = sum(i['price'] for i in cart)
    order_type = request.form.get("order_type")
    table_num = request.form.get("table_num")
    location = f"{order_type}" if order_type == "外帶" else f"內用-{table_num}桌"
    
    if t > 0:
        total_income += t
        counts = Counter([i['name'] for i in cart])
        items_summary = [f"{n} x {c}" for n, c in counts.items()]
        history.append({"loc": location, "price": t, "summary": items_summary})
        session.clear()
        return "<div style='text-align:center; padding:50px;'><h2>🎉 訂單已送出！</h2><br><a href='/'>回首頁</a></div>"
    return redirect("/")

@app.route("/boss")
def boss():
    display_history = history[::-1][:20]
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: sans-serif; padding: 10px; }
            .order-item { border-bottom: 2px solid #333; padding: 15px 0; }
            .print-btn { background: #333; color: #fff; border: none; padding: 10px 20px; border-radius: 5px; margin-top:10px; }
            .item-line { font-size: 18px; margin: 5px 0; }
            .qty { color: red; font-weight: bold; font-size: 20px; }
            @media print {
                .no-print { display: none !important; }
                body { padding: 0; margin: 0; width: 58mm; }
                .order-item { border-bottom: 1px dashed #000; padding: 10px 0; page-break-after: always; }
                .shop-name { font-size: 18px; font-weight: bold; display: block !important; }
                .qty { color: black; border: 1px solid black; padding: 0 3px; }
            }
            .shop-name { display: none; }
        </style>
    </head>
    <body>
        <div class="no-print">
            <h2>💰 後台管理</h2>
            <div style="background:#2ecc71; color:white; padding:15px; border-radius:8px; font-size:20px; text-align:center;">今日累計：${{ total }}</div>
            <hr>
        </div>
        {% for h in logs %}
        <div class="order-item">
            <div class="shop-name">晨食麵所 - 訂單</div>
            <div style="font-size: 24px; font-weight: bold;">{{ h.loc }}</div>
            <div style="margin: 10px 0;">
                {% for line in h.summary %}
                <div class="item-line">
                    {% set parts = line.split(' x ') %}
                    {{ parts[0] }} <span class="qty">x {{ parts[1] }}</span>
                </div>
                {% endfor %}
            </div>
            <div style="font-size: 18px;">總計：${{ h.price }}</div>
            <button class="print-btn no-print" onclick="window.print()">列印出單</button>
        </div>
        {% endfor %}
    </body>
    </html>
    """, total=total_income, logs=display_history)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
