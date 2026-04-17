from flask import Flask, render_template_string, request, redirect, url_for
import os

app = Flask(__name__)

# --- 早餐店菜單資料 ---
MENU = {
    "熱門蛋餅": [
        {"id": 1, "name": "原味蛋餅", "price": 30},
        {"id": 2, "name": "玉米蛋餅", "price": 40},
        {"id": 3, "name": "里肌豬排蛋餅", "price": 55}
    ],
    "經典飲品": [
        {"id": 10, "name": "好喝紅茶", "price": 25},
        {"id": 11, "name": "濃郁奶茶", "price": 30},
        {"id": 12, "name": "研磨咖啡", "price": 45}
    ]
}

# --- 記憶體儲存 (重啟會歸零) ---
current_cart = []    # 客人現在選的
order_history = []   # 已經結帳的訂單
total_sales = 0      # 總營業額

# --- 網頁介面 (HTML) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>活力早餐店</title>
    <style>
        body { font-family: sans-serif; background: #f4f4f4; margin: 0; padding: 20px; }
        .card { background: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
        .btn { background: #ffbe00; border: none; padding: 10px 15px; border-radius: 5px; cursor: pointer; font-weight: bold; }
        .cart-box { background: #333; color: white; padding: 20px; border-radius: 10px; margin-top: 20px; }
        .checkout-btn { background: #4CAF50; color: white; text-decoration: none; padding: 10px; display: block; text-align: center; border-radius: 5px; margin-top: 10px; }
    </style>
</head>
<body>
    <h1>🍳 活力早餐店點餐</h1>
    
    {% for category, items in menu.items() %}
    <h3>{{ category }}</h3>
    {% for item in items %}
    <div class="card">
        <div><strong>{{ item.name }}</strong><br>${{ item.price }}</div>
        <form method="POST" action="/add">
            <input type="hidden" name="id" value="{{ item.id }}">
            <button class="btn">加入購物車</button>
        </form>
    </div>
    {% endfor %}
    {% endfor %}

    <div class="cart-box">
        <h3>🛒 購物車 ({{ cart|length }} 件項目)</h3>
        <ul>
            {% for item in cart %}
            <li>{{ item.name }} - ${{ item.price }}</li>
            {% endfor %}
        </ul>
        <hr>
        <h4>總計：${{ total }}</h4>
        {% if cart %}
        <a href="/checkout" class="checkout-btn">確認送出訂單</a>
        {% endif %}
    </div>
</body>
</html>
"""

# --- 路由設定 (功能) ---

@app.route("/")
def index():
    t = sum(item["price"] for item in current_cart)
    return render_template_string(HTML_TEMPLATE, menu=MENU, cart=current_cart, total=t)

@app.route("/add", methods=["POST"])
def add_to_cart():
    item_id = int(request.form.get("id"))
    # 找尋對應商品
    for category in MENU.values():
        for item in category:
            if item["id"] == item_id:
                current_cart.append(item)
    return redirect(url_for("index"))

@app.route("/checkout")
def checkout():
    global total_sales
    if current_cart:
        order_total = sum(item["price"] for item in current_cart)
        total_sales += order_total
        # 紀錄訂單內容
        items_names = ", ".join([i["name"] for i in current_cart])
        order_history.append(f"金額: ${order_total} | 內容: {items_names}")
        current_cart.clear() # 清空購物車
        return "<h2>🎉 訂單已成功送出！老闆正在為您準備...</h2><br><a href='/'>回首頁繼續點餐</a>"
    return redirect(url_for("index"))

@app.route("/boss")
def admin():
    return f"""
    <div style="font-family:sans-serif; padding:30px;">
        <h1 style="color:#2c3e50;">💰 老闆管理後台</h1>
        <div style="background:#ff5722; color:white; padding:20px; border-radius:10px; font-size:24px;">
            今日累計營業額：<strong>${total_sales}</strong>
        </div>
        <hr>
        <h3>歷史訂單記錄：</h3>
        <ul style="line-height:2;">
            {"".join([f"<li>{order}</li>" for order in order_history[::-1]])}
        </ul>
        <br>
        <a href="/">回到點餐前台</a>
    </div>
    """

if __name__ == "__main__":
    # 重要：這兩行是為了讓 Render 能夠連線
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
