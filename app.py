from flask import Flask, render_template_string, request, redirect, url_for
import os

app = Flask(__name__)

# --- 完整菜單資料 ---
MENU = {
    "蛋餅類": [
        {"name": "原味蛋餅", "price": 30}, {"name": "蔥香蛋餅", "price": 35}, {"name": "肉鬆蛋餅", "price": 40},
        {"name": "起司/牽絲蛋餅", "price": 40}, {"name": "蔬菜蛋餅", "price": 40}, {"name": "火腿蛋餅", "price": 40},
        {"name": "香煎培根蛋餅", "price": 40}, {"name": "熱狗蛋餅", "price": 40}, {"name": "塔香蛋餅", "price": 40},
        {"name": "玉米蛋餅", "price": 40}, {"name": "酥脆薯餅蛋餅", "price": 45}, {"name": "漢堡排蛋餅", "price": 45},
        {"name": "特調鮪魚蛋餅", "price": 50}, {"name": "里肌肉蛋餅", "price": 50}, {"name": "厚切牛肉蛋餅", "price": 60},
        {"name": "辣菜脯里肌蛋餅", "price": 65}
    ],
    "果醬吐司/厚片": [
        {"name": "巧克力吐司", "price": 25}, {"name": "巧克力厚片", "price": 30},
        {"name": "草莓吐司", "price": 25}, {"name": "草莓厚片", "price": 30},
        {"name": "花生吐司", "price": 25}, {"name": "花生厚片", "price": 30},
        {"name": "奶酥吐司", "price": 25}, {"name": "奶酥厚片", "price": 30}
    ],
    "烤吐司系列": [
        {"name": "煎蛋吐司", "price": 35}, {"name": "火腿吐司", "price": 40}, {"name": "培根吐司", "price": 40},
        {"name": "麥香雞吐司", "price": 40}, {"name": "鮪魚吐司", "price": 50}, {"name": "薯餅吐司", "price": 40},
        {"name": "漢堡排吐司", "price": 45}, {"name": "里肌吐司", "price": 55}, {"name": "卡啦雞腿吐司", "price": 60},
        {"name": "厚牛吐司", "price": 60}
    ],
    "炒泡麵/炒麵": [
        {"name": "招牌炒泡麵", "price": 70}, {"name": "起司魂炒泡麵", "price": 75}, {"name": "椒麻炒泡麵", "price": 75},
        {"name": "菜脯辣炒泡麵", "price": 75}, {"name": "經典沙茶炒泡麵", "price": 75},
        {"name": "蘑菇炒麵", "price": 55}, {"name": "黑胡椒炒麵", "price": 55}, {"name": "招牌爆香炒麵", "price": 70},
        {"name": "起司魂炒麵", "price": 75}, {"name": "菜脯辣起司炒麵", "price": 75}, {"name": "經典沙茶炒麵", "price": 75}
    ],
    "單點小點": [
        {"name": "荷包蛋", "price": 15}, {"name": "玉米蛋", "price": 35}, {"name": "蔥蛋", "price": 25},
        {"name": "熱狗(3支)", "price": 20}, {"name": "薯餅", "price": 25}, {"name": "麥克雞塊", "price": 45},
        {"name": "小肉豆", "price": 40}, {"name": "美式脆條", "price": 45}, {"name": "抓餅", "price": 35},
        {"name": "港式蘿蔔糕", "price": 35}, {"name": "雞柳條", "price": 50}, {"name": "黃金蝦排", "price": 35}
    ],
    "套餐系列": [
        {"name": "熱狗+蛋+飲品", "price": 50}, {"name": "草莓肉鬆吐司+飲品", "price": 50},
        {"name": "巧克力薯餅吐司+飲品", "price": 50}, {"name": "肉蛋吐司+紅茶", "price": 60},
        {"name": "雞塊+飲品", "price": 45}, {"name": "薯條+飲品", "price": 50},
        {"name": "蘿蔔糕混蔥蛋+飲品", "price": 60}, {"name": "薯條雞塊+飲品", "price": 70},
        {"name": "花生培根厚牛吐司(含蛋)+飲品", "price": 100}
    ],
    "飲品 (L)": [
        {"name": "紅茶", "price": 25}, {"name": "香醇奶茶", "price": 30}, {"name": "冷泡茶", "price": 25},
        {"name": "豆漿(無糖)", "price": 35}, {"name": "鮮奶茶", "price": 45}, {"name": "豆漿紅茶", "price": 40}
    ]
}

