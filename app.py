from flask import Flask, render_template_string, request, jsonify
import os

app = Flask(__name__)

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
        {"name": "招牌炒泡麵", "price": 70, "can_add": True}, 
        {"name": "起司魂炒泡麵", "price": 75, "can_add": True}, 
        {"name": "椒麻炒泡麵", "price": 75, "can_add": True},
        {"name": "菜脯辣炒泡麵", "price": 75, "can_add": True}, 
        {"name": "經典沙茶炒泡麵", "price": 75, "can_add": True},
        {"name": "蘑菇炒麵", "price": 55, "can_add": True}, 
        {"name": "黑胡椒炒麵", "price": 55, "can_add": True}, 
        {"name": "招牌爆香炒麵", "price": 70, "can_add": True},
        {"name": "起司魂炒麵", "price": 75, "can_add": True}, 
        {"name": "菜脯辣起司炒麵", "price": 75, "can_add": True}, 
        {"name": "經典沙茶炒麵", "price": 75, "can_add": True}
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

cart = []
history = []
total_income = 0

HTML = """
<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>活力晨食點餐系統</title>
    <style>
        body { font-family: sans-serif; background-color: #fdfaf0; color: #444; margin: 0; padding: 10px; padding-bottom: 100px; }
        .header { background: #ffbe00; color: #fff; padding: 20px; text-align: center; border-radius: 0 0 20px 20px; font-size: 22px; font-weight: bold; margin-bottom: 15px; }
        .section-title { background: #5d4037; color: white; padding: 8px 15px; border-radius: 5px; margin-top: 15px; font-size: 16px; }
        .item-card { background: white; padding: 12px; margin: 8px 0; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        .item-info { display: flex; justify-content: space-between; align-items: center; }
        .price { color: #e67e22; font-weight: bold; }
        .add-btn { background: #ffbe00; border: none; padding: 8px 15px; border-radius: 20px; cursor: pointer; font-weight: bold; font-size: 14px; }
        .opt-box { margin-top: 10px; border-top: 1px dashed #eee; padding-top: 10px; display: flex; gap: 5px; flex-wrap: wrap; }
        .opt-btn { background: #eee; border: none; padding: 5px 10px; border-radius: 5px; font-size: 12px; cursor: pointer; }
        .opt-btn.active { background: #4CAF50; color: white; }
        .footer-cart { position: fixed; bottom: 0; left: 0; right: 0; background: #333; color: white; padding: 15px; display: flex; justify-content: space-between; align-items: center; z-index: 100; }
        .checkout-link { background: #ffbe00; color: black; padding: 10px 18px; border-radius: 25px; text-decoration: none; font-weight: bold; font-size: 14px; }
        .msg { position: fixed; top: 20px; left: 50%; transform: translateX(-50%); background: rgba(0,0,0,0.8); color: white; padding: 10px 20px; border-radius: 20px; display: none; z-index: 1000; }
    </style>
    <script>
        function addToCart(name, price, element) {
            let finalName = name;
            let finalPrice = price;
            
            // 檢查有沒有加點選項 (針對泡麵/炒麵)
            if (element) {
                const card = element.closest('.item-card');
                const opts = card.querySelectorAll('.opt-btn.active');
                opts.forEach(opt => {
                    finalName += " + " + opt.dataset.label;
                    finalPrice += parseInt(opt.dataset.price);
                });
            }

            fetch('/add', {
                method: 'POST',
                headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                body: `name=${encodeURIComponent(finalName)}&price=${finalPrice}`
            })
            .then(r => r.json())
            .then(data => {
                document.getElementById('cart-count').innerText = data.count;
                document.getElementById('cart-total').innerText = data.total;
                const msg = document.getElementById('msg-box');
                msg.innerText = finalName + ' 已加入';
                msg.style.display = 'block';
                setTimeout(() => { msg.style.display = 'none'; }, 1000);
            });
        }

        function toggleOpt(btn) {
            btn.classList.toggle('active');
        }
    </script>
</head>
<body>
    <div id="msg-box" class="msg"></div>
    <div class="header">🍳 活力晨食點餐</div>
    
    {% for cat, items in menu.items() %}
    <div class="section-title">{{ cat }}</div>
    {% for item in items %}
    <div class="item-card">
        <div class="item-info">
            <div><strong>{{ item.name }}</strong><br><span class="price">${{ item.price }}</span></div>
            <button class="add-btn" onclick="addToCart('{{ item.name }}', {{ item.price }}, this)">加入 +</button>
        </div>
        
        {% if item.can_add %}
        <div class="opt-box">
            <span style="font-size: 12px; color: #888; width: 100%;">加點選項：</span>
            <button class="opt-btn" data-label="加蛋" data-price="15" onclick="toggleOpt(this)">+蛋 $15</button>
            <button class="opt-btn" data-label="加里肌" data-price="25" onclick="toggleOpt(this)">+里肌 $25</button>
            <button class="opt-btn" data-label="加起司" data-price="15" onclick="toggleOpt(this)">+起司 $15</button>
        </div>
        {% endif %}
    </div>
    {% endfor %}
    {% endfor %}

    <div class="footer-cart">
        <span>已點 <span id="cart-count">{{ cart_len }}</span> 項 | 共 $<span id="cart-total">{{ total }}</span></span>
        <a href="/cart" class="checkout-link">看清單/結帳</a>
    </div>
</body>
</html>
"""

@app.route("/")
def index():
    t = sum(i['price'] for i in cart)
    return render_template_string(HTML, menu=MENU, cart_len=len(cart), total=t)

@app.route("/add", methods=["POST"])
def add():
    name = request.form.get("name")
    price = int(request.form.get("price"))
    cart.append({"name": name, "price": price})
    return jsonify({"count": len(cart), "total": sum(i['price'] for i in cart)})

@app.route("/cart")
def view_cart():
    t = sum(i['price'] for i in cart)
    cart_page = """
    <div style="padding:20px; font-family:sans-serif;">
        <h2>🛒 我的點餐清單</h2>
        {% for i in cart %}
        <div style="display:flex; justify-content:space-between; padding:10px
