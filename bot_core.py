import telebot
import requests
import json
import os
from datetime import datetime
from telebot import types

# ============ AYARLAR ============
API_BASE = "https://logsuzlarsystem.iceiy.com/sorgu"
ADMIN_ID = 8727961464
MAIN_BOT_TOKEN = "8846795660:AAEoeH4K-5BMjZMQCTYvoswICQRCcDJBIko"

# Vercel'de /tmp yazılabilir
DATA_DIR = "/tmp/sorgu_bot_data"
os.makedirs(DATA_DIR, exist_ok=True)

AYAR_FILE = f"{DATA_DIR}/ayarlar.json"
KULLANICI_FILE = f"{DATA_DIR}/kullanicilar.txt"
CLONE_FILE = f"{DATA_DIR}/clones.json"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_6) AppleWebKit/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
]

DEFAULT_AYARLAR = {
    "bakim_modu": False,
    "bakim_mesaji": "🔧 Bot şu anda bakımda. Lütfen daha sonra tekrar deneyin.",
    "son_duyuru": "",
    "versiyon": "2.0.0",
    "son_yenileme": "2025-01-01 00:00:00"
}


# ============ AYAR SİSTEMİ ============
def ayarlari_yukle():
    if os.path.exists(AYAR_FILE):
        try:
            with open(AYAR_FILE, "r", encoding="utf-8") as f:
                return {**DEFAULT_AYARLAR, **json.load(f)}
        except:
            pass
    return DEFAULT_AYARLAR.copy()


def ayarlari_kaydet(ayarlar):
    try:
        with open(AYAR_FILE, "w", encoding="utf-8") as f:
            json.dump(ayarlar, f, ensure_ascii=False, indent=2)
    except:
        pass


