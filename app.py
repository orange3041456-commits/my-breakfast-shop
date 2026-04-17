from flask import Flask, render_template_string, request, jsonify, session, redirect
import os

app = Flask(__name__)
app.secret_key = "morning_noodle_fast_99"

# --- 菜單資料 ---
MENU = {
    "蛋餅類": [
        {"name": "原味蛋餅", "price": 30}, {"name": "蔥香蛋餅", "price": 35}, {"name": "肉鬆蛋餅", "price": 40},
        {"name": "起司/牽絲蛋餅", "price": 40}, {"name": "蔬菜蛋餅", "price": 40}, {"name": "火腿蛋餅", "price": 40},
        {"name": "香煎培根蛋餅", "price": 40}, {"name": "熱狗蛋餅", "price": 40}, {"name": "塔香蛋餅", "price": 40},
        {"name": "玉米蛋餅", "price": 40}, {"name": "酥脆薯餅蛋餅", "price": 45}, {"name": "漢堡排蛋餅", "price": 45},
        {"name": "特調鮪魚蛋餅", "price": 50}, {"name": "里肌肉蛋餅", "price": 50}, {"name": "厚切牛肉蛋餅", "price": 60},
        {"name": "辣菜脯里肌蛋餅", "price": 65}
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
        {"name": "巧克力吐司", "price": 25}, {"name": "巧克力厚片", "price": 30}, {"name": "草莓吐司", "price": 25}, {"name": "草莓厚片", "price": 30},
        {"name": "花生吐司", "price": 25}, {"name": "花生厚片", "price": 30}, {"name": "奶酥吐司", "price": 25}, {"name": "奶酥厚片", "price": 30}
    ],
    "烤吐司系列": [
        {"name": "煎蛋吐司", "price": 35}, {"name": "火腿吐司", "price": 40}, {"name": "培根吐司", "price": 40},
        {"name": "麥香雞吐司", "price": 40}, {"name": "鮪魚吐司", "price": 50}, {"name": "薯餅吐司", "price": 40},
        {"name": "漢堡排吐司", "price": 45}, {"name": "里肌吐司", "price": 55}, {"name": "卡啦雞腿吐司", "price": 60},
        {"name": "厚牛吐司", "price": 60}
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

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
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
        .quick-add { background: #f8f9fa; border: 1px solid #ddd; padding: 8px 4px; border-radius: 6px; font-size: 12px; text-align: center; cursor: pointer; font-weight: bold; }
        .quick-add span { color: #d35400; display: block; font-size: 10px; }
        .footer { position: fixed; bottom: 0; left: 0; right: 0; background: #333; color: white; padding: 12px; display: flex; justify-content: space-between; align-items: center; }
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
                m.innerText = '已加入：' + name;
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
            {% if not item.can_add %}
            <button class="add-btn" onclick="directAdd('{{ item.name }}', {{ item.price }})">加入 +</button>
            {% else %}
            <button class="add-btn" style="background:#eee;" onclick="directAdd('{{ item.name }}', {{ item.price }})">原味加入</button>
            {% endif %}
        </div>
        
        {% if item.can_add %}
        <div class="opt-grid">
            <div class="quick-add" onclick="directAdd('{{ item.name }}+加蛋', {{ item.price + 15 }})">+ 加蛋<span>$15</span></div>
            <div class="quick-add" onclick="directAdd('{{ item.name }}+加里肌', {{ item.price + 25 }})">+ 加里肌<span>$25</span></div>
            <div class="quick-add" onclick="directAdd('{{ item.name }}+加起司', {{ item.price + 15 }})">+ 加起司<span>$15</span></div>
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
    if 'cart' not in session: session['cart'] = []
    temp = session['cart']
    temp.append({"name": request.form.get("name"), "price": int(request.form.get("price"))})
    session['cart'] = temp
    return jsonify({"count": len(session['cart']), "total": sum(i['price'] for i in session['cart'])})

@app.route("/cart")
def view_cart():
    cart = session.get('cart', [])
    t = sum(i['price'] for i in cart)
    return render_template_string("""
    <div style="padding:20px; font-family:sans-serif; max-width:500px; margin:auto;">
        <h3>🛒 我的訂單</h3>
        {% for i in cart %}
        <div style="display:flex; justify-content:space-between; margin-bottom:10px; border-bottom:1px solid #eee; padding-bottom:5px;">
            <span>{{ i.name }}</span><span>${{ i.price }}</span>
        </div>
        {% endfor %}
        <h4 style="text-align:right;">總計: ${{ total }}</h4>
        <a href="/clear" style="display:block; background:#ffbe00; padding:15px; text-align:center; text-decoration:none; color:000; border-radius:10px; font-weight:bold;">確認送出</a>
        <p style="text-align:center;"><a href="/" style="color:gray; text-decoration:none;">回菜單</a></p>
    </div>
    """, cart=cart, total=t)

@app.route("/clear")
def clear():
    global total_income
    cart = session.get('cart', [])
    t = sum(i['price'] for i in cart)
    if t > 0:
        total_income += t
        history.append(f"${t} | " + "、".join([i['name'] for i in cart]))
        session.pop('cart', None)
        return "<div style='text-align:center; padding:50px;'><h2>訂單已送出！</h2><a href='/'>回首頁</a></div>"
    return redirect("/")

@app.route("/boss")
def boss():
    display_history = history[::-1][:20]
    return render_template_string("""
    <div style="padding:20px; font-family:sans-serif; background:#fff; min-height:100vh;">
        <h2 style="color:#d35400;">💰 晨食麵所後台</h2>
        <div style="background:#2ecc71; color:white; padding:15px; border-radius:8px; font-size:20px;">
            今日累計：<strong>${{ total }}</strong>
        </div>
        <h4>最近 20 筆紀錄：</h4>
        <div style="font-size:13px; color:#666;">
            {% for h in logs %}<div style="padding:10px 0; border-bottom:1px solid #eee;">{{ h }}</div>{% endfor %}
        </div>
        <br><a href="/" style="color:blue;">回前台</a>
    </div>
    """, total=total_income, logs=display_history)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
