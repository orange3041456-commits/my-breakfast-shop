from Flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
import os, secrets, requests, datetime
import pytz
from collections import Counter
import json

app = Flask(__name__)
app.secret_key = "morning_noodle_v28_final"
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax')

BOSS_PASSWORD = "8888" 

# ==========================================
# Menu Data
# ==========================================
NOODLE_SUB = "配料：高麗菜、紅蘿蔔、肉絲、蒜碎、洋蔥、蔥花、玉米"
DRINK_OPTS = ["選紅茶", "選冷泡茶", "換奶茶", "換鮮奶茶"]
DRINK_PRICE_MAP = {"換奶茶": 5, "換鮮奶茶": 15}

MENU_DATA = {
    "吃爽組合 (套餐)": [
        {
            "name": "薯條OR雞塊+飲品", 
            "price": 60, 
            "sub": "請務必選擇品項與飲品", 
            "opts": [["選薯條", "選雞塊"], DRINK_OPTS],
            "price_map": DRINK_PRICE_MAP
        },
        {"name": "肉蛋吐司+紅茶", "price": 60},
        {
            "name": "熱狗(3支)+蛋+飲品", 
            "price": 50, 
            "opts": [DRINK_OPTS],
            "price_map": DRINK_PRICE_MAP
        },
        {
            "name": "草莓肉鬆吐司+飲品", 
            "price": 50, 
            "sub": "🍓 鹹甜推薦", 
            "can_add": True, 
            "opts": [DRINK_OPTS],
            "price_map": DRINK_PRICE_MAP
        },
        {
            "name": "巧克力薯餅吐司+飲品", 
            "price": 50, 
            "sub": "🍫 酥脆組合", 
            "can_add": True, 
            "opts": [DRINK_OPTS],
            "price_map": DRINK_PRICE_MAP
        }
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
        {"name": "招牌炒泡麵", "price": 70, "can_add": True, "add_meat": True, "can_spicy": True, "is_noodle": True, "sub": NOODLE_SUB}, 
        {"name": "起司魂炒泡麵", "price": 75, "can_add": True, "add_meat": True, "can_spicy": True, "is_noodle": True, "sub": NOODLE_SUB},
        {"name": "椒麻炒泡麵", "price": 75, "can_add": True, "add_meat": True, "can_spicy": True, "is_noodle": True, "sub": NOODLE_SUB},
        {"name": "菜脯辣炒泡麵", "price": 75, "can_add": True, "add_meat": True, "can_spicy": True, "is_noodle": True, "sub": NOODLE_SUB},
        {"name": "經典沙茶炒泡麵", "price": 75, "can_add": True, "add_meat": True, "can_spicy": True, "is_noodle": True, "sub": NOODLE_SUB}
    ],
    "炒麵系列 (200g)": [
        {"name": "蘑菇麵", "price": 55, "can_add": True, "add_meat": True, "can_spicy": True, "is_noodle": True, "sub": "無肉絲，附基本配料"},
        {"name": "黑胡椒麵", "price": 55, "can_add": True, "add_meat": True, "can_spicy": True, "is_noodle": True, "sub": "無肉絲，附基本配料"},
        {"name": "招牌爆香炒麵", "price": 70, "can_add": True, "add_meat": True, "can_spicy": True, "is_noodle": True, "sub": NOODLE_SUB}, 
        {"name": "起司魂炒麵", "price": 75, "can_add": True, "add_meat": True, "can_spicy": True, "is_noodle": True, "sub": NOODLE_SUB},
        {"name": "菜脯辣起司炒麵", "price": 75, "can_add": True, "add_meat": True, "can_spicy": True, "is_noodle": True, "sub": NOODLE_SUB},
        {"name": "經典沙茶炒麵", "price": 75, "can_add": True, "add_meat": True, "can_spicy": True, "is_noodle": True, "sub": NOODLE_SUB}
    ],
    "果醬吐司/厚片": [
        {"name": "巧克力吐司", "price": 25, "is_jam": True}, {"name": "巧克力厚片", "price": 30, "is_jam": True},
        {"name": "草莓吐司", "price": 25, "is_jam": True}, {"name": "草莓厚片", "price": 30, "is_jam": True},
        {"name": "花生吐司", "price": 25, "is_jam": True}, {"name": "花生厚片", "price": 30, "is_jam": True},
        {"name": "奶酥吐司", "price": 25, "is_jam": True}, {"name": "奶酥厚片", "price": 30, "is_jam": True}
    ],
    "烤吐司系列": [
        {"name": "煎蛋吐司", "price": 35, "can_add": True, "add_meat": True, "is_simple_toast": True, "sub": "預設無生菜、番茄"},
        {"name": "火腿吐司", "price": 40, "can_add": True, "add_meat": True, "is_toast": True, "sub": "含生菜、番茄"},
        {"name": "培根吐司", "price": 40, "can_add": True, "add_meat": True, "is_toast": True, "sub": "含生菜、番茄"},
        {"name": "麥香雞吐司", "price": 40, "can_add": True, "add_meat": True, "is_toast": True, "sub": "含生菜、番茄"},
        {"name": "鮪魚吐司", "price": 50, "can_add": True, "add_meat": True, "is_toast": True, "sub": "含生菜、番茄"},
        {"name": "薯餅吐司", "price": 40, "can_add": True, "add_meat": True, "is_toast": True, "sub": "含生菜、番茄"},
        {"name": "里肌吐司", "price": 55, "can_add": True, "add_meat": True, "is_toast": True, "sub": "含生菜、番茄"}, 
        {"name": "卡啦雞腿吐司", "price": 60, "can_add": True, "add_meat": True, "is_toast": True, "sub": "含生菜、番茄"}
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
    if tid:
        session['info'] = {"type": "內用", "table": tid}
    elif not session.get('info') or not session['info'].get('type'):
        session['info'] = {"type": "外帶", "table": ""}
    return render_template_string(INDEX_HTML, menu=MENU_DATA, cart_len=len(cart), total=sum(i['price'] for i in cart), table_id=tid, is_boss=is_boss)

# ... (中間路由保持不變)

# --- [ INDEX_HTML 更新重點 ] ---
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
    .sub-info { font-size: 12px; color: #888; margin-top: 2px; }
    .grid { margin-top: 12px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px; border-top: 1px dashed #eee; padding-top: 12px; }
    .opt { background: #fcfcfc; border: 1.5px solid #eee; padding: 8px 3px; border-radius: 8px; font-size: 13px; text-align: center; cursor: pointer; }
    .opt.active { background: #5d4037; color: #fff; border-color: #5d4037; }
    .footer { position: fixed; bottom: 0; left: 0; right: 0; background: #333; color: #fff; padding: 15px; display: flex; justify-content: space-between; align-items: center; z-index: 100; }
</style>
<script>
    let opts={}; let curT="{{session.info.table}}"; let curType="{{session.info.type}}"; let tmr;
    function start(){tmr=setTimeout(()=>{let p=prompt("Password:"); if(p)location.href="/boss?pw="+p},2500)}
    function end(){clearTimeout(tmr)}
    function setT(t,b){curType=t;if(t==='外帶') { curT=''; }fetch('/update_info',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:"type="+t+"&table="+curT});document.querySelectorAll('.type-btn').forEach(x=>x.classList.remove('active'));b.classList.add('active');document.getElementById('ts').style.display=(t==='內用')?'block':'none'}
    function setN(n,b){curT=n;fetch('/update_info',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:"type=內用&table="+n});document.querySelectorAll('.table-btn').forEach(x=>x.classList.remove('active'));b.classList.add('active')}
    
    function buy(n,p,i,hasOpts,pMapStr){
        if(curType==='內用' && !curT){ alert("內用請先選擇桌號"); return; }
        let fn=n, fp=p; let drinkSelected = false;
        let pMap = pMapStr ? JSON.parse(pMapStr) : {};

        Object.keys(opts).forEach(k=>{ 
            if(k.indexOf(i+'_')===0){ 
                let optName = opts[k].n;
                fn+='+'+optName; 
                fp+=opts[k].p; 
                if(pMap[optName]) fp += pMap[optName];
                if(optName.indexOf('選') !== -1 || optName.indexOf('換') !== -1) drinkSelected = true; 
            } 
        });
        if(hasOpts > 0 && !drinkSelected){ alert("請務必選擇飲品"); return; }
        
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
        {% if is_boss %}<a href="/boss?pw=8888" class="boss-back">返回</a>{% endif %}
        晨食麵所
    </div>
    <div class="setup">
        <div style="padding:5px;">用餐方式：
            <button class="btn type-btn {{ 'active' if session.info.type == '外帶' else '' }}" onclick="setT('外帶',this)">外帶</button>
            <button class="btn type-btn {{ 'active' if session.info.type == '內用' else '' }}" onclick="setT('內用',this)">內用</button>
            <div id="ts" style="display:{{ 'block' if session.info.type == '內用' else 'none' }};margin-top:8px">桌號：
                {% for n in range(1,6) %}
                <button class="btn table-btn {{ 'active' if session.info.table == n|string else '' }}" onclick="setN('{{n}}',this)">{{n}}</button>
                {% endfor %}
            </div>
        </div>
    </div>
    {% for cat,items in menu.items() %}
        <div class="title">{{cat}}</div>
        {% for item in items %}
            {% set iid = "id" ~ loop.index ~ cat[0] %}
            {% set has_opts = 1 if item.opts else 0 %}
            <div class="card">
                <div class="row">
                    <div style="flex:1"><strong>{{item.name}}</strong>{% if item.sub %}<div class="sub-info">{{item.sub}}</div>{% endif %}<div class="price">${{item.price}}</div></div>
                    <button class="add" onclick="buy('{{item.name}}',{{item.price}},'{{iid}}',{{has_opts}},'{{item.price_map|tojson if item.price_map else '{}'}}')">加入</button>
                </div>
                <div class="grid">
                    {% if item.can_add %}<div class="opt" data-item="{{iid}}" onclick="tgl('{{iid}}','加蛋',15,this)">+蛋 15</div><div class="opt" data-item="{{iid}}" onclick="tgl('{{iid}}','加起司',15,this)">+起司 15</div>{% endif %}
                    {% if item.add_meat %}<div class="opt" data-item="{{iid}}" onclick="tgl('{{iid}}','加里肌',25,this)">+里肌 25</div>{% endif %}
                    {% if item.is_toast %}<div class="opt" data-item="{{iid}}" onclick="tgl('{{iid}}','不加生菜',0,this)">不生菜</div><div class="opt" data-item="{{iid}}" onclick="tgl('{{iid}}','不加番茄',0,this)">不番茄</div>{% endif %}
                    {% if item.is_toast or item.is_jam or item.is_simple_toast %}<div class="opt" data-item="{{iid}}" onclick="tgl('{{iid}}','酥一點',0,this)">酥一點</div>{% endif %}
                    {% if item.can_spicy %}<div class="opt" data-item="{{iid}}" onclick="tgl('{{iid}}','特製辣',0,this)">特製辣</div>{% endif %}
                    
                    {% if item.is_noodle %}
                    <div class="opt" data-item="{{iid}}" onclick="tgl('{{iid}}','不要配菜',0,this)" style="color:#d35400;font-weight:bold;">❌不要配菜</div>
                    <div class="opt" data-item="{{iid}}" onclick="tgl('{{iid}}','不加高麗菜',0,this)">不加高麗菜</div>
                    <div class="opt" data-item="{{iid}}" onclick="tgl('{{iid}}','不加蔥花',0,this)">不加蔥花</div>
                    <div class="opt" data-item="{{iid}}" onclick="tgl('{{iid}}','不加紅蘿蔔',0,this)">不加紅蘿蔔</div>
                    <div class="opt" data-item="{{iid}}" onclick="tgl('{{iid}}','不加玉米',0,this)">不加玉米</div>
                    {% endif %}

                    {% if item.opts %}
                        {% for group in item.opts %}
                            {% set gidx = loop.index %}
                            {% for o in group %}
                                {# 這裡加入顯示加價的邏輯 #}
                                {% set extra = item.price_map.get(o, 0) if item.price_map else 0 %}
                                <div class="opt" data-item="{{iid}}" data-grp="{{iid}}_{{gidx}}" data-val="{{o}}" onclick="tgl('{{iid}}','{{o}}',0,this,'{{gidx}}')">
                                    {{o}}{% if extra > 0 %} (+{{extra}}){% endif %}
                                </div>
                            {% endfor %}
                        {% endfor %}
                    {% endif %}
                </div>
            </div>
        {% endfor %}
    {% endfor %}
    <div class="footer"><span>已點 <span id="cc">{{cart_len}}</span> 項 | $<span id="ct">{{total}}</span></span><a href="/cart{% if is_boss %}?mode=boss{% endif %}" style="background:#ffbe00;color:#000;padding:8px 20px;border-radius:20px;text-decoration:none;font-weight:bold;">去結帳</a></div>
</body></html>
"""

# ... (後續路由與 HTML 保持不變)
