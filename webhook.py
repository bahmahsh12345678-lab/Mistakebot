import sys
import os
from flask import Flask, request, jsonify
import telebot

from bot_core import (
    MAIN_BOT_TOKEN, ADMIN_ID, create_bot,
    clone_listesi_yukle, clone_listesi_kaydet
)

app = Flask(__name__)

# ============ BOT CACHE ============
_BOT_CACHE = {}


def get_bot(token):
    if token not in _BOT_CACHE:
        _BOT_CACHE[token] = create_bot(token, is_clone=(token != MAIN_BOT_TOKEN))
    return _BOT_CACHE[token]


def process_update(token, update_json):
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


# ============ RESET WEBHOOK (YENİ) ============
@app.route("/resetwebhook", methods=["GET"])
def reset_webhook():
    """Tüm botların webhook'unu siler ve bekleyen update'leri temizler"""
    results = []

    # Ana bot
    try:
        bot = get_bot(MAIN_BOT_TOKEN)
        bot.remove_webhook()
        # Bekleyen update'leri temizle
        bot.delete_webhook(drop_pending_updates=True)
        results.append({"bot": "MAIN", "status": "webhook silindi"})
    except Exception as e:
        results.append({"bot": "MAIN", "error": str(e)})

    # Clone botlar
    for c in clone_listesi_yukle():
        try:
            bot = get_bot(c["token"])
            bot.remove_webhook()
            bot.delete_webhook(drop_pending_updates=True)
            results.append({"bot": c["username"], "status": "webhook silindi"})
        except Exception as e:
            results.append({"bot": c["username"], "error": str(e)})

    return jsonify({
        "ok": True,
        "mesaj": "Tüm webhook'lar temizlendi",
        "results": results
    })


# ============ RESET CLONE (YENİ) ============
@app.route("/resetclone", methods=["GET"])
def reset_clone():
    """Clone listesini tamamen temizler"""
    try:
        clone_listesi_kaydet([])
        return jsonify({
            "ok": True,
            "mesaj": "Clone listesi temizlendi",
            "kalan": 0
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ============ RESET AYARLAR (YENİ) ============
@app.route("/resetayar", methods=["GET"])
def reset_ayar():
    """Ayarları sıfırlar (bakım modu kapalı, varsayılan)"""
    try:
        import os
        from bot_core import AYAR_FILE, DEFAULT_AYARLAR
        if os.path.exists(AYAR_FILE):
            os.remove(AYAR_FILE)
        return jsonify({
            "ok": True,
            "mesaj": "Ayarlar sıfırlandı",
            "ayarlar": DEFAULT_AYARLAR
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


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
