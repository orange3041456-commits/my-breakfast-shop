from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)

# --- 完整菜單資料庫 ---
MENU = {
    "蛋餅類": [
        {"id": 1, "name": "原味蛋餅", "price": 30}, {"id": 2, "name": "蔥香蛋餅", "price": 35},
        {"id": 3, "name": "肉鬆蛋餅", "price": 40}, {"id": 4, "name": "起司/牽絲蛋餅", "price": 40},
        {"id": 5, "name": "蔬菜蛋餅", "price": 40}, {"id": 6, "name": "火腿蛋餅", "price": 40},
        {"id": 7, "name": "香煎培根蛋餅", "price": 40}, {"id": 8, "name": "熱狗蛋餅", "price": 40},
        {"id": 9, "name": "塔香蛋餅", "price": 40}, {"id": 10, "name": "玉米蛋餅", "price": 40},
        {"id": 11, "name": "酥脆薯餅蛋餅", "price": 45}, {"id": 12, "name": "漢堡排蛋餅", "price": 45},
        {"id": 13, "name": "特調鮪魚蛋餅", "price": 50}, {"id": 14, "name": "里肌肉蛋餅", "price": 50},
        {"id": 15, "name": "厚切牛肉蛋餅", "price": 60}, {"id": 16, "name": "辣菜脯里肌蛋餅", "price": 65}
    ],
    "果醬/烤土司": [
        {"id": 17, "name": "巧克力吐司", "price": 25}, {"id": 18, "name": "巧克力厚片", "price": 30},
        {"id": 19, "name": "草莓吐司", "price": 25}, {"id": 20, "name": "草莓厚片", "price": 30},
        {"id": 21, "name": "花生吐司", "price": 25}, {"id": 22, "name": "花生厚片", "price": 30},
        {"id": 23, "name": "奶酥吐司", "price": 25}, {"id": 24, "name": "奶酥厚片", "price": 30},
        {"id": 25, "name": "煎蛋吐司", "price": 35}, {"id": 26, "name": "麥香雞吐司", "price": 40},
        {"id": 27, "name": "火腿吐司", "price": 40}, {"id": 28, "name": "培根吐司", "price": 40},
        {"id": 29, "name": "薯餅吐司", "price": 40}, {"id": 30, "name": "漢堡排吐司", "price": 45},
        {"id": 31, "name": "鮪魚吐司", "price": 50}, {"id": 32, "name": "里肌吐司", "price": 55},
        {"id": 33, "name": "卡啦雞腿吐司", "price": 60}, {"id": 34, "name": "厚牛吐司", "price": 60}
    ],
    "麵類/單點": [
        {"id": 35, "name": "招牌炒泡麵", "price": 70}, {"id": 36, "name": "起司魂炒泡麵", "price": 75},
        {"id": 37, "name": "椒麻炒泡麵", "price": 75}, {"id": 38, "name": "蘑菇麵", "price": 55},
        {"id": 39, "name": "黑胡椒麵", "price": 55}, {"id": 40, "name": "荷包蛋", "price": 15},
        {"id": 41, "name": "蔥蛋", "price": 25}, {"id": 42, "name": "薯餅", "price": 25},
        {"id": 43, "name": "小肉豆", "price": 40}, {"id": 44, "name": "港式蘿蔔糕", "price": 35}
    ],
    "飲品(L)": [
        {"id": 45, "name": "紅茶", "price": 25}, {"id": 46, "name": "香醇奶茶", "price": 30},
        {"id": 47, "name": "無糖豆漿", "price": 35}, {"id": 48, "name": "鮮奶茶", "price": 45}
    ],
    "套餐": [
        {"id": 49, "name": "熱狗+蛋+飲品", "price": 50},
        {"id": 50, "name": "肉蛋土司+紅茶", "price": 60},
        {"id": 51, "name": "蘿蔔糕蔥蛋+飲品", "price": 60},
        {"id": 52, "name": "花生培根厚牛+飲品", "price": 100}
    ]
}

orders = []

def get_item_by_id(item_id):
    for cat in MENU.values():
        for item in cat:
            if item["id"] == item_id: return item
    return None

