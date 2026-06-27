"""
Telebirr Bot - PythonAnywhere Version
=======================================
Full automatic merchant checkout flow.

Setup on PythonAnywhere:
1. Upload this file
2. Create a Web App (Flask, Python 3.10)
3. Set source file to this app.py
4. Install: pip install python-telegram-bot==20.7 requests cryptography flask
5. Set your PYTHONANYWHERE_USERNAME below
6. Reload web app

Your webhook URL will be:
  https://YOUR_USERNAME.pythonanywhere.com/telebirr/notify
  https://YOUR_USERNAME.pythonanywhere.com/telegram
"""

import logging
import sqlite3
import re
import requests
import json
import time
import base64
import random
import string
import hashlib
import asyncio
from flask import Flask, request, jsonify
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, ConversationHandler, filters,
)

# ─────────────────────────────────────────────
#  CONFIG — Edit these
# ─────────────────────────────────────────────
BOT_TOKEN             = "8850021596:AAFdzMi_m9K1rEkvjehWVI0z332mBfcPhOo"
ADMIN_IDS             = [969367991]
PYTHONANYWHERE_USERNAME = "Jalud"  # ← Change this!

# Telebirr Credentials
FABRIC_APP_ID    = "c4182ef8-9249-458a-985e-06d191f4d505"
APP_SECRET       = "fad0f06383c6297f545876694b974599"
MERCHANT_CODE    = "101011"
MERCHANT_ID      = "930231098009602"
BASE_URL         = "https://196.188.120.3:38443/apiaccess/payment/gateway"

PRIVATE_KEY_B64  = (
    "MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQC/ZcoOng1sJZ4C"
    "egopQVCw3HYqqVRLEudgT+dDpS8fRVy7zBgqZunju2VRCQuHeWs7yWgc9QGd4/8k"
    "RSLY+jlvKNeZ60yWcqEY+eKyQMmcjOz2Sn41fcVNgF+HV3DGiV4b23B6BCMjnpEF"
    "Ib9d99/TsjsFSc7gCPgfl2yWDxE/Y1B2tVE6op2qd63YsMVFQGdre/CQYvFJENpQ"
    "aBLMq4hHyBDgluUXlF0uA1X7UM0ZjbFC6ZIB/Hn1+pl5Ua8dKYrkVaecolmJT/s7"
    "c/+/1JeN+ja8luBoONsoODt2mTeVJHLF9Y3oh5rI+IY8HukIZJ1U6O7/JcjH3aRJ"
    "TZagXUS9AgMBAAECggEBALBIBx8JcWFfEDZFwuAWeUQ7+VX3mVx/770kOuNx24HY"
    "t718D/HV0avfKETHqOfA7AQnz42EF1Yd7Rux1ZO0e3unSVRJhMO4linT1XjJ9ScM"
    "ISAColWQHk3wY4va/FLPqG7N4L1w3BBtdjIc0A2zRGLNcFDBlxl/CVDHfcqD3CXd"
    "Lukm/friX6TvnrbTyfAFicYgu0+UtDvfxTL3pRL3u3WTkDvnFK5YXhoazLctNOFr"
    "NiiIpCW6dJ7WRYRXuXhz7C0rENHyBtJ0zura1WD5oDbRZ8ON4v1KV4QofWiTFXJp"
    "bDgZdEeJJmFmt5HIi+Ny3P5n31WwZpRMHGeHrV23//0CgYEA+2/gYjYWOW3JgMDL"
    "X7r8fGPTo1ljkOUHuH98H/a/lE3wnnKKx+2ngRNZX4RfvNG4LLeWTz9plxR2RAqq"
    "OTbX8fj/NA/sS4mru9zvzMY1925FcX3WsWKBgKlLryl0vPScq4ejMLSCmypGz4Vg"
    "LMYZqT4NYIkU2Lo1G1MiDoLy0CcCgYEAwt77exynUhM7AlyjhAA2wSINXLKsdFFF"
    "1u976x9kVhOfmbAutfMJPEQWb2WXaOJQMvMpgg2rU5aVsyEcuHsRH/2zatrxrGqL"
    "qgxaiqPz4ELINIh1iYK/hdRpr1vATHoebOv1wt8/9qxITNKtQTgQbqYci3KV1lPs"
    "OrBAB5S57nsCgYAvw+cagS/jpQmcngOEoh8I+mXgKEET64517DIGWHe4kr3dO+FF"
    "bc5eZPCbhqgxVJ3qUM4LK/7BJq/46RXBXLvVSfohR80Z5INtYuFjQ1xJLveeQcuh"
    "UxdK+95W3kdBBi8lHtVPkVsmYvekwK+ukcuaLSGZbzE4otcn47kajKHYDQKBgDbQ"
    "yIbJ+ZsRw8CXVHu2H7DWJlIUBIS3s+CQ/xeVfgDkhjmSIKGX2to0AOeW+S9MseiT"
    "E/L8a1wY+MUppE2UeK26DLUbH24zjlPoI7PqCJjl0DFOzVlACSXZKV1lfsNEeriC"
    "61/EstZtgezyOkAlSCIH4fGr6tAeTU349Bnt0RtvAoGBAObgxjeH6JGpdLz1BbMj"
    "8xUHuYQkbxNeIPhH29CySn0vfhwg9VxAtIoOhvZeCfnsCRTj9OZjepCeUqDiDSoF"
    "znglrKhfeKUndHjvg+9kiae92iI6qJudPCHMNwP8wMSphkxUqnXFR3lr9A765GA9"
    "80818UWZdrhrjLKtIIZdh+X1"
)