# --- 數據儲存 ---
cart = []
history = []
total_income = 0

# --- 介面設計 ---
HTML = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>活力晨食點餐系統</title>
    <style>
        body { font-family: 'PingFang TC', sans-serif; background-color: #fdfaf0; color: #444; margin: 0; padding: 15px; }
        .header { background: #ffbe00; color: #fff; padding: 20px; text-align: center; border-radius: 0 0 20px 20px; font-size: 24px; font-weight: bold; margin-bottom: 20px; }
        .section-title { background: #5d4037; color: white; padding: 8px 15px; border-radius: 5px; margin-top: 20px; }
        .item-card { background: white; padding: 12px; margin: 8px 0; border-radius: 12px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
        .price { color: #e67e22; font-weight: bold; }
        .add-btn { background: #ffbe00; border: none; padding: 8px 15px; border-radius: 20px; cursor: pointer; font-weight: bold; }
        .footer-cart { position: fixed; bottom: 0; left: 0; right: 0; background: #333; color: white; padding: 15px; display: flex; justify-content: space-between; align-items: center; }
        .checkout-link { background: #ffbe00; color: black; padding: 10px 20px; border-radius: 25px; text-decoration: none; font-weight: bold; }
        .cart-item { border-bottom: 1px solid #eee; padding: 10px 0; display: flex; justify-content: space-between; }
    </style>
</head>
<body>
    <div class="header">🍳 活力晨食點餐</div>
    
    {% for cat, items in menu.items() %}
    <div class="section-title">{{ cat }}</div>
    {% for item in items %}
    <div class="item-card">
        <div><strong>{{ item.name }}</strong><br><span class="price">${{ item.price }}</span></div>
        <form method="POST" action="/add">
            <input type="hidden" name="name" value="{{ item.name }}">
            <input type="hidden" name="price" value="{{ item.price }}">
            <button class="add-btn">加入 +</button>
        </form>
    </div>
    {% endfor %}
    {% endfor %}

    <div style="height: 100px;"></div>

    <div class="footer-cart">
        <span>已點 {{ cart|length }} 項 | 總計: ${{ total }}</span>
        <a href="/cart" class="checkout-link">查看清單 / 結帳</a>
    </div>
</body>
</html>
"""

# --- 路由 ---

@app.route("/")
def index():
    t = sum(i['price'] for i in cart)
    return render_template_string(HTML, menu=MENU, cart=cart, total=t)

@app.route("/add", methods=["POST"])
def add():
    name = request.form.get("name")
    price = int(request.form.get("price"))
    cart.append({"name": name, "price": price})
    return redirect(url_for("index"))

@app.route("/cart")
def view_cart():
    t = sum(i['price'] for i in cart)
    cart_page = """
    <div style="padding:20px; font-family:sans-serif;">
        <h2>🛒 我的點餐清單</h2>
        {% for i in cart %}
        <div style="display:flex; justify-content:space-between; padding:10px 0; border-bottom:1px solid #eee;">
            <span>{{ i.name }}</span><span>${{ i.price }}</span>
        </div>
        {% endfor %}
        <h3 style="text-align:right;">總金額：${{ total }}</h3>
        <a href="/clear" style="display:block; background:#ffbe00; padding:15px; text-align:center; color:black; text-decoration:none; border-radius:10px; font-weight:bold;">確認送出訂單</a>
        <br><a href="/" style="display:block; text-align:center; color:gray;">繼續加點</a>
    </div>
    """
    return render_template_string(cart_page, cart=cart, total=t)

@app.route("/clear")
def clear():
    global total_income
    t = sum(i['price'] for i in cart)
    if t > 0:
        total_income += t
        items_str = ", ".join([i['name'] for i in cart])
        history.append(f"收入: ${t} | 品項: {items_str}")
        cart.clear()
        return "<h1>訂單已送達廚房！感謝您的購買。</h1><a href='/'>回首頁</a>"
    return redirect("/")

@app.route("/boss")
def boss():
    return f"""
    <div style="font-family:sans-serif; padding:20px;">
        <h1 style="color:#d35400;">💰 老闆營收報表</h1>
        <div style="background:#2ecc71; color:white; padding:20px; border-radius:10px; font-size:24px;">
            今日總收：<strong>${total_income}</strong>
        </div>
        <hr>
        <h3>訂單細節：</h3>
        <ul>
            {"".join([f"<li>{h}</li>" for h in history[::-1]])}
        </ul>
        <a href="/">回到前台</a>
    </div>
    """

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
