from flask import Flask, render_template_string, request, jsonify, session, redirect
import os
import secrets
from collections import Counter
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

# --- 菜單資料 ---
MENU = {
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
    "泡麵/炒麵(200g)": [
        {"name": "招牌炒泡麵", "price": 70, "can_add": True}, {"name": "起司魂炒泡麵", "price": 75, "can_add": True}, 
        {"name": "椒麻炒泡麵", "price": 75, "can_add": True}, {"name": "菜脯辣炒泡麵", "price": 75, "can_add": True}, 
        {"name": "經典沙茶炒泡麵", "price": 75, "can_add": True}, {"name": "蘑菇炒麵", "price": 55, "can_add": True}, 
        {"name": "黑胡椒炒麵", "price": 55, "can_add": True}, {"name": "招牌爆香炒麵", "price": 70, "can_add": True},
        {"name": "起司魂炒麵", "price": 75, "can_add": True}, {"name": "菜脯辣起司炒麵", "price": 75, "can_add": True}, 
        {"name": "經典沙茶炒麵", "price": 75, "can_add": True}
    ],
    "果醬吐司/厚片": [
        {"name": "巧克力吐司", "price": 25}, {"name": "巧克力厚片", "price": 30}, {"name": "草莓吐司", "price": 25}, 
        {"name": "草莓厚片", "price": 30}, {"name": "花生吐司", "price": 25}, {"name": "花生厚片", "price": 30}, 
        {"name": "奶酥吐司", "price": 25}, {"name": "奶酥厚片", "price": 30}
    ],
    "烤吐司系列": [
        {"name": "煎蛋吐司", "price": 35, "can_add": True}, {"name": "火腿吐司", "price": 40, "can_add": True}, 
        {"name": "培根吐司", "price": 40, "can_add": True}, {"name": "麥香雞吐司", "price": 40, "can_add": True}, 
        {"name": "鮪魚吐司", "price": 50, "can_add": True}, {"name": "薯餅吐司", "price": 40, "can_add": True},
        {"name": "漢堡排吐司", "price": 45, "can_add": True}, {"name": "里肌吐司", "price": 55, "can_add": True}, 
        {"name": "卡啦雞腿吐司", "price": 60, "can_add": True}, {"name": "厚牛吐司", "price": 60, "can_add": True}
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

# --- 自動清理函數 ---
def clean_expired_data():
    global history, total_income
    now = datetime.now()
    cutoff = now - timedelta(hours=24)
    
    # 只保留 24 小時內的訂單
    new_history = [h for h in history if h['time'] > cutoff]
    
    # 如果有訂單被刪除，重新計算累計金額 (或者你想連 24 小時前的金額也保留，可不改 total_income)
    # 這裡採取的做法是：總金額也會隨之「清零」24小時前的部分，保持今日帳目正確。
    if len(new_history) != len(history):
        history = new_history
        total_income = sum(h['price'] for h in history)

@app.before_request
def ensure_session():
    clean_expired_data() # 每次有人瀏覽網頁時，自動檢查有沒有過期資料
    if 'cart' not in session: session['cart'] = []
    if 'order_info' not in session: session['order_info'] = {"type": "外帶", "table": ""}
    session.modified = True

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
        .order-setup { background: #fff; margin: 10px 0; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); border-left: 5px solid #ffbe00; }
        .setup-title { font-weight: bold; margin-bottom: 10px; display: block; }
        .type-btn { padding: 8px 15px; border: 1px solid #ddd; border-radius: 20px; background: #f8f9fa; cursor: pointer; margin-right: 5px; font-size: 14px; }
        .type-btn.active { background: #ffbe00; border-color: #ffbe00; color: #000; font-weight: bold; }
        #table-select { margin-top: 10px; display: none; }
        .table-btn { padding: 8px 12px; border: 1px solid #ddd; border-radius: 5px; margin: 2px; background: white; cursor: pointer; }
        .table-btn.active { background: #5d4037; color: white; border-color: #5d4037; }
        .section-title { background: #5d4037; color: white; padding: 5px 12px; border-radius: 4px; margin-top: 15px; font-size: 14px; }
        .item-card { background: white; padding: 12px; margin: 8px 0; border-radius: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .item-row { display: flex; justify-content: space-between; align-items: center; }
        .price { color: #e67e22; font-weight: bold; }
        .add-btn { background: #ffbe00; border: none; padding: 8px 14px; border-radius: 15px; font-weight: bold; cursor: pointer; }
        .opt-grid { margin-top: 10px; display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; border-top: 1px dashed #eee; padding-top: 10px; }
        .opt-btn { background: #f8f9fa; border: 1px solid #ddd; padding: 8px 0; border-radius: 6px; font-size: 12px; text-align: center; cursor: pointer; }
        .opt-btn.active { background: #5d4037; color: white; border-color: #5d4037; }
        .footer { position: fixed; bottom: 0; left: 0; right: 0; background: #333; color: white; padding: 12px; display: flex; justify-content: space-between; align-items: center; z-index: 100; }
        .msg { position: fixed; top: 10px; left: 50%; transform: translateX(-50%); background: #2ecc71; color: white; padding: 8px 16px; border-radius: 20px; display: none; z-index: 999; }
    </style>
    <script>
        let selectedOptions = {};
        function setOrderType(type, btn) {
            fetch('/update_info', {
                method: 'POST',
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                body: `type=${type}&table=`
            });
            document.querySelectorAll('.type-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById('table-select').style.display = (type === '內用') ? 'block' : 'none';
        }
        function setTable(num, btn) {
            fetch('/update_info', {
                method: 'POST',
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                body: `type=內用&table=${num}`
            });
            document.querySelectorAll('.table-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        }
        function toggleOpt(itemId, optName, price, btn) {
            const key = itemId + '_' + optName;
            if (selectedOptions[key]) {
                delete selectedOptions[key];
                btn.classList.remove('active');
            } else {
                selectedOptions[key] = {name: optName, price: price};
                btn.classList.add('active');
            }
        }
        function addToCart(baseName, basePrice, itemId) {
            let finalName = baseName;
            let finalPrice = basePrice;
            Object.keys(selectedOptions).forEach(key => {
                if (key.startsWith(itemId + '_')) {
                    finalName += '+' + selectedOptions[key].name;
                    finalPrice += selectedOptions[key].price;
                }
            });
            fetch('/add', {
                method: 'POST',
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                body: `name=${encodeURIComponent(finalName)}&price=${finalPrice}`
            }).then(r => r.json()).then(data => {
                document.getElementById('c-count').innerText = data.count;
                document.getElementById('c-total').innerText = data.total;
                const m = document.getElementById('msg-box');
                m.innerText = '已加：' + finalName;
                m.style.display = 'block';
                setTimeout(() => { m.style.display = 'none'; }, 800);
                Object.keys(selectedOptions).forEach(key => { if (key.startsWith(itemId + '_')) delete selectedOptions[key]; });
                document.querySelectorAll(`[data-item="${itemId}"]`).forEach(b => b.classList.remove('active'));
            });
        }
    </script>
</head>
<body>
    <div id="msg-box" class="msg"></div>
    <div class="header">🍜 晨食麵所</div>
    <div class="order-setup">
        <span class="setup-title">📍 請選擇用餐方式：</span>
        <button class="type-btn active" onclick="setOrderType('外帶', this)">🥡 外帶</button>
        <button class="type-btn" onclick="setOrderType('內用', this)">🍽️ 內用</button>
        <div id="table-select">
            <span class="setup-title">🪑 選擇桌號：</span>
            {% for n in range(1, 8) %}
            <button class="table-btn" onclick="setTable('{{ n }}', this)">{{ n }}</button>
            {% endfor %}
        </div>
    </div>
    {% for cat, items in menu.items() %}
    <div class="section-title">{{ cat }}</div>
    {% for item in items %}
    {% set itemId = loop.index0 ~ cat %}
    <div class="item-card">
        <div class="item-row">
            <div><strong>{{ item.name }}</strong><br><span class="price">${{ item.price }}</span></div>
            <button class="add-btn" onclick="addToCart('{{ item.name }}', {{ item.price }}, '{{ itemId }}')">加入 +</button>
        </div>
        {% if item.can_add %}
        <div class="opt-grid">
            <div class="opt-btn" data-item="{{ itemId }}" onclick="toggleOpt('{{ itemId }}', '加蛋', 15, this)">+ 加蛋</div>
            <div class="opt-btn" data-item="{{ itemId }}" onclick="toggleOpt('{{ itemId }}', '加里肌', 25, this)">+ 加里肌</div>
            <div class="opt-btn" data-item="{{ itemId }}" onclick="toggleOpt('{{ itemId }}', '加起司', 15, this)">+ 加起司</div>
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
    location = f"{info['type']}" + (f"-{info['table']}桌" if info['table'] else "")
    return render_template_string("""
    <div style="padding:20px; font-family:sans-serif; max-width:500px; margin:auto;">
        <h3>🛒 訂單清單</h3>
        <p style="background:#eee; padding:10px; border-radius:5px;"><strong>用餐方式：</strong> {{ loc }}</p>
        {% if not counts %}<p>目前沒點餐喔！</p>{% endif %}
        {% for name, count in counts.items() %}
        <p style="font-size:18px;"><strong>{{ name }}</strong> <span style="color:red;"> x {{ count }}</span></p>
        {% endfor %}
        <hr>
        <h4 style="text-align:right;">總計: ${{ total }}</h4>
        <form action="/clear" method="POST">
            <button type="submit" style="width:100%; background:#ffbe00; padding:15px; border:none; border-radius:10px; font-weight:bold; font-size:18px;">確認送出訂單</button>
        </form>
        <p style="text-align:center; margin-top:20px;"><a href="/" style="color:gray;">回菜單修改</a></p>
    </div>
    """, counts=counts, total=t, loc=location)

@app.route("/clear", methods=["POST"])
def clear():
    global total_income
    cart = session.get('cart', [])
    info = session.get('order_info', {"type": "外帶", "table": ""})
    t = sum(i['price'] for i in cart)
    location = f"{info['type']}" + (f"-{info['table']}桌" if info['table'] else "")
    if t > 0:
        total_income += t
        counts = Counter([i['name'] for i in cart])
        items_summary = [f"{n} x {c}" for n, c in counts.items()]
        # 存入當前時間 datetime.now()
        history.append({
            "id": secrets.token_hex(4), 
            "loc": location, 
            "price": t, 
            "summary": items_summary,
            "time": datetime.now() 
        })
        session.clear()
        return "<div style='text-align:center; padding:50px;'><h2>🎉 訂單已送出！</h2><br><a href='/'>回首頁</a></div>"
    return redirect("/")

@app.route("/delete_order", methods=["POST"])
def delete_order():
    order_id = request.form.get("id")
    global history
    history = [h for h in history if h['id'] != order_id]
    return jsonify({"status": "deleted"})

@app.route("/boss")
def boss():
    clean_expired_data() # 後台頁面也觸發一次清理
    display_history = history[::-1]
    return render_template_string("""
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body { font-family: sans-serif; padding: 10px; background: #f4f4f4; }
            .order-item { background: white; border-radius: 10px; padding: 15px; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .print-btn { background: #333; color: #fff; border: none; padding: 10px 20px; border-radius: 5px; cursor:pointer; font-weight:bold; }
            .done-btn { background: #e74c3c; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor:pointer; margin-left:10px; font-weight:bold; }
            .item-line { font-size: 18px; margin: 5px 0; border-bottom: 1px solid #eee; padding-bottom: 5px; }
            .time-tag { font-size: 12px; color: gray; float: right; }
            .qty { color: red; font-weight: bold; font-size: 20px; }
            @media print {
                .no-print { display: none !important; }
                body { padding: 0; margin: 0; width: 58mm; background: white; }
                .order-item { border-bottom: 1px dashed #000; padding: 10px 0; box-shadow: none; page-break-after: always; }
                .shop-name { font-size: 18px; font-weight: bold; display: block !important; }
            }
            .shop-name { display: none; }
        </style>
        <script>
            function removeOrder(id, element) {
                if(confirm('確定要移除這筆訂單嗎？')) {
                    fetch('/delete_order', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                        body: `id=${id}`
                    }).then(() => {
                        element.closest('.order-item').style.display = 'none';
                    });
                }
            }
        </script>
    </head>
    <body>
        <div class="no-print">
            <h2 style="text-align:center;">💰 晨食麵所 後台</h2>
            <div style="background:#2ecc71; color:white; padding:15px; border-radius:8px; font-size:22px; text-align:center; font-weight:bold; margin-bottom:10px;">
                24H 累計金額：${{ total }}
            </div>
            <p style="text-align:center; font-size:12px; color:gray;">(系統會自動清除 24 小時前的舊訂單)</p>
            <hr>
        </div>
        {% for h in logs %}
        <div class="order-item">
            <span class="time-tag">{{ h.time.strftime('%H:%M') }}</span>
            <div class="shop-name">晨食麵所 - 訂單</div>
            <div style="font-size: 24px; font-weight: bold; color: #5d4037;">{{ h.loc }}</div>
            <div style="margin: 10px 0;">
                {% for line in h.summary %}
                <div class="item-line">
                    {% set parts = line.split(' x ') %}
                    {{ parts[0] }} <span class="qty">x {{ parts[1] }}</span>
                </div>
                {% endfor %}
            </div>
            <div style="font-size: 18px; font-weight: bold;">總計：${{ h.price }}</div>
            <div class="no-print" style="margin-top:15px;">
                <button class="print-btn" onclick="window.print()">列印出單</button>
                <button class="done-btn" onclick="removeOrder('{{ h.id }}', this)">結案 / 刪除</button>
            </div>
        </div>
        {% endfor %}
    </body>
    </html>
    """, total=total_income, logs=display_history)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