PRICE_PER_CREDIT = 10
SERVICE_NAME     = "PDF Download"

# Auto-generated URLs
BASE_WEBHOOK     = f"https://{PYTHONANYWHERE_USERNAME}.pythonanywhere.com"
NOTIFY_URL       = f"{BASE_WEBHOOK}/telebirr/notify"
TELEGRAM_WEBHOOK = f"{BASE_WEBHOOK}/telegram"
# ─────────────────────────────────────────────

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

DB_FILE = '/home/Jalud/mysite/users_database.db'
_token_cache = {"token": None, "expires": 0}
_pending_orders = {}  # merch_order_id → {user_id, amount}


# ══════════════════════════════════════════════
#  DATABASE
# ══════════════════════════════════════════════

def db():
    return sqlite3.connect(DB_FILE)

def init_db():
    with db() as con:
        con.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id    INTEGER PRIMARY KEY,
                username   TEXT,
                full_name  TEXT,
                credits    INTEGER DEFAULT 0,
                total_paid REAL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS used_orders (
                order_id TEXT PRIMARY KEY,
                amount   REAL,
                used_by  INTEGER,
                used_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

def get_or_create_user(user_id, username, full_name):
    with db() as con:
        con.execute(
            "INSERT OR IGNORE INTO users (user_id, username, full_name) VALUES (?,?,?)",
            (user_id, username, full_name)
        )
        row = con.execute(
            "SELECT credits, total_paid FROM users WHERE user_id=?", (user_id,)
        ).fetchone()
    return row or (0, 0.0)

def get_user_stats(user_id):
    with db() as con:
        row = con.execute(
            "SELECT credits, total_paid FROM users WHERE user_id=?", (user_id,)
        ).fetchone()
    return row or (0, 0.0)

def add_credits(user_id, order_id, amount):
    credits = int(amount // PRICE_PER_CREDIT)
    with db() as con:
        con.execute(
            "INSERT OR IGNORE INTO used_orders (order_id, amount, used_by) VALUES (?,?,?)",
            (order_id, amount, user_id)
        )
        con.execute(
            "UPDATE users SET credits=credits+?, total_paid=total_paid+? WHERE user_id=?",
            (credits, amount, user_id)
        )
    return credits


# ══════════════════════════════════════════════
#  SIGNING
# ══════════════════════════════════════════════

def load_private_key():
    pem = "-----BEGIN PRIVATE KEY-----\n"
    key = PRIVATE_KEY_B64
    for i in range(0, len(key), 64):
        pem += key[i:i+64] + "\n"
    pem += "-----END PRIVATE KEY-----"
    return serialization.load_pem_private_key(
        pem.encode(), password=None, backend=default_backend()
    )

def sign_data(data: str) -> str:
    try:
        key = load_private_key()
        sig = key.sign(data.encode('utf-8'), padding.PKCS1v15(), hashes.SHA256())
        return base64.b64encode(sig).decode('utf-8')
    except Exception as e:
        logging.error(f"Sign error: {e}")
        return ""

def random_str(n=32):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=n))

def new_order_id():
    return ''.join(random.choices(string.digits, k=18))


# ══════════════════════════════════════════════
#  TELEBIRR API
# ══════════════════════════════════════════════

def get_token():
    now = time.time()
    if _token_cache["token"] and now < _token_cache["expires"]:
        return _token_cache["token"]
    try:
        resp = requests.post(
            f"{BASE_URL}/payment/v1/token",
            headers={"Content-Type": "application/json", "X-APP-Key": FABRIC_APP_ID},
            json={"appSecret": APP_SECRET},
            verify=False, timeout=10
        )
        token = resp.json().get("token", "")
        if token:
            _token_cache["token"] = token
            _token_cache["expires"] = now + 3500
            return token
    except Exception as e:
        logging.error(f"Token error: {e}")
    return None

