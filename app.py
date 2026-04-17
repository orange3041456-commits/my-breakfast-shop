from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
import os
import secrets
from collections import Counter
from datetime import datetime

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax')

# --- 密碼設定 ---
BOSS_PASSWORD = "8888" 

# --- 完整菜單資料 ---
MENU_DATA = {
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
    "泡麵系列 (2包泡麵)": [
        {"name": "招牌炒泡麵", "price": 70, "can_add": True}, {"name": "起司魂炒泡麵", "price": 75, "can_add": True}, 
        {"name": "椒麻炒泡麵", "price": 75, "can_add": True}, {"name": "菜脯辣炒泡麵", "price": 75, "can_add": True}, 
        {"name": "經典沙茶炒泡麵", "price": 75, "can_add": True}
    ],
    "炒麵系列 (200G)": [
        {"name": "蘑菇炒麵", "price": 55, "can_add": True}, {"name": "黑胡椒炒麵", "price": 55, "can_add": True}, 
        {"name": "招牌爆香炒麵", "price": 70, "can_add": True}, {"name": "起司魂炒麵", "price": 75, "can_add": True}, 
        {"name": "菜脯辣起司炒麵", "price": 75, "can_add": True}, {"name": "經典沙茶炒麵", "price": 75, "can_add": True}
    ],
    "果醬吐司/厚片": [
        {"name": "巧克力吐司", "price": 25}, {"name": "巧克力厚片", "price": 30}, {"name": "草莓吐司", "price": 25}, 
        {"name": "草莓厚片", "price": 30}, {"name": "花生吐司", "price": 25}, {"name": "花生厚片", "price": 30}, 
        {"name": "奶酥吐司", "price": 25}, {"name": "奶酥厚片", "price": 30}
    ],
    "烤吐司系列": [
        {"name": "煎蛋吐司", "price": 35, "can_add": True, "no_veg": False}, 
        {"name": "火腿吐司 (有生菜、番茄)", "price": 40, "can_add": True, "no_veg": True}, 
        {"name": "培根吐司 (有生菜、番茄)", "price": 40, "can_add": True, "no_veg": True}, 
        {"name": "麥香雞吐司 (有生菜、番茄)", "price": 40, "can_add": True, "no_veg": True}, 
        {"name": "鮪魚吐司 (有生菜、番茄)", "price": 50, "can_add": True, "no_veg": True}, 
        {"name": "薯餅吐司 (有生菜、番茄)", "price": 40, "can_add": True, "no_veg": True},
        {"name": "漢堡排吐司 (有生菜、番茄)", "price": 45, "can_add": True, "no_veg": True}, 
        {"name": "里肌吐司 (有生菜、番茄)", "price": 55, "can_add": True, "no_veg": True}, 
        {"name": "卡啦雞腿吐司 (有生菜、番茄)", "price": 60, "can_add": True, "no_veg": True}, 
        {"name": "厚牛吐司 (有生菜、番茄)", "price": 60, "can_add": True, "no_veg": True}
    ],
    "單點小點": [
        {"name": "荷包蛋", "price": 15}, {"name": "玉米蛋", "price": 35}, {"name": "蔥蛋", "price": 25},
        {"name": "熱狗(3支)", "price": 20}, {"name": "薯餅", "price": 25}, {"name": "麥克雞塊", "price": 45},
        {"name": "小肉豆", "price": 40}, {"name":