# ============ KULLANICI YÖNETİMİ ============
def kullanicilari_yukle():
    kullanicilar = {}
    if os.path.exists(KULLANICI_FILE):
        with open(KULLANICI_FILE, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    uid, uname, ad, tarih = line.strip().split("|")
                    kullanicilar[uid] = {"username": uname, "ad": ad, "tarih": tarih}
                except:
                    pass
    return kullanicilar


def kullanici_kaydet(user_id, username, ad):
    kullanicilar = kullanicilari_yukle()
    if str(user_id) not in kullanicilar:
        with open(KULLANICI_FILE, "a", encoding="utf-8") as f:
            f.write(f"{user_id}|{username}|{ad}|{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        return True
    return False


# ============ API İSTEK ============
def api_istek(url):
    try:
        headers = {"User-Agent": USER_AGENTS[hash(url) % len(USER_AGENTS)]}
        r = requests.get(url, timeout=20, headers=headers)
        try:
            return r.json()
        except:
            return {"success": False, "raw": r.text[:2000]}
    except Exception as e:
        return {"success": False, "message": f"API hatası: {str(e)}"}


def json_to_text(baslik, data):
    """JSON veriyi okunabilir metne çevirir"""
    metin = f"📌 *{baslik}*\n"
    metin += f"🕐 `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`\n"
    metin += "─" * 30 + "\n\n"

    def format_dict(d, indent=0):
        s = ""
        prefix = "  " * indent
        if isinstance(d, dict):
            for k, v in d.items():
                if isinstance(v, (dict, list)):
                    s += f"{prefix}• *{k}:*\n{format_dict(v, indent + 1)}"
                else:
                    s += f"{prefix}• *{k}:* `{v}`\n"
        elif isinstance(d, list):
            for i, item in enumerate(d):
                s += f"{prefix}[{i + 1}] {format_dict(item, indent + 1)}"
        else:
            s += f"{prefix}{d}\n"
        return s

    metin += format_dict(data)
    return metin


# ============ MENÜLER ============
def ana_menu(user_id, is_clone=False):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("📇 TC Sorgu", callback_data="menu_tc"),
        types.InlineKeyboardButton("📋 TC Pro", callback_data="menu_tcpro"),
    )
    kb.add(
        types.InlineKeyboardButton("👤 Ad Soyad", callback_data="menu_adsoyad"),
        types.InlineKeyboardButton("👪 Aile", callback_data="menu_aile"),
    )
    kb.add(
        types.InlineKeyboardButton("👨‍👩‍👧‍👦 Aile Pro", callback_data="menu_ailepro"),
        types.InlineKeyboardButton("🌳 Sülale", callback_data="menu_sulale"),
    )
    kb.add(
        types.InlineKeyboardButton("🏢 İşyeri", callback_data="menu_isyeri"),
        types.InlineKeyboardButton("📞 TC→GSM", callback_data="menu_tcgsm"),
    )
    kb.add(
        types.InlineKeyboardButton("📱 GSM→TC", callback_data="menu_gsmtc"),
        types.InlineKeyboardButton("🎓 E-Okul", callback_data="menu_eokul"),
    )
    kb.add(
        types.InlineKeyboardButton("🏠 Adres", callback_data="menu_adres"),
        types.InlineKeyboardButton("📜 Tapu", callback_data="menu_tapu"),
    )
    kb.add(types.InlineKeyboardButton("🗺️ Ada Parsel", callback_data="menu_adaparsel"))
    kb.add(types.InlineKeyboardButton("ℹ️ Hakkında", callback_data="menu_hakkinda"))

    if user_id == ADMIN_ID and not is_clone:
        kb.add(types.InlineKeyboardButton("👑 ADMİN PANEL", callback_data="admin_panel"))

    return kb


def admin_menu(ayarlar):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("📢 Duyuru", callback_data="admin_duyuru"),
        types.InlineKeyboardButton("📊 İstatistik", callback_data="admin_stats"),
    )
    kb.add(
        types.InlineKeyboardButton(
            "🟢 Bakım AÇ" if not ayarlar["bakim_modu"] else "🔴 Bakım KAPAT",
            callback_data="admin_bakim"
        ),
        types.InlineKeyboardButton("✏️ Bakım Mesajı", callback_data="admin_bakim_mesaj"),
    )
    kb.add(
        types.InlineKeyboardButton("🔄 Yenile Bildir", callback_data="admin_yenile"),
        types.InlineKeyboardButton("🤖 Clone Yönet", callback_data="admin_clone"),
    )
    kb.add(types.InlineKeyboardButton("🔙 Geri", callback_data="menu_geri"))
    return kb


def clone_menu():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("➕ Yeni Clone Ekle", callback_data="clone_add"))
    kb.add(types.InlineKeyboardButton("📋 Clone Listesi", callback_data="clone_list"))
    kb.add(types.InlineKeyboardButton("🗑️ Clone Sil", callback_data="clone_del"))
    kb.add(types.InlineKeyboardButton("🔙 Geri", callback_data="admin_panel"))
    return kb


# ============ SORGU MENÜLERİ ============
SORGU_MENU = {
    "menu_tc": ("📇 *TC Sorgu*\n\nTC kimlik numarasını yazın (11 hane):", "tc"),
    "menu_tcpro": ("📋 *TC Pro Sorgu*\n\nTC kimlik numarasını yazın:", "tcpro"),
    "menu_adsoyad": ("👤 *Ad Soyad Sorgu*\n\n`AD SOYAD` şeklinde yazın (örn: `ROKET ATAR`)", "adsoyad"),
    "menu_aile": ("👪 *Aile Sorgu*\n\nTC kimlik numarasını yazın:", "aile"),
    "menu_ailepro": ("👨‍👩‍👧‍👦 *Aile Pro Sorgu*\n\nTC kimlik numarasını yazın:", "ailepro"),
    "menu_sulale": ("🌳 *Sülale Sorgu*\n\nTC kimlik numarasını yazın:", "sulale"),
    "menu_isyeri": ("🏢 *İşyeri Sorgu*\n\nTC kimlik numarasını yazın:", "isyeri"),
    "menu_tcgsm": ("📞 *TC → GSM Sorgu*\n\nTC kimlik numarasını yazın:", "tcgsm"),
    "menu_gsmtc": ("📱 *GSM → TC Sorgu*\n\nGSM numarasını yazın (örn: 5550000000):", "gsmtc"),
    "menu_eokul": ("🎓 *E-Okul Sorgu*\n\nTC kimlik numarasını yazın:", "eokul"),
    "menu_adres": ("🏠 *Adres Sorgu*\n\nTC kimlik numarasını yazın:", "adres"),
    "menu_tapu": ("📜 *Tapu Sorgu*\n\nTC kimlik numarasını yazın:", "tapu"),
    "menu_adaparsel": ("🗺️ *Ada Parsel Sorgu*\n\n`İL İLÇE` şeklinde yazın (örn: `İSTANBUL KADIKÖY`)", "adaparsel"),
}