def create_order(user_id: int, amount: float, title: str = "Buy Credits"):
    """
    Create a Telebirr payment order.
    Returns (payment_url, merch_order_id) or (None, None)
    """
    token = get_token()
    if not token:
        return None, None

    try:
        order_id  = new_order_id()
        timestamp = str(int(time.time()))
        nonce     = random_str()

        biz = {
            "notify_url":     NOTIFY_URL,
            "business_type":  "BuyGoods",
            "trade_type":     "InApp",
            "appid":          MERCHANT_ID,
            "merch_code":     MERCHANT_CODE,
            "merch_order_id": order_id,
            "title":          title,
            "total_amount":   str(int(amount)),
            "trans_currency": "ETB",
            "timeout_express": "30m",
            "redirect_url":   f"https://t.me/{BOT_TOKEN.split(':')[0]}"
        }

        body = {
            "timestamp":   timestamp,
            "nonce_str":   nonce,
            "method":      "payment.preorder",
            "sign_type":   "SHA256WithRSA",
            "version":     "1.0",
            "biz_content": biz
        }
        body["sign"] = sign_data(json.dumps(biz, separators=(',', ':')))

        resp = requests.post(
            f"{BASE_URL}/payment/v1/merchant/preOrder",
            headers={
                "Content-Type":  "application/json",
                "X-APP-Key":     FABRIC_APP_ID,
                "Authorization": token
            },
            json=body,
            verify=False, timeout=15
        )
        data = resp.json()
        logging.info(f"PreOrder response: {data}")

        if str(data.get("code")) == "0":
            biz_content = data.get("biz_content", {})
            if isinstance(biz_content, str):
                biz_content = json.loads(biz_content)
            prepay_id = biz_content.get("prepay_id", "")
            if prepay_id:
                # Store pending order
                _pending_orders[order_id] = {
                    "user_id": user_id,
                    "amount":  amount
                }
                # Build payment URL
                pay_url = (
                    f"https://developerportal.ethiotelecom.et/checkout"
                    f"?prepay_id={prepay_id}"
                    f"&merch_code={MERCHANT_CODE}"
                )
                return pay_url, order_id
    except Exception as e:
        logging.error(f"CreateOrder error: {e}")
    return None, None


# ══════════════════════════════════════════════
#  TELEGRAM BOT
# ══════════════════════════════════════════════

CHOOSE_AMOUNT = 1