BASE_HTML = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
    body { font-family: sans-serif; margin: 0; display: flex; height: 100vh; background: #f8f9fa; }
    .sidebar { width: 85px; background: #fff; border-right: 1px solid #ddd; display: flex; flex-direction: column; overflow-y: auto; }
    .sidebar a { padding: 15px 5px; text-align: center; text-decoration: none; color: #555; font-size: 12px; border-bottom: 1px solid #eee; }
    .main { flex: 1; overflow-y: auto; padding: 15px; padding-bottom: 100px; }
    .cat-title { background: #eee; padding: 5px 10px; font-weight: bold; margin: 10px 0; border-radius: 4px; }
    .food-card { background: #fff; padding: 12px; margin-bottom: 8px; border-radius: 10px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    .add-btn { background: #ffbe00; border: none; width: 30px; height: 30px; border-radius: 50%; font-weight: bold; cursor: pointer; }
    .cart-bar { position: fixed; bottom: 0; width: 100%; background: #333; color: white; padding: 15px; display: flex; justify-content: space-between; align-items: center; }
    .checkout-btn { background: #ffbe00; color: black; padding: 8px 20px; border-radius: 20px; text-decoration: none; font-weight: bold; }
</style></head>
<body>
    {% if page == 'menu' %}
    <div class="sidebar">
        {% for cat in menu_data.keys() %}<a href="#{{ cat }}">{{ cat }}</a>{% endfor %}
    </div>
    <div class="main">
        <h2 style="color:#ffbe00; margin-top:0;">活力晨食店 🍳</h2>
        {% for cat, items in menu_data.items() %}
        <div id="{{ cat }}" class="cat-title">{{ cat }}</div>
        {% for item in items %}
        <div class="food-card">
            <div><b>{{ item.name }}</b><br><span style="color:orange;">${{ item.price }}</span></div>
            <form method="POST" action="/add"><input type="hidden" name="id" value="{{ item.id }}"><button class="add-btn">+</button></form>
        </div>
        {% endfor %}{% endfor %}
    </div>
    <div class="cart-bar">
        <span>已點 {{ count }} 份</span><span style="font-size: 1.2em;">${{ total }}</span>
        <a href="/cart" class="checkout-btn">選好了</a>
    </div>
    {% elif page == 'cart' %}
    <div style="padding:20px; width:100%; background:white; min-height:100vh;">
        <h2>🛒 確認訂單</h2>
        {% for idx, item in cart_items %}
        <div style="display:flex; justify-content:space-between; padding:10px 0; border-bottom:1px solid #eee;">
            <span>{{ item.name }}</span><span>${{ item.price }} <a href="/del/{{ idx }}" style="color:red; margin-left:10px;">移除</a></span>
        </div>
        {% endfor %}
        <h3 style="text-align:right; margin-top:20px;">總計: ${{ total }}</h3>
        <div style="margin-top:30px; display:flex; gap:10px;">
            <a href="/" style="flex:1; text-align:center; background:#ddd; padding:15px; text-decoration:none; color:black; border-radius:10px;">回菜單</a>
            <a href="/clear" style="flex:1; text-align:center; background:#ffbe00; padding:15px; text-decoration:none; color:black; border-radius:10px; font-weight:bold;">送出訂單</a>
        </div>
    </div>
    {% endif %}
</body></html>
"""

@app.route("/")
def index():
    t = sum(i["price"] for i in orders)
    return render_template_string(BASE_HTML, page='menu', menu_data=MENU, total=t, count=len(orders))

@app.route("/add", methods=["POST"])
def add():
    item = get_item_by_id(int(request.form.get("id")))
    if item: orders.append(item)
    return redirect(url_for("index"))

@app.route("/cart")
def cart():
    t = sum(i["price"] for i in orders)
    return render_template_string(BASE_HTML, page='cart', cart_items=list(enumerate(orders)), total=t)

@app.route("/del/<int:idx>")
def delete(idx):
    if 0 <= idx < len(orders): orders.pop(idx)
    return redirect(url_for("cart"))

@app.route("/clear")
def clear():
    orders.clear()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