def sorgu_url_uret(tip, text):
    if tip == "tc":
        return f"{API_BASE}/tc.php?tc={text}", f"TC Sorgu: {text}"
    elif tip == "tcpro":
        return f"{API_BASE}/tcpro.php?tc={text}", f"TC Pro: {text}"
    elif tip == "adsoyad":
        p = text.split()
        if len(p) < 2:
            return None, "❌ `AD SOYAD` şeklinde yazın!"
        return f"{API_BASE}/adsoyad.php?ad={p[0]}&soyad={p[1]}", f"Ad Soyad: {p[0]} {p[1]}"
    elif tip == "aile":
        return f"{API_BASE}/aile.php?tc={text}", f"Aile: {text}"
    elif tip == "ailepro":
        return f"{API_BASE}/ailepro.php?tc={text}", f"Aile Pro: {text}"
    elif tip == "sulale":
        return f"{API_BASE}/sulale.php?tc={text}", f"Sülale: {text}"
    elif tip == "isyeri":
        return f"{API_BASE}/isyeri.php?tc={text}", f"İşyeri: {text}"
    elif tip == "tcgsm":
        return f"{API_BASE}/tcgsm.php?tc={text}", f"TC→GSM: {text}"
    elif tip == "gsmtc":
        return f"{API_BASE}/gsmtc.php?gsm={text}", f"GSM→TC: {text}"
    elif tip == "eokul":
        return f"{API_BASE}/eokul.php?tc={text}", f"E-Okul: {text}"
    elif tip == "adres":
        return f"{API_BASE}/adres.php?tc={text}", f"Adres: {text}"
    elif tip == "tapu":
        return f"{API_BASE}/tapu.php?tc={text}", f"Tapu: {text}"
    elif tip == "adaparsel":
        p = text.split()
        if len(p) < 2:
            return None, "❌ `İL İLÇE` şeklinde yazın!"
        return f"{API_BASE}/adaparsel.php?il={p[0]}&ilce={p[1]}", f"Ada Parsel: {p[0]} {p[1]}"
    return None, "❌ Bilinmeyen sorgu tipi"