telegram_app = Application.builder().token(BOT_TOKEN).build()
bot = Bot(token=BOT_TOKEN)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    credits, _ = get_or_create_user(user.id, user.username, user.full_name)
    keyboard = [
        [InlineKeyboardButton("💳 Buy Credits (Telebirr)", callback_data="buy")],
        [InlineKeyboardButton("📊 My Account", callback_data="account")],
    ]
    await update.message.reply_text(
        f"👋 Welcome, *{user.full_name}*!\n\n"
        f"📄 Each *{SERVICE_NAME}* costs *{PRICE_PER_CREDIT} ETB*\n"
        f"💰 Your Credits: *{credits}*\n\n"
        "Tap *Buy Credits* to pay via Telebirr.",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def account_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    credits, total_paid = get_user_stats(user.id)
    keyboard = [[InlineKeyboardButton("💳 Buy Credits", callback_data="buy")]]
    await update.effective_message.reply_text(
        f"📊 *Your Account*\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"👤 *{user.full_name}*\n"
        f"💰 Credits: *{credits}*\n"
        f"💵 Total Paid: *{total_paid:.2f} ETB*\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"💡 {PRICE_PER_CREDIT} ETB = 1 {SERVICE_NAME}",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def buy_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()

    keyboard = [
        [InlineKeyboardButton(f"10 ETB (1 credit)",   callback_data="amount_10")],
        [InlineKeyboardButton(f"50 ETB (5 credits)",  callback_data="amount_50")],
        [InlineKeyboardButton(f"100 ETB (10 credits)", callback_data="amount_100")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")],
    ]
    text = (
        f"💳 *Buy Credits via Telebirr*\n\n"
        f"Choose how much to pay:"
    )
    if query:
        await query.edit_message_text(text, parse_mode="Markdown",
                                      reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(text, parse_mode="Markdown",
                                        reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = update.effective_user

    amount = int(query.data.split("_")[1])

    await query.edit_message_text(
        f"⏳ Creating your Telebirr payment link for *{amount} ETB*...",
        parse_mode="Markdown"
    )

    pay_url, order_id = create_order(user.id, amount, f"Buy {amount//PRICE_PER_CREDIT} {SERVICE_NAME}(s)")

    if not pay_url:
        await query.edit_message_text(
            "❌ Could not create payment link. Please try again later.\n"
            "Contact support if this continues."
        )
        return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton("💳 Pay Now on Telebirr", url=pay_url)],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel")],
    ]
    await query.edit_message_text(
        f"✅ *Payment Link Ready!*\n\n"
        f"💰 Amount: *{amount} ETB*\n"
        f"🎁 You will get: *{amount//PRICE_PER_CREDIT} credit(s)*\n\n"
        f"Tap the button below to pay via Telebirr.\n"
        f"Credits will be added *automatically* after payment! ✅",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
        await query.edit_message_text("❌ Cancelled. Send /start to begin again.")
    else:
        await update.message.reply_text("❌ Cancelled.")
    return ConversationHandler.END

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "account":
        await account_cmd(update, context)
    elif query.data == "buy":
        await buy_prompt(update, context)

async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    with db() as con:
        users     = con.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        total_etb = con.execute("SELECT SUM(total_paid) FROM users").fetchone()[0] or 0
        orders    = con.execute("SELECT COUNT(*) FROM used_orders").fetchone()[0]
    await update.message.reply_text(
        f"📊 *Bot Stats*\n"
        f"👥 Users: *{users}*\n"
        f"💵 Total: *{total_etb:.0f} ETB*\n"
        f"✅ Orders: *{orders}*",
        parse_mode="Markdown"
    )

# Register handlers
conv = ConversationHandler(
    entry_points=[
        CallbackQueryHandler(buy_prompt, pattern="^buy$"),
        CallbackQueryHandler(handle_amount, pattern="^amount_"),
    ],
    states={
        CHOOSE_AMOUNT: [
            CallbackQueryHandler(handle_amount, pattern="^amount_"),
            CallbackQueryHandler(cancel, pattern="^cancel$"),
        ]
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)
telegram_app.add_handler(CommandHandler("start",   start))
telegram_app.add_handler(CommandHandler("account", account_cmd))
telegram_app.add_handler(CommandHandler("stats",   admin_stats))
telegram_app.add_handler(CallbackQueryHandler(handle_amount, pattern="^amount_"))
telegram_app.add_handler(CallbackQueryHandler(button_handler))


# ══════════════════════════════════════════════
#  FLASK ROUTES
# ══════════════════════════════════════════════

@app.route("/")
def index():
    return "✅ Bot is running!", 200

@app.route("/telegram", methods=["POST"])
def telegram_webhook():
    """Receive updates from Telegram."""
    try:
        data = request.get_json()
        update = Update.de_json(data, telegram_app.bot)
        asyncio.run(telegram_app.process_update(update))
    except Exception as e:
        logging.error(f"Telegram webhook error: {e}")
    return jsonify({"ok": True})

@app.route("/telebirr/notify", methods=["POST"])
def telebirr_notify():
    """
    Receive payment confirmation from Telebirr.
    Called automatically when user pays!
    """
    try:
        data = request.get_json() or request.form.to_dict()
        logging.info(f"Telebirr notify: {data}")

        biz = data.get("biz_content", {})
        if isinstance(biz, str):
            biz = json.loads(biz)

        order_id     = biz.get("merch_order_id", "")
        trade_status = biz.get("trade_status", "")
        amount       = float(biz.get("total_amount", 0))

        if trade_status in ("TRADE_SUCCESS", "SUCCESS") and order_id in _pending_orders:
            order_info = _pending_orders.pop(order_id)
            user_id    = order_info["user_id"]

            credits_added = add_credits(user_id, order_id, amount)
            credits_now, _ = get_user_stats(user_id)

            # Notify user via Telegram
            asyncio.run(bot.send_message(
                user_id,
                f"✅ *Payment Verified Automatically!*\n\n"
                f"💰 *{amount:.0f} ETB* received\n"
                f"🎁 *{credits_added} {SERVICE_NAME}(s)* added!\n"
                f"📊 Your credits: *{credits_now}*\n\n"
                f"Thank you! 🙏",
                parse_mode="Markdown"
            ))

            # Notify admin
            for admin_id in ADMIN_IDS:
                asyncio.run(bot.send_message(
                    admin_id,
                    f"✅ *Auto Payment*\n"
                    f"Order: `{order_id}`\n"
                    f"Amount: {amount:.0f} ETB\n"
                    f"Credits: {credits_added}\n"
                    f"User ID: {user_id}",
                    parse_mode="Markdown"
                ))

        return jsonify({"code": "0", "msg": "success"})
    except Exception as e:
        logging.error(f"Notify error: {e}")
        return jsonify({"code": "1", "msg": str(e)})

@app.route("/setup", methods=["GET"])
def setup_webhook():
    """Visit this URL once to set up Telegram webhook."""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
        resp = requests.post(url, json={"url": TELEGRAM_WEBHOOK})
        return jsonify(resp.json())
    except Exception as e:
        return str(e), 500


# ══════════════════════════════════════════════
#  STARTUP
# ══════════════════════════════════════════════

import urllib3
urllib3.disable_warnings()
init_db()

if __name__ == "__main__":
    app.run(debug=False)
