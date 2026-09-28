import sys
import os
from flask import Flask, request, jsonify
import telebot

# bot_core.py aynı klasörde olduğu için sys.path gerekmez
from bot_core import (
    MAIN_BOT_TOKEN, ADMIN_ID, create_bot,
    clone_listesi_yukle
)

app = Flask(__name__)

# ============ BOT CACHE ============
_BOT_CACHE = {}


def get_bot(token):
    """Vercel serverless için bot instance cache"""
    if token not in _BOT_CACHE:
        _BOT_CACHE[token] = create_bot(token, is_clone=(token != MAIN_BOT_TOKEN))
    return _BOT_CACHE[token]


def process_update(token, update_json):
    """Telegram'dan gelen update'i işler"""
    try:
        bot = get_bot(token)
        update = telebot.types.Update.de_json(update_json)
        bot.process_new_updates([update])
        return True
    except Exception as e:
        print(f"[WEBHOOK ERROR] {e}")
        return False


# ============ ANA WEBHOOK ============
@app.route("/webhook/<bot_token>", methods=["POST"])
def webhook_main(bot_token):
    """Her bot için ayrı endpoint"""
    update = request.get_json(force=True)
    if not update:
        return jsonify({"ok": False, "error": "empty"}), 400

    if process_update(bot_token, update):
        return jsonify({"ok": True})
    return jsonify({"ok": False}), 500


# ============ CLONE WEBHOOK ============
@app.route("/clone/<bot_token>", methods=["POST"])
def webhook_clone(bot_token):
    clones = clone_listesi_yukle()
    tokens = [c["token"] for c in clones]

    if bot_token not in tokens and bot_token != MAIN_BOT_TOKEN:
        return jsonify({"ok": False, "error": "unauthorized"}), 403

    update = request.get_json(force=True)
    if not update:
        return jsonify({"ok": False, "error": "empty"}), 400

    if process_update(bot_token, update):
        return jsonify({"ok": True})
    return jsonify({"ok": False}), 500


# ============ SET WEBHOOK ============
@app.route("/setwebhook", methods=["GET"])
def set_webhook():
    """Tüm botlar için webhook'ları ayarlar"""
    base_url = request.host_url.rstrip("/")
    results = []

    # Ana bot
    try:
        bot = get_bot(MAIN_BOT_TOKEN)
        url = f"{base_url}/webhook/{MAIN_BOT_TOKEN}"
        bot.remove_webhook()
        bot.set_webhook(url=url, drop_pending_updates=True)
        results.append({"bot": "MAIN", "url": url, "status": "ok"})
    except Exception as e:
        results.append({"bot": "MAIN", "error": str(e)})

    # Clone botlar
    for c in clone_listesi_yukle():
        try:
            bot = get_bot(c["token"])
            url = f"{base_url}/clone/{c['token']}"
            bot.remove_webhook()
            bot.set_webhook(url=url, drop_pending_updates=True)
            results.append({"bot": c["username"], "url": url, "status": "ok"})
        except Exception as e:
            results.append({"bot": c["username"], "error": str(e)})

    return jsonify({"ok": True, "results": results})


# ============ HEALTH ============
@app.route("/", methods=["GET"])
def health():
    return jsonify({
        "status": "running",
        "admin_id": ADMIN_ID,
        "clone_count": len(clone_listesi_yukle())
    })


# ============ VERCEL HANDLER ============
handler = app