# ============ BOT OLUŞTUR ============
def create_bot(token, is_clone=False):
    """Her token için ayrı bot instance oluşturur - sanal ortamda çalışır"""
    bot = telebot.TeleBot(token, threaded=False, parse_mode=None)

    # ---- START ----
    @bot.message_handler(commands=['start'])
    def start(message):
        a = ayarlari_yukle()
        if a["bakim_modu"] and message.from_user.id != ADMIN_ID:
            bot.send_message(message.chat.id, f"🔧 *BAKIM MODU*\n\n{a['bakim_mesaji']}", parse_mode="Markdown")
            return
        kullanici_kaydet(
            message.from_user.id,
            message.from_user.username or "yok",
            message.from_user.first_name or "İsimsiz"
        )
        mesaj = (
            f"👋 *Hoş geldin {message.from_user.first_name}!*\n\n"
            f"🔍 Gelişmiş Sorgu Botu\n"
            f"📌 Versiyon: `{a['versiyon']}`\n\n"
            f"Aşağıdaki butonlardan sorgu yapabilirsin 👇"
        )
        bot.send_message(message.chat.id, mesaj, parse_mode="Markdown",
                         reply_markup=ana_menu(message.from_user.id, is_clone))

    # ---- ADMIN ----
    @bot.message_handler(commands=['admin'])
    def admin_cmd(message):
        if message.from_user.id != ADMIN_ID:
            bot.reply_to(message, "❌ Bu komut sadece admin içindir.")
            return
        a = ayarlari_yukle()
        bot.send_message(message.chat.id, "👑 *ADMİN PANEL*\n\nİşlem seçin:",
                         parse_mode="Markdown", reply_markup=admin_menu(a))

    # ---- CALLBACK ----
    @bot.callback_query_handler(func=lambda call: True)
    def callback_handler(call):
        uid = call.from_user.id
        data = call.data
        a = ayarlari_yukle()

        if a["bakim_modu"] and uid != ADMIN_ID and not data.startswith(("menu_", "admin_")):
            bot.answer_callback_query(call.id, "🔧 Bot bakımda!")
            return

        # Menü geri
        if data == "menu_geri":
            bot.edit_message_text("👋 *Ana Menü*\n\nSorgu seçin:",
                                  call.message.chat.id, call.message.message_id,
                                  parse_mode="Markdown",
                                  reply_markup=ana_menu(uid, is_clone))
            return

        if data == "menu_hakkinda":
            metin = (
                "ℹ️ *Hakkında*\n\n"
                f"🤖 Bot: Gelişmiş Sorgu Botu\n"
                f"📌 Versiyon: `{a['versiyon']}`\n"
                f"🌐 API: `{API_BASE}`\n\n"
                "Bu bot eğitim amaçlıdır."
            )
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("🔙 Geri", callback_data="menu_geri"))
            bot.edit_message_text(metin, call.message.chat.id, call.message.message_id,
                                  parse_mode="Markdown", reply_markup=kb)
            return

        # Sorgu menüleri
        if data in SORGU_MENU:
            metin, tip = SORGU_MENU[data]
            bot.delete_message(call.message.chat.id, call.message.message_id)
            msg = bot.send_message(call.message.chat.id, metin, parse_mode="Markdown")
            bot.register_next_step_handler(msg, sorgu_isle, tip)
            return

        # ===== ADMİN =====
        if data == "admin_panel":
            if uid != ADMIN_ID:
                bot.answer_callback_query(call.id, "❌ Yetkiniz yok!")
                return
            bot.edit_message_text("👑 *ADMİN PANEL*\n\nİşlem seçin:",
                                  call.message.chat.id, call.message.message_id,
                                  parse_mode="Markdown", reply_markup=admin_menu(a))
            return

        if data == "admin_duyuru":
            if uid != ADMIN_ID: return
            bot.delete_message(call.message.chat.id, call.message.message_id)
            msg = bot.send_message(call.message.chat.id, "📢 *Duyuru metnini yazın:*\n\n_(İptal için /iptal)_",
                                   parse_mode="Markdown")
            bot.register_next_step_handler(msg, duyuru_gonder)
            return

        if data == "admin_stats":
            if uid != ADMIN_ID: return
            kullanicilar = kullanicilari_yukle()
            clones = clone_listesi_yukle()
            metin = (
                f"📊 *İSTATİSTİKLER*\n\n"
                f"👥 Toplam Kullanıcı: `{len(kullanicilar)}`\n"
                f"🤖 Clone Bot Sayısı: `{len(clones)}`\n"
                f"🔧 Bakım Modu: `{'AÇIK 🟢' if a['bakim_modu'] else 'KAPALI 🔴'}`\n"
                f"📌 Versiyon: `{a['versiyon']}`\n"
                f"🕐 Son Yenileme: `{a['son_yenileme']}`\n"
            )
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("🔙 Geri", callback_data="admin_panel"))
            bot.edit_message_text(metin, call.message.chat.id, call.message.message_id,
                                  parse_mode="Markdown", reply_markup=kb)
            return

        if data == "admin_bakim":
            if uid != ADMIN_ID: return
            a["bakim_modu"] = not a["bakim_modu"]
            ayarlari_kaydet(a)
            bot.answer_callback_query(call.id,
                                      f"Bakım {'AÇILDI 🟢' if a['bakim_modu'] else 'KAPATILDI 🔴'}")
            bot.edit_message_text("👑 *ADMİN PANEL*\n\nİşlem seçin:",
                                  call.message.chat.id, call.message.message_id,
                                  parse_mode="Markdown", reply_markup=admin_menu(a))
            return

        if data == "admin_bakim_mesaj":
            if uid != ADMIN_ID: return
            bot.delete_message(call.message.chat.id, call.message.message_id)
            msg = bot.send_message(call.message.chat.id, "✏️ *Yeni bakım mesajını yazın:*",
                                   parse_mode="Markdown")
            bot.register_next_step_handler(msg, bakim_mesaj_kaydet)
            return

        if data == "admin_yenile":
            if uid != ADMIN_ID: return
            bot.answer_callback_query(call.id, "🔄 Bildirim gönderiliyor...")
            yenileme_bildirimi(bot)
            return

        if data == "admin_clone":
            if uid != ADMIN_ID: return
            bot.edit_message_text("🤖 *CLONE YÖNETİMİ*\n\nİşlem seçin:",
                                  call.message.chat.id, call.message.message_id,
                                  parse_mode="Markdown", reply_markup=clone_menu())
            return

        if data == "clone_add":
            if uid != ADMIN_ID: return
            bot.delete_message(call.message.chat.id, call.message.message_id)
            msg = bot.send_message(
                call.message.chat.id,
                "🤖 *Yeni Clone Bot Token'ı Gönderin:*\n\n"
                "_(BotFather'dan alacağınız token. İptal için /iptal)_",
                parse_mode="Markdown"
            )
            bot.register_next_step_handler(msg, clone_ekle)
            return

        if data == "clone_list":
            if uid != ADMIN_ID: return
            clones = clone_listesi_yukle()
            if not clones:
                metin = "📋 *Clone Listesi*\n\nHenüz clone bot eklenmemiş."
            else:
                metin = "📋 *Clone Listesi*\n\n"
                for i, c in enumerate(clones, 1):
                    metin += f"{i}. `{c['token'][:15]}...` \n   👤 @{c.get('username', 'yok')}\n\n"
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("🔙 Geri", callback_data="admin_clone"))
            bot.edit_message_text(metin, call.message.chat.id, call.message.message_id,
                                  parse_mode="Markdown", reply_markup=kb)
            return

        if data == "clone_del":
            if uid != ADMIN_ID: return
            bot.delete_message(call.message.chat.id, call.message.message_id)
            msg = bot.send_message(call.message.chat.id, "🗑️ *Silinecek token'ı gönderin:*",
                                   parse_mode="Markdown")
            bot.register_next_step_handler(msg, clone_sil)
            return

    # ---- SORGU İŞLE ----
    def sorgu_isle(message, tip):
        a = ayarlari_yukle()
        if a["bakim_modu"] and message.from_user.id != ADMIN_ID:
            bot.reply_to(message, f"🔧 {a['bakim_mesaji']}")
            return

        text = message.text.strip()
        url, baslik = sorgu_url_uret(tip, text)

        if not url:
            bot.reply_to(message, baslik, parse_mode="Markdown")
            return

        islem = bot.reply_to(message, "🔍 Sorgulanıyor...")

        try:
            data = api_istek(url)
            metin = json_to_text(baslik, data)

            # Mesaj çok uzunsa parçala
            if len(metin) > 4000:
                parcalar = [metin[i:i + 4000] for i in range(0, len(metin), 4000)]
                bot.delete_message(message.chat.id, islem.message_id)
                for p in parcalar:
                    try:
                        bot.send_message(message.chat.id, p, parse_mode="Markdown")
                    except:
                        bot.send_message(message.chat.id, p)
            else:
                bot.edit_message_text(metin, message.chat.id, islem.message_id,
                                      parse_mode="Markdown")

        except Exception as e:
            bot.edit_message_text(f"❌ Hata: {str(e)}",
                                  message.chat.id, islem.message_id)

    # ---- ADMİN İŞLEMLERİ ----
    def duyuru_gonder(message):
        if message.from_user.id != ADMIN_ID: return
        if message.text == "/iptal":
            bot.reply_to(message, "❌ İptal edildi.")
            return
        a = ayarlari_yukle()
        a["son_duyuru"] = message.text
        ayarlari_kaydet(a)

        kullanicilar = kullanicilari_yukle()
        basarili, hatali = 0, 0
        durum = bot.reply_to(message, f"📢 Gönderiliyor... (0/{len(kullanicilar)})")

        for i, uid_k in enumerate(kullanicilar.keys()):
            try:
                bot.send_message(uid_k, f"📢 *DUYURU*\n\n{message.text}", parse_mode="Markdown")
                basarili += 1
            except:
                hatali += 1

        bot.edit_message_text(
            f"✅ *Duyuru Tamamlandı*\n\n✅ Başarılı: `{basarili}`\n❌ Hatalı: `{hatali}`",
            durum.chat.id, durum.message_id, parse_mode="Markdown"
        )

    def bakim_mesaj_kaydet(message):
        if message.from_user.id != ADMIN_ID: return
        a = ayarlari_yukle()
        a["bakim_mesaji"] = message.text
        ayarlari_kaydet(a)
        bot.reply_to(message, "✅ Bakım mesajı güncellendi!")

    def clone_ekle(message):
        if message.from_user.id != ADMIN_ID: return
        if message.text == "/iptal":
            bot.reply_to(message, "❌ İptal edildi.")
            return
        token = message.text.strip()
        if ":" not in token:
            bot.reply_to(message, "❌ Geçersiz token formatı!")
            return
        try:
            test_bot = telebot.TeleBot(token)
            me = test_bot.get_me()
            clone_kaydet(token, me.username)
            bot.reply_to(
                message,
                f"✅ *Clone Bot Eklendi!*\n\n"
                f"🤖 @{me.username}\n"
                f"📌 ID: `{me.id}`\n\n"
                f"⚠️ Webhook kurmak için `/setwebhook` URL'sini tarayıcıda açın.",
                parse_mode="Markdown"
            )
        except Exception as e:
            bot.reply_to(message, f"❌ Token geçersiz: {str(e)}")

    def clone_sil(message):
        if message.from_user.id != ADMIN_ID: return
        token = message.text.strip()
        if clone_sil_token(token):
            bot.reply_to(message, "✅ Clone silindi!")
        else:
            bot.reply_to(message, "❌ Token bulunamadı!")

    return bot


def yenileme_bildirimi(bot):
    a = ayarlari_yukle()
    a["son_yenileme"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ayarlari_kaydet(a)

    kullanicilar = kullanicilari_yukle()
    metin = (
        "🔄 *SİSTEM YENİLENDİ!*\n\n"
        f"📌 Versiyon: `{a['versiyon']}`\n"
        f"🕐 Tarih: `{a['son_yenileme']}`\n\n"
        "✨ Yeni özellikler eklendi!"
    )
    for uid in kullanicilar.keys():
        try:
            bot.send_message(uid, metin, parse_mode="Markdown")
        except:
            pass


# ============ CLONE YÖNETİMİ ============
def clone_listesi_yukle():
    if os.path.exists(CLONE_FILE):
        try:
            with open(CLONE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []


def clone_listesi_kaydet(clones):
    with open(CLONE_FILE, "w", encoding="utf-8") as f:
        json.dump(clones, f, ensure_ascii=False, indent=2)


def clone_kaydet(token, username):
    clones = clone_listesi_yukle()
    for c in clones:
        if c["token"] == token:
            return False
    clones.append({
        "token": token,
        "username": username,
        "eklenme": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    clone_listesi_kaydet(clones)
    return True


def clone_sil_token(token):
    clones = clone_listesi_yukle()
    yeni = [c for c in clones if c["token"] != token]
    if len(yeni) != len(clones):
        clone_listesi_kaydet(yeni)
        return True
    return False
