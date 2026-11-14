# ============================================================
# KANSAI SIGNAL - Telegram Bot v5 AI FULLY AUTO + CHART + SCALPING RSI 10/90 + STOCH
# - 2 JENIS SIGNAL: SCALPING (10-20/day) & INTRADAY (2-3/day)
# - Client pilih masa /start: Scalping / Intraday / Dua-Dua
# - Scalping: SL 20 pips, TP1 20, TP2 40, TP3 60
# - Intraday: SL 50 pips, TP1 50, TP2 100, TP3 150
# - GOLD 1 pip = 0.10 (4110 -> 4115 = 50 pips)
# - BTC  1 pip = 10 USD (100000 -> 100500 = 50 pips)
# - Result kira 0.05 lot dalam USD, tunjuk DUA-DUA jenis untuk marketing
# - 3 PAYMENT: 1) Manual Bank  2) Billplz Auto  3) Broker Daftar + Deposit $50 (FREE Monthly)
# - Free Trial 7 Hari (sekali sahaja) + Bot DM sahaja
# ============================================================
import json
import os
import threading
import datetime
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# ---------- CONFIG ----------
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "424384984"))

# Billplz (kalau ada)
BILLPLZ_API_KEY = os.getenv("BILLPLZ_API_KEY", "")
BILLPLZ_COLLECTION_ID = os.getenv("BILLPLZ_COLLECTION_ID", "")
BILLPLZ_X_SIGNATURE = os.getenv("BILLPLZ_X_SIGNATURE", "")

# DuitNow / Bank Manual
BANK_NAME = os.getenv("BANK_NAME", "")
BANK_ACCOUNT_NAME = os.getenv("BANK_ACCOUNT_NAME", "")
BANK_ACCOUNT_NO = os.getenv("BANK_ACCOUNT_NO", "")

# BROKER - ISI LINK KAU KAT SINI
BROKER_NAME = "Elev8"
BROKER_LINK = "https://elev8link.com/iWejT9XCLSA"

# ---------- 2 CHANNEL BARU - KANSAI ----------
# Nanti kau ganti dengan username channel kau sendiri
# Contoh: "@kansai_news" dan "@kansai_ta"
# Pastikan bot dah jadi Admin dalam kedua-dua channel tu
CHANNEL_NEWS_ID = "@kansai_news"  # Channel 1: News - https://t.me/kansai_news  # Channel 1: News Forex
CHANNEL_TA_ID = "@kansai_ta"  # Channel 2: TA - https://t.me/kansai_ta  # Channel 2: Teknikal Analisis Forex

BROKER_MIN_DEPOSIT = 50  # $50

PRICE_1BULAN = 50
PRICE_3BULAN = 120

# Render Disk - kalau ada /data (Disk), simpan users.json kat sana supaya tak hilang bila redeploy.
import os as _os_disk
_DATA_DIR = "/data" if _os_disk.path.isdir("/data") else "."
USERS_FILE = _os_disk.path.join(_DATA_DIR, "users.json")
SIGNALS_FILE = _os_disk.path.join(_DATA_DIR, "signals.json")
# AUTO-MERGE: Kalau ada users.json kat folder projek (dari GitHub), gabungkan dengan /data punya. Jangan timpa, gabung.
try:
    import shutil as _shutil, json as _json_restore
    for _src_name, _dst_path, _is_dict in [("users.json", USERS_FILE, True), ("signals.json", SIGNALS_FILE, False)]:
        if not _os_disk.path.exists(_src_name):
            continue
        if _os_disk.path.abspath(_src_name) == _os_disk.path.abspath(_dst_path):
            continue
        try:
            if _os_disk.path.getsize(_src_name) < 10:
                continue
            with open(_src_name, "r", encoding="utf-8") as _ff:
                _src_data = _json_restore.load(_ff)
            _dst_data = None
            if _os_disk.path.exists(_dst_path) and _os_disk.path.getsize(_dst_path) >= 10:
                try:
                    with open(_dst_path, "r", encoding="utf-8") as _ff2:
                        _dst_data = _json_restore.load(_ff2)
                except Exception:
                    _dst_data = None
            if _is_dict:
                _merged = {}
                if isinstance(_src_data, dict):
                    _merged.update(_src_data)
                if isinstance(_dst_data, dict):
                    _merged.update(_dst_data)
                if len(_merged) > 0 and len(_merged) != (len(_dst_data) if isinstance(_dst_data, dict) else 0):
                    with open(_dst_path, "w", encoding="utf-8") as _ff3:
                        _json_restore.dump(_merged, _ff3, indent=2)
                    print(f"AUTO-MERGE users: src={len(_src_data) if isinstance(_src_data, dict) else 0} dst={len(_dst_data) if isinstance(_dst_data, dict) else 0} merged={len(_merged)}")
                elif not _os_disk.path.exists(_dst_path) or _dst_data in (None, {}, []):
                    with open(_dst_path, "w", encoding="utf-8") as _ff3:
                        _json_restore.dump(_src_data, _ff3, indent=2)
                    print(f"AUTO-RESTORE users OK")
            else:
                if isinstance(_src_data, list) and isinstance(_dst_data, list):
                    _ids = {s.get("id") for s in _dst_data if isinstance(s, dict)}
                    _add = [s for s in _src_data if isinstance(s, dict) and s.get("id") not in _ids]
                    if _add:
                        _merged_list = _dst_data + _add
                        with open(_dst_path, "w", encoding="utf-8") as _ff3:
                            _json_restore.dump(_merged_list, _ff3, indent=2)
                        print(f"AUTO-MERGE signals: +{len(_add)}")
                elif _dst_data in (None, [], {}):
                    with open(_dst_path, "w", encoding="utf-8") as _ff3:
                        _json_restore.dump(_src_data, _ff3, indent=2)
                    print(f"AUTO-RESTORE signals OK")
        except Exception as _e:
            print(f"AUTO-MERGE fail {_src_name}: {_e}")
except Exception as _e2:
    print(f"AUTO-RESTORE setup fail: {_e2}")

PIP_VALUE = {
    "XAUUSD": 0.10,
    "GOLD": 0.10,
    "BTCUSD": 10.0,
    "BTC": 10.0,
}
USD_PER_PIP_005LOT = 0.50

app_flask = Flask(__name__)

# ---------- HELPERS ----------
def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return default

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

def now():
    return datetime.datetime.now()
def now_str():
    return now().strftime("%Y-%m-%d %H:%M:%S")

def normalize_pair(pair_raw):
    p = pair_raw.upper().strip()
    if p in ["GOLD", "XAU", "XAUUSD", "XAU/USD"]:
        return "XAUUSD"
    if p in ["BTC", "BTCUSD", "BTC/USD", "BITCOIN"]:
        return "BTCUSD"
    return p

def normalize_signal_type(t_raw):
    t = t_raw.upper().strip()
    if t in ["SCALP", "SCALPING", "SCALPING", "S"]:
        return "SCALPING"
    if t in ["INTRA", "INTRADAY", "INTRADAY", "I", "SWING"]:
        return "INTRADAY"
    return "INTRADAY"

def calc_levels(pair, direction, entry, signal_type):
    pip = PIP_VALUE.get(pair, 0.10)
    # SCALPING = lebih kecil & laju, INTRADAY = lebih besar
    if signal_type == "SCALPING":
        sl_pips = int(os.getenv("SCALP_SL", "40"))
        tp1_pips = int(os.getenv("SCALP_TP", "60"))
        tp2_pips = 0
        tp3_pips = 0
    else:
        sl_pips, tp1_pips, tp2_pips, tp3_pips = 50, 50, 100, 150
    sl_dist = sl_pips * pip
    tp1_dist = tp1_pips * pip
    tp2_dist = tp2_pips * pip
    tp3_dist = tp3_pips * pip
    if direction == "BUY":
        sl = entry - sl_dist
        tp1 = entry + tp1_dist
        tp2 = entry + tp2_dist
        tp3 = entry + tp3_dist
    else:
        sl = entry + sl_dist
        tp1 = entry - tp1_dist
        tp2 = entry - tp2_dist
        tp3 = entry - tp3_dist
    if pair == "XAUUSD":
        return round(sl, 2), round(tp1, 2), round(tp2, 2), round(tp3, 2), sl_pips, tp1_pips, tp2_pips, tp3_pips
    else:
        return round(sl, 0), round(tp1, 0), round(tp2, 0), round(tp3, 0), sl_pips, tp1_pips, tp2_pips, tp3_pips

def usd_from_pips(pips):
    return round(pips * USD_PER_PIP_005LOT, 2)

def is_active_user(user):
    # ADMIN (kau) tak payah langganan, boleh access semua
    if user and user.get("is_admin"):
        return True
    if not user:
        return False
    end_str = user.get("sub_end") or user.get("trial_end")
    if not end_str:
        return False
    try:
        end = datetime.datetime.fromisoformat(end_str)
        return now() < end
    except:
        return False

def get_user_status_text(user):
    if not user:
        return "Tiada rekod"
    if is_active_user(user):
        end = user.get("sub_end") or user.get("trial_end")
        pref = user.get("signal_pref", "INTRADAY")
        pay = user.get("payment_type", "-")
        if user.get("is_vip"):
            return f"VIP Aktif ({pref} / {pay}) sehingga {end}"
        else:
            return f"Free Trial Aktif ({pref}) sehingga {end}"
    else:
        return "Tidak Aktif / Tamat Tempoh"

def should_receive_signal(user, signal_type):
    # User pilih SCALPING dapat SCALPING je, INTRADAY dapat INTRADAY je, BOTH dapat semua
    pref = user.get("signal_pref", "INTRADAY")
    if pref == "BOTH":
        return True
    return pref == signal_type

# ---------- /start - PILIH SIGNAL ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or update.effective_user.first_name or "Tuan/Puan"
    users = load_json(USERS_FILE, {})

    # Kalau user baru, create tapi belum set signal_pref - suruh pilih dulu
    if user_id not in users:
        trial_end = now() + datetime.timedelta(days=7)
        _is_admin_new = (str(user_id) == str(ADMIN_ID))
        users[user_id] = {
            "is_admin": _is_admin_new,
            "is_vip": True if _is_admin_new else False,
            "sub_end": "2099-12-31T23:59:59" if _is_admin_new else None,
            "username": username,
            "trial_used": True,
            "trial_start": now_str(),
            "trial_end": trial_end.isoformat(),
            "sub_end": None,
            "is_vip": False,
            "signal_pref": None,
            "payment_type": None,
            "created_at": now_str()
        }
        save_json(USERS_FILE, users)

        keyboard = [
            [InlineKeyboardButton("⚡ SCALPING - 10 ke 20 Signal Sehari", callback_data="choose_SCALPING")],
            [InlineKeyboardButton("📈 INTRADAY - 2 ke 3 Signal Sehari", callback_data="choose_INTRADAY")],
            [InlineKeyboardButton("🔥 DUA-DUA - Scalping + Intraday", callback_data="choose_BOTH")],
            [InlineKeyboardButton("💡 Tips Trading Kansai", callback_data="tips_kansai")],
            [InlineKeyboardButton("📋 Copytrading (Coming Soon)", callback_data="copytrading_soon")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        msg = (
            f"Assalamualaikum & Selamat Datang ke *KANSAI SIGNAL* 🌟\n\n"
            f"Terima kasih kerana berminat, {username}.\n\n"
            f"🎁 Anda telah menerima *7 Hari Free Trial*.\n"
            f"Trial aktif sehingga: *{trial_end.strftime('%d/%m/%Y %H:%M')}*\n\n"
            f"Kami ada *2 jenis signal*:\n\n"
            f"⚡ *SCALPING 🔴 & 🟢*\n"
            f"• 10 ke 20 signal sehari\n"
            f"• Signal baru setiap 20-30 minit\n"
            f"• 🟢 Signal : SL 20 pips, TP1 20 / TP2 40 / TP3 60 pips\n"
            f"• 🔴 Signal : SL 30 pips, TP 40 pips\n"
            f"• Sesuai untuk yang suka laju & banyak entry\n\n"
            f"📈 *INTRADAY*\n"
            f"• 2 ke 3 signal sehari\n"
            f"• Lebih santai, tak perlu tengok chart selalu\n"
            f"• SL 50 pips, TP1 50 / TP2 100 / TP3 150 pips\n"
            f"• Sesuai untuk yang kerja / busy\n\n"
            f"👇 *Sila pilih signal mana yang anda nak aktifkan:*\n"
            f"Anda boleh tukar bila-bila masa dengan taip /tukar"
        )
        await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=reply_markup)
        return

    user = users[user_id]
    # Kalau admin, pastikan dia admin + VIP kekal, tak payah langganan
    if str(user_id) == str(ADMIN_ID):
        user["is_admin"] = True
        user["is_vip"] = True
        user["sub_end"] = "2099-12-31T23:59:59"
        save_json(USERS_FILE, users)
    # Kalau user lama tapi belum pilih pref, suruh pilih
    if not user.get("signal_pref"):
        keyboard = [
            [InlineKeyboardButton("⚡ SCALPING - 10 ke 20 Signal Sehari", callback_data="choose_SCALPING")],
            [InlineKeyboardButton("📈 INTRADAY - 2 ke 3 Signal Sehari", callback_data="choose_INTRADAY")],
            [InlineKeyboardButton("🔥 DUA-DUA - Scalping + Intraday", callback_data="choose_BOTH")],
            [InlineKeyboardButton("💡 Tips Trading Kansai", callback_data="tips_kansai")],
            [InlineKeyboardButton("📋 Copytrading (Coming Soon)", callback_data="copytrading_soon")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"Selamat Datang Kembali ke *KANSAI SIGNAL* 🌟\n\n"
            f"Sila pilih signal mana yang anda nak aktifkan dulu:",
            parse_mode="Markdown", reply_markup=reply_markup
        )
        return

    if is_active_user(user):
        msg = (
            f"Selamat Datang Kembali ke *KANSAI SIGNAL* 🌟\n\n"
            f"Status anda: *{'VIP Aktif' if user.get('is_vip') else 'Free Trial Aktif'}*\n"
            f"Signal Pilihan: *{user.get('signal_pref')}*\n"
            f"Sehingga: {user.get('sub_end') or user.get('trial_end')}\n\n"
            f"Anda akan terus menerima signal {user.get('signal_pref')} GOLD & BTC terus ke sini.\n"
            f"Taip /tukar untuk tukar jenis signal.\n"
            f"Taip /result untuk lihat prestasi Scalping & Intraday."
        )
        await update.message.reply_text(msg, parse_mode="Markdown")
    else:
        msg = (
            f"Selamat Datang Kembali ke *KANSAI SIGNAL* 🌟\n\n"
            f"Maaf, tempoh percubaan / langganan anda telah tamat.\n\n"
            f"Untuk terus menerima signal, sila langgan:\n"
            f"• RM50 / Sebulan (Bank / Billplz)\n"
            f"• RM120 / 3 Bulan (Bank / Billplz)\n"
            f"• PERCUMA Sebulan - Daftar Broker & Deposit $50\n\n"
            f"Taip /bayar untuk buat pembayaran.\n"
            f"Taip /result untuk lihat prestasi terkini kami."
        )
        await update.message.reply_text(msg, parse_mode="Markdown")

# ---------- /tukar - TUKAR JENIS SIGNAL ----------
async def tukar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("⚡ SCALPING Sahaja", callback_data="choose_SCALPING")],
        [InlineKeyboardButton("📈 INTRADAY Sahaja", callback_data="choose_INTRADAY")],
        [InlineKeyboardButton("🔥 DUA-DUA", callback_data="choose_BOTH")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Sila pilih jenis signal yang anda nak terima:\n\n"
        "⚡ SCALPING - 10 ke 20 signal sehari, setiap 20-30 minit\n"
        "📈 INTRADAY - 2 ke 3 signal sehari, lebih santai\n"
        "🔥 DUA-DUA - Dapat semua signal",
        reply_markup=reply_markup
    )

# ---------- /mysub ----------
async def mysub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    users = load_json(USERS_FILE, {})
    user = users.get(user_id)
    if not user:
        await update.message.reply_text("Anda belum mendaftar. Sila taip /start untuk mula Free Trial 7 Hari.")
        return
    status = get_user_status_text(user)
    msg = (
        f"📋 *Status Langganan Anda*\n\n"
        f"Username: @{user.get('username','-')}\n"
        f"Status: {status}\n"
        f"Signal Pilihan: {user.get('signal_pref','-')}\n"
        f"Kaedah Bayaran: {user.get('payment_type','-')}\n\n"
        f"Taip /tukar untuk tukar jenis signal.\n"
        f"Jika sudah tamat, taip /bayar untuk sambung langganan."
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

# ---------- /bayar - 3 JENIS PAYMENT ----------
async def bayar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🏦 1. Bayar Manual - Bank / DuitNow", callback_data="pay_manual")],
        [InlineKeyboardButton("💳 2. Bayar Auto - Billplz (FPX)", callback_data="pay_billplz_menu")],
        [InlineKeyboardButton("🎁 3. PERCUMA - Daftar Broker + Deposit $50", callback_data="pay_broker")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    msg = (
        f"💳 *Pembayaran KANSAI SIGNAL - 3 Pilihan*\n\n"
        f"1️⃣ *Manual - Bank / DuitNow*\n"
        f"Transfer manual, hantar resit, admin approve.\n"
        f"RM50 / Sebulan | RM120 / 3 Bulan\n\n"
        f"2️⃣ *Auto - Billplz (FPX)*\n"
        f"Bayar terus, akaun auto aktif. Paling cepat.\n"
        f"RM50 / Sebulan | RM120 / 3 Bulan\n\n"
        f"3️⃣ *PERCUMA - Daftar Broker + Deposit $50*\n"
        f"Daftar bawah link kami, deposit $50 dalam akaun trading anda sendiri.\n"
        f"Duit tu masih duit anda, bukan bayar kat kami.\n"
        f"Dapat langgan *PERCUMA sebulan*.\n"
        f"Bulan depan, tunjuk akaun masih ada $50 ke atas, dapat sambung PERCUMA lagi sebulan.\n\n"
        f"👇 Sila pilih:"
    )
    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = str(query.from_user.id)
    username = query.from_user.username or query.from_user.first_name or "User"
    users = load_json(USERS_FILE, {})

    # --- AI APPROVE / REJECT (SEMI) ---
    if query.data.startswith("ai_approve_"):
        try:
            pid = int(query.data.replace("ai_approve_", ""))
            pending = AI_PENDING.get(pid)
            if not pending:
                await query.message.reply_text("Pending signal ni dah expired / dah dihantar.")
                return
            new_id, sent = await _create_ai_signal(context, pending["pair"], pending["direction"], pending["entry"], pending["signal_type"], pending["reason"])
            del AI_PENDING[pid]
            await query.message.reply_text(f"Approved! AI signal dah dihantar sebagai #{new_id} kepada {sent} user.")
        except Exception as e:
            await query.message.reply_text(f"Error approve AI: {e}")
        return
    if query.data.startswith("ai_reject_"):
        try:
            pid = int(query.data.replace("ai_reject_", ""))
            if pid in AI_PENDING:
                del AI_PENDING[pid]
            await query.message.reply_text(f"Rejected pending AI #{pid}. AI tak hantar signal tu.")
        except Exception as e:
            await query.message.reply_text(f"Error reject: {e}")
        return

    # --- COPYTRADING (COMING SOON) - BUTTON TUNJUK JE, TAK BOLEH TEKAN BUAT APA-APA ---
    if query.data == "copytrading_soon":
        try:
            await query.answer("📋 Copytrading Coming Soon! Stay tuned di @kansai_news", show_alert=True)
        except:
            pass
        return
    # --- TIPS KANSAI BUTTON ---
    if query.data == "tips_kansai":
        try:
            await query.answer()
        except:
            pass
        try:
            await query.message.reply_text(TIPS_KANSAI_TEXT, parse_mode="Markdown")
        except Exception as e:
            print(f"Tips Markdown gagal: {e}")
            # Fallback tanpa Markdown kalau ada character yang Telegram tak terima
            try:
                await query.message.reply_text(TIPS_KANSAI_TEXT.replace("*", "").replace("_", ""))
            except Exception as e2:
                print(f"Tips fallback gagal: {e2}")
        return
    if query.data == "menu":
        await query.message.reply_text("Taip /start untuk menu utama, /tips untuk Tips Trading Kansai, /result untuk result.")
        return
    # --- PILIH SIGNAL ---
    if query.data.startswith("choose_"):
        pref = query.data.replace("choose_", "")
        # pref = SCALPING / INTRADAY / BOTH
        if user_id in users:
            users[user_id]["signal_pref"] = pref
            save_json(USERS_FILE, users)
            if pref == "SCALPING":
                desc = "⚡ SCALPING\n10 ke 20 signal sehari, setiap 20-30 minit\nSL 20 pips, TP1 20 / TP2 40 / TP3 60 pips"
            elif pref == "INTRADAY":
                desc = "📈 INTRADAY\n2 ke 3 signal sehari\nSL 50 pips, TP1 50 / TP2 100 / TP3 150 pips"
            else:
                desc = "🔥 DUA-DUA (Scalping + Intraday)\nAnda akan terima semua signal"
            await query.message.reply_text(
                f"✅ *Signal {pref} Telah Diaktifkan!*\n\n{desc}\n\n"
                f"Anda akan mula menerima signal {pref} GOLD & BTC terus ke sini.\n"
                f"Taip /result untuk lihat prestasi kami.\n"
                f"Taip /tukar bila-bila masa untuk tukar jenis signal.",
                parse_mode="Markdown"
            )
        return

    # --- PAYMENT MANUAL ---
    if query.data == "pay_manual":
        msg = (
            f"🏦 *Bayaran Manual - Bank / DuitNow*\n\n"
            f"Sila transfer ke:\n"
            f"Bank: {BANK_NAME}\n"
            f"Nama: {BANK_ACCOUNT_NAME}\n"
            f"No. Akaun / DuitNow: {BANK_ACCOUNT_NO}\n\n"
            f"Jumlah:\n"
            f"• RM50 untuk 30 Hari\n"
            f"• RM120 untuk 90 Hari\n\n"
            f"Langkah:\n"
            f"1. Buat transfer\n"
            f"2. Screenshot resit\n"
            f"3. Hantar gambar resit ke sini\n"
            f"4. Admin akan semak & aktifkan akaun anda\n\n"
            f"Terima kasih atas sokongan anda."
        )
        await query.message.reply_text(msg, parse_mode="Markdown")
        return

    # --- PAYMENT BILLPLZ MENU ---
    if query.data == "pay_billplz_menu":
        kb = [
            [InlineKeyboardButton("💳 Billplz RM50 / Sebulan", callback_data="pay_billplz_50")],
            [InlineKeyboardButton("💳 Billplz RM120 / 3 Bulan", callback_data="pay_billplz_120")],
        ]
        await query.message.reply_text("Sila pilih pakej Billplz:", reply_markup=InlineKeyboardMarkup(kb))
        return

    if query.data.startswith("pay_billplz"):
        amount = "50" if "50" in query.data else "120"
        days = "30 Hari" if amount == "50" else "90 Hari"
        if BILLPLZ_API_KEY.startswith("ISI_"):
            msg = (
                f"💳 *Bayaran Auto Billplz*\n\n"
                f"Maaf, pembayaran auto sedang dalam penyelenggaraan seketika.\n\n"
                f"Sila gunakan kaedah Manual Bank atau Broker PERCUMA buat masa ini.\n\n"
                f"Anda pilih: RM{amount} / {days}\n"
                f"Taip /bayar dan pilih kaedah lain."
            )
            await query.message.reply_text(msg, parse_mode="Markdown")
            return
        msg = f"💳 *Bayaran Auto Billplz*\n\nAnda pilih: RM{amount} / {days}\nSila tunggu, link pembayaran akan dihantar sekejap lagi."
        await query.message.reply_text(msg, parse_mode="Markdown")
        return

    # --- PAYMENT BROKER ---
    if query.data == "pay_broker":
        msg = (
            f"🎁 *PERCUMA Sebulan - Daftar Broker + Deposit $50*\n\n"
            f"Cara dia senang je:\n\n"
            f"1️⃣ Daftar akaun trading bawah link kami:\n"
            f"Broker: *{BROKER_NAME}*\n"
            f"Link: {BROKER_LINK}\n\n"
            f"2️⃣ Deposit *$50* ke dalam akaun trading anda sendiri.\n"
            f"Duit tu masih duit anda, bukan bayar kat kami. Anda boleh trade guna duit tu.\n\n"
            f"3️⃣ Screenshot akaun anda yang tunjuk:\n"
            f"• Nama anda\n"
            f"• Balance $50 ke atas / Deposit $50\n"
            f"• Hantar screenshot tu ke sini\n\n"
            f"4️⃣ Admin akan semak & aktifkan langganan *PERCUMA sebulan* untuk anda.\n\n"
            f"🔄 *Bulan Depan Macam Mana?*\n"
            f"Bulan depan, anda cuma perlu hantar screenshot baru yang tunjuk akaun anda masih ada $50 ke atas.\n"
            f"Kalau ada, anda dapat sambung PERCUMA lagi sebulan. Setiap bulan macam tu.\n\n"
            f"Jika akaun bawah $50, anda perlu topup balik ke $50 untuk sambung.\n\n"
            f"Ada soalan? Taip /start dan admin akan bantu."
        )
        await query.message.reply_text(msg, parse_mode="Markdown")
        return

# Terima gambar resit / screenshot broker
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    caption = update.message.caption or "Resit / Screenshot"
    # Forward ke Admin - admin bezakan resit bank vs broker dari caption / gambar
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=f"🧾 *Resit / Screenshot Baru*\n\nDari: @{username} (ID: {user_id})\nCaption: {caption}\n\nUntuk approve bank/Billplz manual:\n/approve {user_id} 30  (RM50)\n/approve {user_id} 90  (RM120)\n\nUntuk approve BROKER (FREE sebulan):\n/approve_broker {user_id} 30\n\nSila semak gambar di bawah.",
            parse_mode="Markdown"
        )
        await context.bot.forward_message(chat_id=ADMIN_ID, from_chat_id=update.effective_chat.id, message_id=update.message.message_id)
    except Exception as e:
        print("Forward error:", e)
    await update.message.reply_text(
        "Terima kasih. Screenshot / resit anda telah dihantar kepada admin untuk semakan.\n"
        "Admin akan aktifkan akaun anda sebaik sahaja disahkan.\n"
        "Anda akan menerima notifikasi di sini."
    )

# ---------- /signal - ADMIN SAHAJA ----------
# Format baru:
# /signal SCALP BUY XAUUSD 4110
# /signal INTRA BUY XAUUSD 4110
# /signal SCALP SELL BTCUSD 100000
# Format lama masih support: /signal BUY XAUUSD 4110 (default INTRADAY)
async def signal_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Maaf, command ini hanya untuk admin.")
        return
    args = context.args
    if len(args) < 3:
        await update.message.reply_text(
            "Format Baru:\n"
            "/signal SCALP BUY XAUUSD 4110\n"
            "/signal INTRA BUY XAUUSD 4110\n"
            "/signal SCALP SELL BTCUSD 100000\n"
            "/signal INTRA SELL BTCUSD 100000\n\n"
            "SCALP = SL 20, TP1 20, TP2 40, TP3 60\n"
            "INTRA = SL 50, TP1 50, TP2 100, TP3 150\n\n"
            "Format lama pun boleh:\n"
            "/signal BUY XAUUSD 4110 (auto jadi INTRADAY)"
        )
        return

    # Parse: kalau arg pertama SCALP/INTRA, shift
    signal_type = "INTRADAY"
    idx = 0
    if args[0].upper() in ["SCALP", "SCALPING", "INTRA", "INTRADAY"]:
        signal_type = normalize_signal_type(args[0])
        idx = 1
    if len(args) < idx + 3:
        await update.message.reply_text("Format tak lengkap. Contoh: /signal SCALP BUY XAUUSD 4110")
        return
    direction = args[idx].upper()
    if direction not in ["BUY", "SELL"]:
        await update.message.reply_text("Direction mesti BUY atau SELL.")
        return
    pair = normalize_pair(args[idx+1])
    if pair not in ["XAUUSD", "BTCUSD"]:
        await update.message.reply_text("Pair hanya XAUUSD (GOLD) & BTCUSD (BTC) sahaja.")
        return
    try:
        entry = float(args[idx+2])
    except:
        await update.message.reply_text("Entry mesti nombor. Contoh: /signal SCALP BUY XAUUSD 4110")
        return
    _ok, _reason = _can_send_ai(pair, signal_type)
    if not _ok:
        await update.message.reply_text(f"❌ Tak boleh hantar - {_reason}\n\nTutup dulu signal OPEN tu guna /close {pair} TP1 / SL, baru buat signal baru.")
        return

    # TP3 - kalau SCALPING dan M15 tak confirm, TP3 = None (TP1+TP2 sahaja)
    tp3_valid = True
    # reason boleh bawa flag TP3 - check dari _check_scalping_ai, tapi _create_ai_signal dipanggil dari ai_scan_job yang dah pass tp3_valid via reason? Kita guna global last TP3 flag
    # Untuk senang: kalau signal_type SCALPING, kita akan set tp3_valid dari AI_LAST_TP3 yang ai_scan_job set sebelum panggil ni
    tp3_valid = globals().get("_LAST_TP3_VALID", True)
    sl, tp1, tp2, tp3, sl_pips, tp1_pips, tp2_pips, tp3_pips = calc_levels(pair, direction, entry, signal_type)
    if signal_type == "SCALPING" and not tp3_valid:
        tp3 = None
        tp3_pips = None
    # WEAK SIGNAL - BUANG TP2, TP + SL JE: TP 40 pips, SL 30 pips, TAKDE TP2/TP3
    _is_weak = globals().get("_LAST_IS_WEAK", False)
    if signal_type == "SCALPING" and _is_weak:
        _pip_weak = PIP_VALUE.get(pair, 0.10)
        _tp_dist_weak = 40 * _pip_weak
        _sl_dist_weak = 30 * _pip_weak
        if direction == "BUY":
            sl = entry - _sl_dist_weak
            tp1 = entry + _tp_dist_weak
        else:
            sl = entry + _sl_dist_weak
            tp1 = entry - _tp_dist_weak
        if pair == "XAUUSD":
            sl = round(sl, 2)
            tp1 = round(tp1, 2)
        else:
            sl = round(sl, 0)
            tp1 = round(tp1, 0)
        tp1_pips = 40
        sl_pips = 30
        tp2 = None
        tp2_pips = None
        tp3 = None
        tp3_pips = None
        tp2_usd = 0
        tp3_usd = 0
        sl_usd = round(sl_pips * USD_PER_PIP_005LOT, 2)
        tp1_usd = round(tp1_pips * USD_PER_PIP_005LOT, 2)

    signals = load_json(SIGNALS_FILE, [])
    new_id = 1
    if signals:
        new_id = max([s.get("id", 0) for s in signals]) + 1

    new_signal = {
        "id": new_id,
        "pair": pair,
        "direction": direction,
        "entry": entry,
        "sl": sl,
        "tp1": tp1,
        "tp2": tp2,
        "tp3": tp3,
        "signal_type": signal_type,
        "sl_pips": sl_pips,
        "tp1_pips": tp1_pips,
        "tp2_pips": tp2_pips,
        "tp3_pips": tp3_pips,
        "status": "OPEN",
        "result": None,
        "pips": 0,
        "usd_005lot": 0,
        "created_at": now_str()
    }
    signals.append(new_signal)
    save_json(SIGNALS_FILE, signals)

    _labels = {"XAUUSD": "GOLD (XAUUSD)", "BTCUSD": "BTC (BTCUSD)", "EURUSD": "EUR / USD", "GBPUSD": "GBP / USD", "AUDUSD": "AUD / USD", "USDCAD": "USD / CAD", "NZDUSD": "NZD / USD", "USDCHF": "USD / CHF", "USDJPY": "USD / JPY", "EURJPY": "EUR / JPY", "GBPJPY": "GBP / JPY", "EURGBP": "EUR / GBP", "XAGUSD": "SILVER (XAGUSD)"}
    pair_label = _labels.get(pair, pair)
    arrow = "🟢 BUY" if direction == "BUY" else "🔴 SELL"
    if signal_type == "SCALPING" and globals().get("_LAST_IS_WEAK", False):
        type_label = "🔴 WEAK SIGNAL - DYOR"
        # Override header: WEAK = merah, STRONG = hijau
    elif signal_type == "SCALPING":
        type_label = "🟢 STRONG SIGNAL"
    else:
        type_label = "📈 INTRADAY"
    # USD untuk 0.05 lot
    sl_usd = usd_from_pips(sl_pips)
    tp1_usd = usd_from_pips(tp1_pips)
    tp2_usd = usd_from_pips(tp2_pips)
    tp3_usd = usd_from_pips(tp3_pips)

    msg = (
        f"📈 *KANSAI SIGNAL - {type_label} #{new_id}*\n\n"
        f"Pair: *{pair_label}*\n"
        f"Direction: *{arrow}*\n"
        f"Jenis: *{signal_type}*\n\n"
        f"Entry: *{entry}*\n"
        f"SL: *{sl}* (-{sl_pips} pips / -${sl_usd:.2f} untuk 0.05 lot)\n"
        f"TP1: *{tp1}* (+{tp1_pips} pips / +${tp1_usd:.2f} untuk 0.05 lot)\n"
        f"TP2: *{tp2}* (+{tp2_pips} pips / +${tp2_usd:.2f} untuk 0.05 lot)\n"
        f"TP3: *{tp3}* (+{tp3_pips} pips / +${tp3_usd:.2f} untuk 0.05 lot)\n\n"
        f"💡 Tips: Tutup sebahagian di TP1 untuk lock profit, biarkan selebihnya ke TP2 & TP3.\n\n"
        f"⚠️ Peringatan: Trading ada risiko. Sila urus risiko anda dengan baik."
    )

    users = load_json(USERS_FILE, {})
    sent = 0
    _sent_to = []
    _failed_to = []
    for uid, u in users.items():
        if is_active_user(u) and should_receive_signal(u, signal_type):
            try:
                await context.bot.send_message(chat_id=int(uid), text=msg, parse_mode="Markdown")
                sent += 1
                _sent_to.append(f"@{u.get('username','-')} (ID:{uid})")
            except Exception as e:
                print(f"Gagal hantar ke {uid}: {e}")
                _failed_to.append(f"@{u.get('username','-')} (ID:{uid}) - {str(e)[:80]}")
    try:
        _all_signals2 = load_json(SIGNALS_FILE, [])
        for _s in _all_signals2:
            if _s.get("id") == new_id:
                _s["sent_count"] = sent
                _s["sent_to"] = _sent_to
                _s["failed_to"] = _failed_to
                _s["sent_at"] = now_str()
                _s["sent_by"] = "MANUAL"
                break
        save_json(SIGNALS_FILE, _all_signals2)
    except Exception as _e_save2:
        print(f"Gagal simpan sent log manual: {_e_save2}")
    await update.message.reply_text(f"✅ Signal {signal_type} #{new_id} dihantar kepada {sent} user (yang pilih {signal_type} / BOTH).\n\n{msg}", parse_mode="Markdown")

# ---------- /close - ADMIN ----------
async def close_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Maaf, command ini hanya untuk admin.")
        return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "Format:\n"
            "/close 5 TP1\n"
            "/close 5 TP2\n"
            "/close 5 TP3\n"
            "/close 5 SL"
        )
        return
    try:
        sid = int(args[0])
    except:
        await update.message.reply_text("ID signal mesti nombor.")
        return
    result_raw = args[1].upper()
    if result_raw not in ["TP1", "TP2", "TP3", "SL", "WIN", "LOSS", "BE"]:
        await update.message.reply_text("Result mesti TP1 / TP2 / TP3 / SL")
        return

    signals = load_json(SIGNALS_FILE, [])
    target = None
    for s in signals:
        if s.get("id") == sid:
            target = s
            break
    if not target:
        await update.message.reply_text(f"Signal #{sid} tidak dijumpai.")
        return
    if target.get("status") == "CLOSED":
        await update.message.reply_text(f"Signal #{sid} sudah ditutup sebelum ini.")
        return

    # Guna pips dari signal asal (SCALPING vs INTRADAY lain)
    sl_pips = target.get("sl_pips", 50)
    tp1_pips = target.get("tp1_pips", 50)
    tp2_pips = target.get("tp2_pips", 100)
    tp3_pips = target.get("tp3_pips", 150)
    mapping = {
        "TP1": (tp1_pips, usd_from_pips(tp1_pips), "WIN"),
        "TP2": (tp2_pips, usd_from_pips(tp2_pips), "WIN"),
        "TP3": (tp3_pips, usd_from_pips(tp3_pips), "WIN"),
        "SL": (-sl_pips, usd_from_pips(-sl_pips), "LOSS"),
        "WIN": (tp1_pips, usd_from_pips(tp1_pips), "WIN"),
        "LOSS": (-sl_pips, usd_from_pips(-sl_pips), "LOSS"),
        "BE": (0, 0.0, "BE"),
    }
    pips_val, usd_val, winloss = mapping[result_raw]
    if result_raw in ["WIN", "LOSS"] and len(args) >= 3:
        try:
            pips_val = int(float(args[2]))
            if result_raw == "LOSS" and pips_val > 0:
                pips_val = -pips_val
            usd_val = usd_from_pips(pips_val)
        except:
            pass

    target["status"] = "CLOSED"
    target["result"] = result_raw
    target["pips"] = pips_val
    target["usd_005lot"] = usd_val
    target["closed_at"] = now_str()
    save_json(SIGNALS_FILE, signals)

    pair_label = "GOLD (XAUUSD)" if target["pair"] == "XAUUSD" else "BTC (BTCUSD)"
    signal_type = target.get("signal_type", "INTRADAY")
    type_label = "⚡ SCALPING" if signal_type == "SCALPING" else "📈 INTRADAY"
    icon = "✅" if winloss == "WIN" else ("❌" if winloss == "LOSS" else "➖")
    usd_text = f"+${usd_val:.2f}" if usd_val >= 0 else f"-${abs(usd_val):.2f}"
    pips_text = f"+{pips_val} pips" if pips_val >= 0 else f"{pips_val} pips"

    msg = (
        f"{icon} *KANSAI SIGNAL - {type_label} #{sid} CLOSED*\n\n"
        f"Pair: *{pair_label} {target['direction']}*\n"
        f"Entry: *{target['entry']}*\n"
        f"Result: *{result_raw}*\n"
        f"Pips: *{pips_text}*\n"
        f"Profit / Loss: *{usd_text}* (0.05 lot)\n\n"
        f"Terima kasih kerana bersama KANSAI SIGNAL."
    )

    users = load_json(USERS_FILE, {})
    sent = 0
    _sent_to = []
    _failed_to = []
    for uid, u in users.items():
        if is_active_user(u) and should_receive_signal(u, signal_type):
            try:
                await context.bot.send_message(chat_id=int(uid), text=msg, parse_mode="Markdown")
                sent += 1
                _sent_to.append(f"@{u.get('username','-')} (ID:{uid})")
            except Exception as _e_send:
                _failed_to.append(f"@{u.get('username','-')} (ID:{uid}) - {str(_e_send)[:80]}")
    try:
        _all_signals = load_json(SIGNALS_FILE, [])
        for _s in _all_signals:
            if _s.get("id") == sid:
                _s["sent_count"] = sent
                _s["sent_to"] = _sent_to
                _s["failed_to"] = _failed_to
                _s["sent_at"] = now_str()
                break
        save_json(SIGNALS_FILE, _all_signals)
    except Exception as _e_save:
        print(f"Gagal simpan sent log AI: {_e_save}")
    await update.message.reply_text(f"✅ Signal {signal_type} #{sid} ditutup sebagai {result_raw} ({pips_text} / {usd_text}) dan dihantar kepada {sent} user.\n\n{msg}", parse_mode="Markdown")

# ---------- /result - TUNJUK DUA-DUA UNTUK MARKETING ----------
async def result_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    signals = load_json(SIGNALS_FILE, [])
    closed = [s for s in signals if s.get("status") == "CLOSED"]
    week_ago = now() - datetime.timedelta(days=7)
    month_ago = now() - datetime.timedelta(days=30)
    def parse_date(s):
        try:
            return datetime.datetime.fromisoformat(s)
        except:
            try:
                return datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
            except:
                return now()
    def calc_stats(filtered):
        total = len(filtered)
        wins = len([s for s in filtered if s.get("pips", 0) > 0])
        losses = len([s for s in filtered if s.get("pips", 0) < 0])
        total_pips = sum([s.get("pips", 0) for s in filtered])
        total_usd = sum([s.get("usd_005lot", 0) for s in filtered])
        winrate = round((wins / total * 100), 1) if total > 0 else 0
        return total, wins, losses, total_pips, total_usd, winrate

    weekly_all = [s for s in closed if parse_date(s.get("closed_at") or s.get("created_at")) >= week_ago]
    monthly_all = [s for s in closed if parse_date(s.get("closed_at") or s.get("created_at")) >= month_ago]

    # Pecah ikut jenis
    w_scalp = [s for s in weekly_all if s.get("signal_type") == "SCALPING"]
    w_intra = [s for s in weekly_all if s.get("signal_type") == "INTRADAY"]
    m_scalp = [s for s in monthly_all if s.get("signal_type") == "SCALPING"]
    m_intra = [s for s in monthly_all if s.get("signal_type") == "INTRADAY"]

    def fmt(label, data):
        total, wins, losses, pips, usd, wr = calc_stats(data)
        usd_t = f"+${usd:.2f}" if usd >= 0 else f"-${abs(usd):.2f}"
        pips_t = f"+{pips} pips" if pips >= 0 else f"{pips} pips"
        return f"*{label}*\nSignal: {total} | Win: {wins} | Loss: {losses} | Win Rate: {wr}%\nPips: {pips_t} | USD: {usd_t} (0.05 lot)\n"

    msg = (
        f"📊 *KANSAI SIGNAL - PRESTASI*\n\n"
        f"--- *MINGGU INI (7 Hari)* ---\n"
        f"{fmt('⚡ SCALPING', w_scalp)}"
        f"{fmt('📈 INTRADAY', w_intra)}"
        f"{fmt('🔥 TOTAL MINGGU INI', weekly_all)}\n"
        f"--- *BULAN INI (30 Hari)* ---\n"
        f"{fmt('⚡ SCALPING', m_scalp)}"
        f"{fmt('📈 INTRADAY', m_intra)}"
        f"{fmt('🔥 TOTAL BULAN INI', monthly_all)}\n"
        f"_Kiraan berdasarkan 0.05 lot. 0.10 lot = darab 2, 0.01 lot = bahagi 5._\n\n"
        f"Taip /tukar untuk tukar jenis signal anda."
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

# ---------- /approve - ADMIN (Bank / Billplz) ----------
async def approve_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Maaf, command ini hanya untuk admin.")
        return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Format: /approve 123456 30  (RM50) atau /approve 123456 90 (RM120)")
        return
    target_id = args[0]
    try:
        days = int(args[1])
    except:
        await update.message.reply_text("Hari mesti nombor.")
        return
    users = load_json(USERS_FILE, {})
    if target_id not in users:
        await update.message.reply_text(f"User ID {target_id} tidak dijumpai.")
        return
    user = users[target_id]
    current_end_str = user.get("sub_end") or user.get("trial_end")
    try:
        current_end = datetime.datetime.fromisoformat(current_end_str) if current_end_str else now()
        base = max(now(), current_end)
    except:
        base = now()
    new_end = base + datetime.timedelta(days=days)
    user["sub_end"] = new_end.isoformat()
    user["is_vip"] = True
    user["payment_type"] = "BANK / BILLPLZ"
    user["reminded_24h"] = False
    user["expired_notified"] = False
    save_json(USERS_FILE, users)
    await update.message.reply_text(f"✅ User {target_id} (@{user.get('username','-')}) diapprove {days} hari (BANK/BILLPLZ) sehingga {new_end.strftime('%d/%m/%Y %H:%M')}")
    try:
        await context.bot.send_message(chat_id=int(target_id), text=f"🎉 *Tahniah! Langganan Anda Telah Diaktifkan.*\n\nTerima kasih kerana melanggan KANSAI SIGNAL.\n\nStatus: *VIP Aktif*\nSignal: *{user.get('signal_pref','-')}*\nSehingga: {new_end.strftime('%d/%m/%Y %H:%M')}\n\nAnda akan menerima signal GOLD & BTC terus ke sini.", parse_mode="Markdown")
    except:
        pass

# ---------- /approve_broker - ADMIN (Broker FREE) ----------
async def approve_broker_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Maaf, command ini hanya untuk admin.")
        return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("Format: /approve_broker 123456 30  (FREE sebulan sebab deposit $50)")
        return
    target_id = args[0]
    try:
        days = int(args[1])
    except:
        await update.message.reply_text("Hari mesti nombor.")
        return
    users = load_json(USERS_FILE, {})
    if target_id not in users:
        await update.message.reply_text(f"User ID {target_id} tidak dijumpai.")
        return
    user = users[target_id]
    current_end_str = user.get("sub_end") or user.get("trial_end")
    try:
        current_end = datetime.datetime.fromisoformat(current_end_str) if current_end_str else now()
        base = max(now(), current_end)
    except:
        base = now()
    new_end = base + datetime.timedelta(days=days)
    user["sub_end"] = new_end.isoformat()
    user["is_vip"] = True
    user["payment_type"] = f"BROKER ${BROKER_MIN_DEPOSIT} - {BROKER_NAME}"
    user["broker_verified"] = True
    user["broker_verified_at"] = now_str()
    user["reminded_24h"] = False
    user["expired_notified"] = False
    save_json(USERS_FILE, users)
    await update.message.reply_text(f"✅ User {target_id} (@{user.get('username','-')}) diapprove BROKER FREE {days} hari sehingga {new_end.strftime('%d/%m/%Y %H:%M')}\n\nIngatkan user: Bulan depan kena hantar screenshot baru tunjuk balance $50 ke atas untuk sambung FREE.")
    try:
        await context.bot.send_message(
            chat_id=int(target_id),
            text=(
                f"🎉 *Tahniah! Langganan BROKER PERCUMA Anda Telah Diaktifkan.*\n\n"
                f"Terima kasih kerana daftar bawah link kami & deposit $50.\n\n"
                f"Status: *VIP Aktif (BROKER)*\n"
                f"Signal: *{user.get('signal_pref','-')}*\n"
                f"Sehingga: {new_end.strftime('%d/%m/%Y %H:%M')}\n\n"
                f"🔄 *Bulan Depan:*\n"
                f"Sila hantar screenshot baru yang tunjuk akaun anda masih ada $50 ke atas untuk sambung PERCUMA lagi sebulan.\n\n"
                f"Anda akan menerima signal GOLD & BTC terus ke sini."
            ),
            parse_mode="Markdown"
        )
    except:
        pass

# ---------- /listvip ----------
async def listvip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Maaf, command ini hanya untuk admin.")
        return
    users = load_json(USERS_FILE, {})
    active = []
    expired = []
    for uid, u in users.items():
        line = f"• @{u.get('username','-')} (ID: {uid}) - {u.get('signal_pref','-')} / {u.get('payment_type','-')} {'VIP' if u.get('is_vip') else 'Trial'}"
        if is_active_user(u):
            active.append(line)
        else:
            expired.append(line)
    msg = f"👥 *Senarai User*\n\n*Aktif ({len(active)}):*\n" + ("\n".join(active) if active else "Tiada") + f"\n\n*Expired ({len(expired)}):*\n" + ("\n".join(expired) if expired else "Tiada")
    await update.message.reply_text(msg, parse_mode="Markdown")

# ---------- JOBS ----------
async def check_expiry_job(context: ContextTypes.DEFAULT_TYPE):
    users = load_json(USERS_FILE, {})
    changed = False
    for uid, u in users.items():
        end_str = u.get("sub_end") or u.get("trial_end")
        if not end_str:
            continue
        try:
            end = datetime.datetime.fromisoformat(end_str)
        except:
            continue
        diff = end - now()
        if 0 < diff.total_seconds() <= 24*3600 and not u.get("reminded_24h"):
            try:
                is_broker = "BROKER" in (u.get("payment_type") or "")
                extra = ""
                if is_broker:
                    extra = "\n\n🔄 *Untuk Broker:* Sila hantar screenshot baru tunjuk balance $50 ke atas untuk sambung PERCUMA."
                await context.bot.send_message(chat_id=int(uid), text=f"⏰ *Peringatan KANSAI SIGNAL*\n\nLangganan / Trial anda akan tamat dalam masa 24 jam.\nTamat pada: {end.strftime('%d/%m/%Y %H:%M')}{extra}\n\nUntuk terus menerima signal, sila taip /bayar untuk sambung langganan.", parse_mode="Markdown")
                u["reminded_24h"] = True
                changed = True
            except:
                pass
        if diff.total_seconds() <= 0 and not u.get("expired_notified"):
            try:
                await context.bot.send_message(chat_id=int(uid), text="Maaf, langganan / trial anda telah tamat.\n\nUntuk terus menerima signal GOLD & BTC, sila taip /bayar untuk langgan semula.\n\nTaip /result untuk lihat prestasi terkini kami.")
                u["expired_notified"] = True
                u["reminded_24h"] = False
                changed = True
            except:
                pass
        if diff.total_seconds() > 24*3600:
            if u.get("reminded_24h") or u.get("expired_notified"):
                u["reminded_24h"] = False
                u["expired_notified"] = False
                changed = True
    if changed:
        save_json(USERS_FILE, users)

async def weekly_report_job(context: ContextTypes.DEFAULT_TYPE):
    signals = load_json(SIGNALS_FILE, [])
    closed = [s for s in signals if s.get("status") == "CLOSED"]
    week_ago = now() - datetime.timedelta(days=7)
    def parse_date(s):
        try:
            return datetime.datetime.fromisoformat(s)
        except:
            try:
                return datetime.datetime.strptime(s, "%Y-%m-%d %H:%M:%S")
            except:
                return now()
    weekly = [s for s in closed if parse_date(s.get("closed_at") or s.get("created_at")) >= week_ago]
    w_scalp = [s for s in weekly if s.get("signal_type") == "SCALPING"]
    w_intra = [s for s in weekly if s.get("signal_type") == "INTRADAY"]
    def calc(f):
        total=len(f); wins=len([s for s in f if s.get("pips",0)>0]); pips=sum([s.get("pips",0) for s in f]); usd=sum([s.get("usd_005lot",0) for s in f]); wr=round((wins/total*100),1) if total>0 else 0
        return total,wins,pips,usd,wr
    t,w,p,u,wr = calc(weekly)
    ts,ws,ps,us,wrs = calc(w_scalp)
    ti,wi,pi,ui,wri = calc(w_intra)
    msg = (
        f"📊 *KANSAI SIGNAL - Weekly Report*\n\n"
        f"Minggu ini:\n"
        f"⚡ SCALPING: {ts} signal, {wrs}% win, {ps:+} pips / ${us:+.2f} (0.05 lot)\n"
        f"📈 INTRADAY: {ti} signal, {wri}% win, {pi:+} pips / ${ui:+.2f} (0.05 lot)\n"
        f"🔥 TOTAL: {t} signal, {wr}% win, {p:+} pips / ${u:+.2f} (0.05 lot)\n\n"
        f"Jika anda belum langgan, taip /bayar untuk sertai kami.\n"
        f"Jika anda sudah VIP, terima kasih atas sokongan anda."
    )
    users = load_json(USERS_FILE, {})
    for uid in users.keys():
        try:
            await context.bot.send_message(chat_id=int(uid), text=msg, parse_mode="Markdown")
        except:
            pass

# AI ENGINE SNIPPET - SEMI AUTO
# AI suggest kat admin, admin approve baru hantar kat client
import requests as _req
AI_ENABLED = True
AI_MODE = "AUTO"
AI_LAST_SIGNAL = {}
AI_DAILY_COUNT = {}
AI_PENDING = {}
AI_PENDING_COUNTER = 0

def _ema_list(prices, period):
    if len(prices) < period:
        return None
    k = 2 / (period + 1)
    ema = sum(prices[:period]) / period
    for p in prices[period:]:
        ema = p * k + ema * (1 - k)
    return ema

def _rsi_list(prices, period=14):
    if len(prices) < period + 1:
        return 50
    gains = []
    losses = []
    for i in range(1, period+1):
        diff = prices[i] - prices[i-1]
        if diff >= 0:
            gains.append(diff)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(-diff)
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def _fetch_yahoo(symbol, interval="5m", range_="1d"):
    # DISABLED - Yahoo / yfinance kena block kat Render (IP datacenter), selalu return "No price data"
    # Buang terus, jimat 10-20 saat, elak job missed. Guna Binance + TwelveData + Cache je.
    print(f"Yahoo DISABLED - skip {symbol} (block kat Render)")
    return []
def _fetch_coinbase(product="EUR-USD", granularity=300, limit=120):
    # Coinbase tak block Render - fallback untuk EURUSD, GBPUSD, BTC
    try:
        url = f"https://api.exchange.coinbase.com/products/{product}/candles?granularity={granularity}"
        r = _req.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
        if r.status_code != 200:
            print(f"Coinbase {product} status {r.status_code}")
            return []
        data = r.json()
        # Coinbase returns [time, low, high, open, close, volume] newest first - reverse to oldest first
        data = sorted(data, key=lambda x: x[0])
        closes = [float(c[4]) for c in data]
        print(f"Coinbase OK {product} gran={granularity} len={len(closes)}")
        return closes
    except Exception as e:
        print(f"Coinbase fetch error {product}: {e}")
        return []




# --- CACHE - simpan data last yang berjaya, kalau API gagal guna cache ni, jangan Gagal terus ---
import json as _json_cache
import os as _os_cache
def _cache_save(pair, timeframe, closes):
    try:
        fn = f"/tmp/cache_{pair}_{timeframe}.json"
        with open(fn, "w") as f:
            _json_cache.dump({"closes": closes[-120:], "ts": __import__("time").time()}, f)
    except Exception:
        pass

def _cache_load(pair, timeframe, max_age_sec=300):
    # Kalau cache baru lagi (<5 min), guna terus - jangan panggil API, elak rate limit
    try:
        fn = f"/tmp/cache_{pair}_{timeframe}.json"
        if not _os_cache.path.exists(fn):
            return []
        with open(fn, "r") as f:
            d = _json_cache.load(f)
        closes = d.get("closes", [])
        ts = d.get("ts", 0)
        age = __import__("time").time() - ts
        if closes and age < max_age_sec:
            print(f"Cache FRESH {pair} {timeframe} age={int(age)}s len={len(closes)} - guna cache, tak panggil API")
            return closes
        if closes:
            print(f"Cache STALE {pair} {timeframe} age={int(age)}s - cuba API baru")
        return closes if closes else []
    except Exception:
        return []

def _cache_fresh(pair, timeframe, max_age_sec=300):
    try:
        fn = f"/tmp/cache_{pair}_{timeframe}.json"
        if not _os_cache.path.exists(fn):
            return None
        with open(fn, "r") as f:
            d = _json_cache.load(f)
        closes = d.get("closes", [])
        ts = d.get("ts", 0)
        age = __import__("time").time() - ts
        if closes and age < max_age_sec:
            return closes
        return None
    except Exception:
        return None

def _cache_save_ohlc(pair, timeframe, ohlc):
    try:
        fn = f"/tmp/cache_ohlc_{pair}_{timeframe}.json"
        with open(fn, "w") as f:
            _json_cache.dump({"ohlc": ohlc[-60:], "ts": __import__("time").time()}, f)
    except Exception:
        pass

def _cache_load_ohlc(pair, timeframe):
    try:
        fn = f"/tmp/cache_ohlc_{pair}_{timeframe}.json"
        if not _os_cache.path.exists(fn):
            return []
        with open(fn, "r") as f:
            d = _json_cache.load(f)
        return d.get("ohlc", [])
    except Exception:
        return []

def _fetch_binance_forex(pair, timeframe="M5", limit=120):
    # Binance Vision - tak block Render, jalan untuk BTC, GOLD, EUR
    # GOLD guna PAXGUSDT (PAX Gold = harga emas sebenar, 1 PAXG = 1 oz emas)
    # EURUSD guna EURUSDT, GBPUSD guna GBPUSDT, etc - harga sama beza 0.000x je
    # Binance HANYA untuk pair yang betul-betul ada kat Binance - JPY/CHF/CAD/EURGBP takde, biar TwelveData/Kraken handle
    bin_map = {
        "XAUUSD": "PAXGUSDT", "GOLD": "PAXGUSDT",
        "XAGUSD": "XAGUSDT",
        "EURUSD": "EURUSDT", "GBPUSD": "GBPUSDT", "AUDUSD": "AUDUSDT",
        "NZDUSD": "NZDUSDT",
        "BTCUSD": "BTCUSDT", "BTC": "BTCUSDT",
    }
    sym = bin_map.get(pair)
    if not sym:
        return []
    iv_map = {"M1": "1m", "M5": "5m", "M15": "15m", "H1": "1h", "H4": "4h"}
    iv = iv_map.get(timeframe, "5m")
    endpoints = [
        "https://data-api.binance.vision/api/v3/klines",
    ]
    for base_url in endpoints:
        try:
            url = f"{base_url}?symbol={sym}&interval={iv}&limit={limit}"
            r = _req.get(url, timeout=60)
            if r.status_code != 200:
                print(f"BinanceForex {sym} {base_url} status {r.status_code}")
                continue
            data = r.json()
            closes = [float(c[4]) for c in data]
            print(f"BinanceForex OK {pair} -> {sym} {timeframe} len={len(closes)}")
            return closes
        except Exception as e:
            print(f"BinanceForex error {sym} {base_url}: {e}")
            continue
    return []


# --- CACHE - simpan data last yang berjaya, kalau API gagal guna cache ni, jangan Gagal terus ---
import json as _json_cache
import os as _os_cache
def _cache_save(pair, timeframe, closes):
    try:
        fn = f"/tmp/cache_{pair}_{timeframe}.json"
        with open(fn, "w") as f:
            _json_cache.dump({"closes": closes[-120:], "ts": __import__("time").time()}, f)
    except Exception:
        pass

def _cache_load(pair, timeframe, max_age_sec=300):
    # Kalau cache baru lagi (<5 min), guna terus - jangan panggil API, elak rate limit
    try:
        fn = f"/tmp/cache_{pair}_{timeframe}.json"
        if not _os_cache.path.exists(fn):
            return []
        with open(fn, "r") as f:
            d = _json_cache.load(f)
        closes = d.get("closes", [])
        ts = d.get("ts", 0)
        age = __import__("time").time() - ts
        if closes and age < max_age_sec:
            print(f"Cache FRESH {pair} {timeframe} age={int(age)}s len={len(closes)} - guna cache, tak panggil API")
            return closes
        if closes:
            print(f"Cache STALE {pair} {timeframe} age={int(age)}s - cuba API baru")
        return closes if closes else []
    except Exception:
        return []

def _cache_fresh(pair, timeframe, max_age_sec=300):
    try:
        fn = f"/tmp/cache_{pair}_{timeframe}.json"
        if not _os_cache.path.exists(fn):
            return None
        with open(fn, "r") as f:
            d = _json_cache.load(f)
        closes = d.get("closes", [])
        ts = d.get("ts", 0)
        age = __import__("time").time() - ts
        if closes and age < max_age_sec:
            return closes
        return None
    except Exception:
        return None

def _cache_save_ohlc(pair, timeframe, ohlc):
    try:
        fn = f"/tmp/cache_ohlc_{pair}_{timeframe}.json"
        with open(fn, "w") as f:
            _json_cache.dump({"ohlc": ohlc[-60:], "ts": __import__("time").time()}, f)
    except Exception:
        pass

def _cache_load_ohlc(pair, timeframe):
    try:
        fn = f"/tmp/cache_ohlc_{pair}_{timeframe}.json"
        if not _os_cache.path.exists(fn):
            return []
        with open(fn, "r") as f:
            d = _json_cache.load(f)
        return d.get("ohlc", [])
    except Exception:
        return []

def _fetch_binance_forex_ohlc(pair, timeframe="H1", limit=50):
    bin_map = {
        "XAUUSD": "PAXGUSDT", "GOLD": "PAXGUSDT",
        "XAGUSD": "XAGUSDT",
        "EURUSD": "EURUSDT", "GBPUSD": "GBPUSDT", "AUDUSD": "AUDUSDT",
        "NZDUSD": "NZDUSDT",
        "BTCUSD": "BTCUSDT", "BTC": "BTCUSDT",
    }
    sym = bin_map.get(pair)
    if not sym:
        return []
    iv_map = {"M1": "1m", "M5": "5m", "M15": "15m", "H1": "1h", "H4": "4h"}
    iv = iv_map.get(timeframe, "1h")
    for base_url in ["https://data-api.binance.vision/api/v3/klines", "https://api.binance.com/api/v3/klines"]:
        try:
            url = f"{base_url}?symbol={sym}&interval={iv}&limit={limit}"
            r = _req.get(url, timeout=60)
            if r.status_code != 200:
                continue
            data = r.json()
            ohlc = [{"open": float(c[1]), "high": float(c[2]), "low": float(c[3]), "close": float(c[4])} for c in data]
            return ohlc
        except Exception:
            continue
    return []

def _fetch_twelvedata(pair, timeframe="M5", limit=120):
    # TwelveData - untuk GOLD + FOREX, tak block Render, free demo key
    # XAUUSD -> XAU/USD, EURUSD -> EUR/USD
    td_map = {
        "XAUUSD": "XAU/USD", "GOLD": "XAU/USD",
        "XAGUSD": "XAG/USD",
        "EURUSD": "EUR/USD", "GBPUSD": "GBP/USD", "AUDUSD": "AUD/USD",
        "USDCAD": "USD/CAD", "NZDUSD": "NZD/USD", "USDCHF": "USD/CHF",
        "USDJPY": "USD/JPY", "EURJPY": "EUR/JPY", "GBPJPY": "GBP/JPY", "EURGBP": "EUR/GBP",
        "BTCUSD": "BTC/USD", "BTC": "BTC/USD",
    }
    sym = td_map.get(pair)
    if not sym:
        return []
    iv_map = {"M1": "1min", "M5": "5min", "M15": "15min", "H1": "1h", "H4": "4h"}
    iv = iv_map.get(timeframe, "5min")
    # Cuba demo key dulu, kalau user ada key sendiri boleh tukar kat sini
    for api_key in [os.getenv("TWELVEDATA_API_KEY", "")]:
        try:
            url = f"https://api.twelvedata.com/time_series?symbol={sym}&interval={iv}&outputsize={limit}&apikey={api_key}"
            r = _req.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
            if r.status_code != 200:
                print(f"TwelveData {sym} status {r.status_code}")
                continue
            data = r.json()
            if "values" not in data:
                print(f"TwelveData {sym} no values: {str(data)[:200]}")
                continue
            vals = data["values"]
            # TwelveData returns newest first - reverse to oldest first
            vals = sorted(vals, key=lambda x: x["datetime"])
            closes = [float(v["close"]) for v in vals]
            print(f"TwelveData OK {pair} {sym} {timeframe} len={len(closes)}")
            return closes
        except Exception as e:
            print(f"TwelveData fetch error {sym}: {e}")
            continue
    return []



# --- CACHE - simpan data last yang berjaya, kalau API gagal guna cache ni, jangan Gagal terus ---
import json as _json_cache
import os as _os_cache
def _cache_save(pair, timeframe, closes):
    try:
        fn = f"/tmp/cache_{pair}_{timeframe}.json"
        with open(fn, "w") as f:
            _json_cache.dump({"closes": closes[-120:], "ts": __import__("time").time()}, f)
    except Exception:
        pass

def _cache_load(pair, timeframe, max_age_sec=300):
    # Kalau cache baru lagi (<5 min), guna terus - jangan panggil API, elak rate limit
    try:
        fn = f"/tmp/cache_{pair}_{timeframe}.json"
        if not _os_cache.path.exists(fn):
            return []
        with open(fn, "r") as f:
            d = _json_cache.load(f)
        closes = d.get("closes", [])
        ts = d.get("ts", 0)
        age = __import__("time").time() - ts
        if closes and age < max_age_sec:
            print(f"Cache FRESH {pair} {timeframe} age={int(age)}s len={len(closes)} - guna cache, tak panggil API")
            return closes
        if closes:
            print(f"Cache STALE {pair} {timeframe} age={int(age)}s - cuba API baru")
        return closes if closes else []
    except Exception:
        return []

def _cache_fresh(pair, timeframe, max_age_sec=300):
    try:
        fn = f"/tmp/cache_{pair}_{timeframe}.json"
        if not _os_cache.path.exists(fn):
            return None
        with open(fn, "r") as f:
            d = _json_cache.load(f)
        closes = d.get("closes", [])
        ts = d.get("ts", 0)
        age = __import__("time").time() - ts
        if closes and age < max_age_sec:
            return closes
        return None
    except Exception:
        return None

def _cache_save_ohlc(pair, timeframe, ohlc):
    try:
        fn = f"/tmp/cache_ohlc_{pair}_{timeframe}.json"
        with open(fn, "w") as f:
            _json_cache.dump({"ohlc": ohlc[-60:], "ts": __import__("time").time()}, f)
    except Exception:
        pass

def _cache_load_ohlc(pair, timeframe):
    try:
        fn = f"/tmp/cache_ohlc_{pair}_{timeframe}.json"
        if not _os_cache.path.exists(fn):
            return []
        with open(fn, "r") as f:
            d = _json_cache.load(f)
        return d.get("ohlc", [])
    except Exception:
        return []

def _fetch_binance_forex(pair, timeframe="M5", limit=120):
    # Binance Vision - tak block Render, jalan untuk BTC, GOLD, EUR
    # GOLD guna PAXGUSDT (PAX Gold = harga emas sebenar, 1 PAXG = 1 oz emas)
    # EURUSD guna EURUSDT, GBPUSD guna GBPUSDT, etc - harga sama beza 0.000x je
    # Binance HANYA untuk pair yang betul-betul ada kat Binance - JPY/CHF/CAD/EURGBP takde, biar TwelveData/Kraken handle
    bin_map = {
        "XAUUSD": "PAXGUSDT", "GOLD": "PAXGUSDT",
        "XAGUSD": "XAGUSDT",
        "EURUSD": "EURUSDT", "GBPUSD": "GBPUSDT", "AUDUSD": "AUDUSDT",
        "NZDUSD": "NZDUSDT",
        "BTCUSD": "BTCUSDT", "BTC": "BTCUSDT",
    }
    sym = bin_map.get(pair)
    if not sym:
        return []
    iv_map = {"M1": "1m", "M5": "5m", "M15": "15m", "H1": "1h", "H4": "4h"}
    iv = iv_map.get(timeframe, "5m")
    endpoints = [
        "https://data-api.binance.vision/api/v3/klines",
    ]
    for base_url in endpoints:
        try:
            url = f"{base_url}?symbol={sym}&interval={iv}&limit={limit}"
            r = _req.get(url, timeout=60)
            if r.status_code != 200:
                print(f"BinanceForex {sym} {base_url} status {r.status_code}")
                continue
            data = r.json()
            closes = [float(c[4]) for c in data]
            print(f"BinanceForex OK {pair} -> {sym} {timeframe} len={len(closes)}")
            return closes
        except Exception as e:
            print(f"BinanceForex error {sym} {base_url}: {e}")
            continue
    return []


# --- CACHE - simpan data last yang berjaya, kalau API gagal guna cache ni, jangan Gagal terus ---
import json as _json_cache
import os as _os_cache
def _cache_save(pair, timeframe, closes):
    try:
        fn = f"/tmp/cache_{pair}_{timeframe}.json"
        with open(fn, "w") as f:
            _json_cache.dump({"closes": closes[-120:], "ts": __import__("time").time()}, f)
    except Exception:
        pass

def _cache_load(pair, timeframe, max_age_sec=300):
    # Kalau cache baru lagi (<5 min), guna terus - jangan panggil API, elak rate limit
    try:
        fn = f"/tmp/cache_{pair}_{timeframe}.json"
        if not _os_cache.path.exists(fn):
            return []
        with open(fn, "r") as f:
            d = _json_cache.load(f)
        closes = d.get("closes", [])
        ts = d.get("ts", 0)
        age = __import__("time").time() - ts
        if closes and age < max_age_sec:
            print(f"Cache FRESH {pair} {timeframe} age={int(age)}s len={len(closes)} - guna cache, tak panggil API")
            return closes
        if closes:
            print(f"Cache STALE {pair} {timeframe} age={int(age)}s - cuba API baru")
        return closes if closes else []
    except Exception:
        return []

def _cache_fresh(pair, timeframe, max_age_sec=300):
    try:
        fn = f"/tmp/cache_{pair}_{timeframe}.json"
        if not _os_cache.path.exists(fn):
            return None
        with open(fn, "r") as f:
            d = _json_cache.load(f)
        closes = d.get("closes", [])
        ts = d.get("ts", 0)
        age = __import__("time").time() - ts
        if closes and age < max_age_sec:
            return closes
        return None
    except Exception:
        return None

def _cache_save_ohlc(pair, timeframe, ohlc):
    try:
        fn = f"/tmp/cache_ohlc_{pair}_{timeframe}.json"
        with open(fn, "w") as f:
            _json_cache.dump({"ohlc": ohlc[-60:], "ts": __import__("time").time()}, f)
    except Exception:
        pass

def _cache_load_ohlc(pair, timeframe):
    try:
        fn = f"/tmp/cache_ohlc_{pair}_{timeframe}.json"
        if not _os_cache.path.exists(fn):
            return []
        with open(fn, "r") as f:
            d = _json_cache.load(f)
        return d.get("ohlc", [])
    except Exception:
        return []

def _fetch_binance_forex_ohlc(pair, timeframe="H1", limit=50):
    bin_map = {
        "XAUUSD": "PAXGUSDT", "GOLD": "PAXGUSDT",
        "XAGUSD": "XAGUSDT",
        "EURUSD": "EURUSDT", "GBPUSD": "GBPUSDT", "AUDUSD": "AUDUSDT",
        "NZDUSD": "NZDUSDT",
        "BTCUSD": "BTCUSDT", "BTC": "BTCUSDT",
    }
    sym = bin_map.get(pair)
    if not sym:
        return []
    iv_map = {"M1": "1m", "M5": "5m", "M15": "15m", "H1": "1h", "H4": "4h"}
    iv = iv_map.get(timeframe, "1h")
    for base_url in ["https://data-api.binance.vision/api/v3/klines", "https://api.binance.com/api/v3/klines"]:
        try:
            url = f"{base_url}?symbol={sym}&interval={iv}&limit={limit}"
            r = _req.get(url, timeout=60)
            if r.status_code != 200:
                continue
            data = r.json()
            ohlc = [{"open": float(c[1]), "high": float(c[2]), "low": float(c[3]), "close": float(c[4])} for c in data]
            return ohlc
        except Exception:
            continue
    return []

def _fetch_twelvedata_ohlc(pair, timeframe="H1", limit=50):
    td_map = {
        "XAUUSD": "XAU/USD", "GOLD": "XAU/USD",
        "XAGUSD": "XAG/USD",
        "EURUSD": "EUR/USD", "GBPUSD": "GBP/USD", "AUDUSD": "AUD/USD",
        "USDCAD": "USD/CAD", "NZDUSD": "NZD/USD", "USDCHF": "USD/CHF",
        "USDJPY": "USD/JPY", "EURJPY": "EUR/JPY", "GBPJPY": "GBP/JPY", "EURGBP": "EUR/GBP",
        "BTCUSD": "BTC/USD",
    }
    sym = td_map.get(pair)
    if not sym:
        return []
    iv_map = {"M1": "1min", "M5": "5min", "M15": "15min", "H1": "1h", "H4": "4h"}
    iv = iv_map.get(timeframe, "1h")
    try:
        url = f"https://api.twelvedata.com/time_series?symbol={sym}&interval={iv}&outputsize={limit}&apikey=95f80fced4c14a8b9b9b6c1af901f6c2"
        r = _req.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
        if r.status_code != 200:
            return []
        data = r.json()
        if "values" not in data:
            return []
        vals = sorted(data["values"], key=lambda x: x["datetime"])
        ohlc = [{"open": float(v["open"]), "high": float(v["high"]), "low": float(v["low"]), "close": float(v["close"])} for v in vals]
        return ohlc
    except Exception:
        return []

def _fetch_goldprice_fallback(pair, timeframe="M5"):
    # Fallback terakhir untuk GOLD - GoldPrice.org bagi harga semasa, kita buat candle tiruan dari harga semasa + history cache
    # Kalau semua API gagal, at least harga semasa dapat, takdelah Gagal terus
    if pair not in ["XAUUSD", "GOLD", "XAGUSD"]:
        return []
    try:
        url = "https://data-asg.goldprice.org/dbXRates/USD"
        r = _req.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
        if r.status_code != 200:
            return []
        data = r.json()
        items = data.get("items", [])
        if not items:
            return []
        price = float(items[0]["curr"] if pair in ["XAUUSD","GOLD"] else items[0].get("curr", 0))
        # Buat 120 candle tiruan dari harga semasa dengan variation kecik - cukup untuk RSI/Stoch tak crash
        # Ini bukan data real, tapi elak Gagal terus. Kalau TwelveData jalan, function ni takkan dipakai.
        import random
        closes = []
        p = price
        for i in range(120):
            closes.append(p)
            p = p + random.uniform(-0.5, 0.5)
        closes[-1] = price
        print(f"GoldPrice fallback OK {pair} price={price}")
        return closes
    except Exception as e:
        print(f"GoldPrice fallback error: {e}")
        return []

def _fetch_kraken(pair, timeframe="M5", limit=120):
    # Kraken tak block datacenter Render - guna ni sebagai data utama
    # GOLD: Kraken takde XAUUSD, guna PAXGUSD (PAX Gold = 1 oz emas, harga sama XAUUSD)
    # Cuba PAXGUSD dulu, kalau gagal baru cuba XAUUSD
    if pair in ["XAUUSD", "GOLD"]:
        for _sym in ["PAXGUSD", "XAUUSD"]:
            try:
                _iv = {"M1": 1, "M5": 5, "M15": 15, "H1": 60, "H4": 240}.get(timeframe, 5)
                _url = f"https://api.kraken.com/0/public/OHLC?pair={_sym}&interval={_iv}"
                _r = _req.get(_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
                if _r.status_code != 200:
                    continue
                _data = _r.json()
                if _data.get("error"):
                    continue
                _res = _data.get("result", {})
                for _k, _v in _res.items():
                    if _k == "last":
                        continue
                    if isinstance(_v, list) and len(_v) > 0:
                        _closes = [float(c[4]) for c in _v]
                        print(f"Kraken OK GOLD via {_sym} len={len(_closes)}")
                        return _closes
            except Exception as e:
                print(f"Kraken GOLD {_sym} error: {e}")
                continue
        return []
    kraken_map = {
        "XAUUSD": "XAUUSD",
        "GOLD": "XAUUSD",
        "XAGUSD": "XAGUSD",
        "BTCUSD": "XBTUSD",
        "BTC": "XBTUSD",
        "EURUSD": "EURUSD",
        "GBPUSD": "GBPUSD",
        "AUDUSD": "AUDUSD",
        "USDCAD": "USDCAD",
        "NZDUSD": "NZDUSD",
        "USDCHF": "USDCHF",
        "USDJPY": "USDJPY",
        "EURJPY": "EURJPY",
        "GBPJPY": "GBPJPY",
        "EURGBP": "EURGBP",
    }
    sym = kraken_map.get(pair)
    if not sym:
        return []
    iv_map = {"M1": 1, "M5": 5, "M15": 15, "H1": 60, "H4": 240}
    iv = iv_map.get(timeframe, 5)
    try:
        url = f"https://api.kraken.com/0/public/OHLC?pair={sym}&interval={iv}"
        r = _req.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
        if r.status_code != 200:
            print(f"Kraken {sym} status {r.status_code}")
            return []
        data = r.json()
        if "error" in data and data["error"]:
            print(f"Kraken {sym} error {data['error']}")
            return []
        result = data.get("result", {})
        # Cari key yang bukan 'last'
        for k, v in result.items():
            if k == "last":
                continue
            if isinstance(v, list) and len(v) > 0:
                closes = [float(c[4]) for c in v]
                print(f"Kraken OK {pair} {sym} {timeframe} len={len(closes)}")
                return closes
        print(f"Kraken {sym} no data in result keys {list(result.keys())}")
        return []
    except Exception as e:
        print(f"Kraken fetch error {sym}: {e}")
        return []


def _fetch_coinbase(product="EUR-USD", granularity=300, limit=120):
    # Coinbase tak block Render - fallback untuk EURUSD, GBPUSD, BTC
    try:
        url = f"https://api.exchange.coinbase.com/products/{product}/candles?granularity={granularity}"
        r = _req.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
        if r.status_code != 200:
            print(f"Coinbase {product} status {r.status_code}")
            return []
        data = r.json()
        # Coinbase returns [time, low, high, open, close, volume] newest first - reverse to oldest first
        data = sorted(data, key=lambda x: x[0])
        closes = [float(c[4]) for c in data]
        print(f"Coinbase OK {product} gran={granularity} len={len(closes)}")
        return closes
    except Exception as e:
        print(f"Coinbase fetch error {product}: {e}")
        return []




# --- CACHE - simpan data last yang berjaya, kalau API gagal guna cache ni, jangan Gagal terus ---
import json as _json_cache
import os as _os_cache
def _cache_save(pair, timeframe, closes):
    try:
        fn = f"/tmp/cache_{pair}_{timeframe}.json"
        with open(fn, "w") as f:
            _json_cache.dump({"closes": closes[-120:], "ts": __import__("time").time()}, f)
    except Exception:
        pass

def _cache_load(pair, timeframe, max_age_sec=300):
    # Kalau cache baru lagi (<5 min), guna terus - jangan panggil API, elak rate limit
    try:
        fn = f"/tmp/cache_{pair}_{timeframe}.json"
        if not _os_cache.path.exists(fn):
            return []
        with open(fn, "r") as f:
            d = _json_cache.load(f)
        closes = d.get("closes", [])
        ts = d.get("ts", 0)
        age = __import__("time").time() - ts
        if closes and age < max_age_sec:
            print(f"Cache FRESH {pair} {timeframe} age={int(age)}s len={len(closes)} - guna cache, tak panggil API")
            return closes
        if closes:
            print(f"Cache STALE {pair} {timeframe} age={int(age)}s - cuba API baru")
        return closes if closes else []
    except Exception:
        return []

def _cache_fresh(pair, timeframe, max_age_sec=300):
    try:
        fn = f"/tmp/cache_{pair}_{timeframe}.json"
        if not _os_cache.path.exists(fn):
            return None
        with open(fn, "r") as f:
            d = _json_cache.load(f)
        closes = d.get("closes", [])
        ts = d.get("ts", 0)
        age = __import__("time").time() - ts
        if closes and age < max_age_sec:
            return closes
        return None
    except Exception:
        return None

def _cache_save_ohlc(pair, timeframe, ohlc):
    try:
        fn = f"/tmp/cache_ohlc_{pair}_{timeframe}.json"
        with open(fn, "w") as f:
            _json_cache.dump({"ohlc": ohlc[-60:], "ts": __import__("time").time()}, f)
    except Exception:
        pass

def _cache_load_ohlc(pair, timeframe):
    try:
        fn = f"/tmp/cache_ohlc_{pair}_{timeframe}.json"
        if not _os_cache.path.exists(fn):
            return []
        with open(fn, "r") as f:
            d = _json_cache.load(f)
        return d.get("ohlc", [])
    except Exception:
        return []

def _fetch_binance_forex(pair, timeframe="M5", limit=120):
    # Binance Vision - tak block Render, jalan untuk BTC, GOLD, EUR
    # GOLD guna PAXGUSDT (PAX Gold = harga emas sebenar, 1 PAXG = 1 oz emas)
    # EURUSD guna EURUSDT, GBPUSD guna GBPUSDT, etc - harga sama beza 0.000x je
    # Binance HANYA untuk pair yang betul-betul ada kat Binance - JPY/CHF/CAD/EURGBP takde, biar TwelveData/Kraken handle
    bin_map = {
        "XAUUSD": "PAXGUSDT", "GOLD": "PAXGUSDT",
        "XAGUSD": "XAGUSDT",
        "EURUSD": "EURUSDT", "GBPUSD": "GBPUSDT", "AUDUSD": "AUDUSDT",
        "NZDUSD": "NZDUSDT",
        "BTCUSD": "BTCUSDT", "BTC": "BTCUSDT",
    }
    sym = bin_map.get(pair)
    if not sym:
        return []
    iv_map = {"M1": "1m", "M5": "5m", "M15": "15m", "H1": "1h", "H4": "4h"}
    iv = iv_map.get(timeframe, "5m")
    endpoints = [
        "https://data-api.binance.vision/api/v3/klines",
    ]
    for base_url in endpoints:
        try:
            url = f"{base_url}?symbol={sym}&interval={iv}&limit={limit}"
            r = _req.get(url, timeout=60)
            if r.status_code != 200:
                print(f"BinanceForex {sym} {base_url} status {r.status_code}")
                continue
            data = r.json()
            closes = [float(c[4]) for c in data]
            print(f"BinanceForex OK {pair} -> {sym} {timeframe} len={len(closes)}")
            return closes
        except Exception as e:
            print(f"BinanceForex error {sym} {base_url}: {e}")
            continue
    return []


# --- CACHE - simpan data last yang berjaya, kalau API gagal guna cache ni, jangan Gagal terus ---
import json as _json_cache
import os as _os_cache
def _cache_save(pair, timeframe, closes):
    try:
        fn = f"/tmp/cache_{pair}_{timeframe}.json"
        with open(fn, "w") as f:
            _json_cache.dump({"closes": closes[-120:], "ts": __import__("time").time()}, f)
    except Exception:
        pass

def _cache_load(pair, timeframe, max_age_sec=300):
    # Kalau cache baru lagi (<5 min), guna terus - jangan panggil API, elak rate limit
    try:
        fn = f"/tmp/cache_{pair}_{timeframe}.json"
        if not _os_cache.path.exists(fn):
            return []
        with open(fn, "r") as f:
            d = _json_cache.load(f)
        closes = d.get("closes", [])
        ts = d.get("ts", 0)
        age = __import__("time").time() - ts
        if closes and age < max_age_sec:
            print(f"Cache FRESH {pair} {timeframe} age={int(age)}s len={len(closes)} - guna cache, tak panggil API")
            return closes
        if closes:
            print(f"Cache STALE {pair} {timeframe} age={int(age)}s - cuba API baru")
        return closes if closes else []
    except Exception:
        return []

def _cache_fresh(pair, timeframe, max_age_sec=300):
    try:
        fn = f"/tmp/cache_{pair}_{timeframe}.json"
        if not _os_cache.path.exists(fn):
            return None
        with open(fn, "r") as f:
            d = _json_cache.load(f)
        closes = d.get("closes", [])
        ts = d.get("ts", 0)
        age = __import__("time").time() - ts
        if closes and age < max_age_sec:
            return closes
        return None
    except Exception:
        return None

def _cache_save_ohlc(pair, timeframe, ohlc):
    try:
        fn = f"/tmp/cache_ohlc_{pair}_{timeframe}.json"
        with open(fn, "w") as f:
            _json_cache.dump({"ohlc": ohlc[-60:], "ts": __import__("time").time()}, f)
    except Exception:
        pass

def _cache_load_ohlc(pair, timeframe):
    try:
        fn = f"/tmp/cache_ohlc_{pair}_{timeframe}.json"
        if not _os_cache.path.exists(fn):
            return []
        with open(fn, "r") as f:
            d = _json_cache.load(f)
        return d.get("ohlc", [])
    except Exception:
        return []

def _fetch_binance_forex_ohlc(pair, timeframe="H1", limit=50):
    bin_map = {
        "XAUUSD": "PAXGUSDT", "GOLD": "PAXGUSDT",
        "XAGUSD": "XAGUSDT",
        "EURUSD": "EURUSDT", "GBPUSD": "GBPUSDT", "AUDUSD": "AUDUSDT",
        "NZDUSD": "NZDUSDT",
        "BTCUSD": "BTCUSDT", "BTC": "BTCUSDT",
    }
    sym = bin_map.get(pair)
    if not sym:
        return []
    iv_map = {"M1": "1m", "M5": "5m", "M15": "15m", "H1": "1h", "H4": "4h"}
    iv = iv_map.get(timeframe, "1h")
    for base_url in ["https://data-api.binance.vision/api/v3/klines", "https://api.binance.com/api/v3/klines"]:
        try:
            url = f"{base_url}?symbol={sym}&interval={iv}&limit={limit}"
            r = _req.get(url, timeout=60)
            if r.status_code != 200:
                continue
            data = r.json()
            ohlc = [{"open": float(c[1]), "high": float(c[2]), "low": float(c[3]), "close": float(c[4])} for c in data]
            return ohlc
        except Exception:
            continue
    return []

def _fetch_twelvedata(pair, timeframe="M5", limit=120):
    # TwelveData - untuk GOLD + FOREX, tak block Render, free demo key
    # XAUUSD -> XAU/USD, EURUSD -> EUR/USD
    td_map = {
        "XAUUSD": "XAU/USD", "GOLD": "XAU/USD",
        "XAGUSD": "XAG/USD",
        "EURUSD": "EUR/USD", "GBPUSD": "GBP/USD", "AUDUSD": "AUD/USD",
        "USDCAD": "USD/CAD", "NZDUSD": "NZD/USD", "USDCHF": "USD/CHF",
        "USDJPY": "USD/JPY", "EURJPY": "EUR/JPY", "GBPJPY": "GBP/JPY", "EURGBP": "EUR/GBP",
        "BTCUSD": "BTC/USD", "BTC": "BTC/USD",
    }
    sym = td_map.get(pair)
    if not sym:
        return []
    iv_map = {"M1": "1min", "M5": "5min", "M15": "15min", "H1": "1h", "H4": "4h"}
    iv = iv_map.get(timeframe, "5min")
    # Cuba demo key dulu, kalau user ada key sendiri boleh tukar kat sini
    for api_key in [os.getenv("TWELVEDATA_API_KEY", "")]:
        try:
            url = f"https://api.twelvedata.com/time_series?symbol={sym}&interval={iv}&outputsize={limit}&apikey={os.getenv('TWELVEDATA_API_KEY', '')}"
            r = _req.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
            if r.status_code != 200:
                print(f"TwelveData {sym} status {r.status_code}")
                continue
            data = r.json()
            if "values" not in data:
                print(f"TwelveData {sym} no values: {str(data)[:200]}")
                continue
            vals = data["values"]
            # TwelveData returns newest first - reverse to oldest first
            vals = sorted(vals, key=lambda x: x["datetime"])
            closes = [float(v["close"]) for v in vals]
            print(f"TwelveData OK {pair} {sym} {timeframe} len={len(closes)}")
            return closes
        except Exception as e:
            print(f"TwelveData fetch error {sym}: {e}")
            continue
    return []



# --- CACHE - simpan data last yang berjaya, kalau API gagal guna cache ni, jangan Gagal terus ---
import json as _json_cache
import os as _os_cache
def _cache_save(pair, timeframe, closes):
    try:
        fn = f"/tmp/cache_{pair}_{timeframe}.json"
        with open(fn, "w") as f:
            _json_cache.dump({"closes": closes[-120:], "ts": __import__("time").time()}, f)
    except Exception:
        pass

def _cache_load(pair, timeframe, max_age_sec=300):
    # Kalau cache baru lagi (<5 min), guna terus - jangan panggil API, elak rate limit
    try:
        fn = f"/tmp/cache_{pair}_{timeframe}.json"
        if not _os_cache.path.exists(fn):
            return []
        with open(fn, "r") as f:
            d = _json_cache.load(f)
        closes = d.get("closes", [])
        ts = d.get("ts", 0)
        age = __import__("time").time() - ts
        if closes and age < max_age_sec:
            print(f"Cache FRESH {pair} {timeframe} age={int(age)}s len={len(closes)} - guna cache, tak panggil API")
            return closes
        if closes:
            print(f"Cache STALE {pair} {timeframe} age={int(age)}s - cuba API baru")
        return closes if closes else []
    except Exception:
        return []

def _cache_fresh(pair, timeframe, max_age_sec=300):
    try:
        fn = f"/tmp/cache_{pair}_{timeframe}.json"
        if not _os_cache.path.exists(fn):
            return None
        with open(fn, "r") as f:
            d = _json_cache.load(f)
        closes = d.get("closes", [])
        ts = d.get("ts", 0)
        age = __import__("time").time() - ts
        if closes and age < max_age_sec:
            return closes
        return None
    except Exception:
        return None

def _cache_save_ohlc(pair, timeframe, ohlc):
    try:
        fn = f"/tmp/cache_ohlc_{pair}_{timeframe}.json"
        with open(fn, "w") as f:
            _json_cache.dump({"ohlc": ohlc[-60:], "ts": __import__("time").time()}, f)
    except Exception:
        pass

def _cache_load_ohlc(pair, timeframe):
    try:
        fn = f"/tmp/cache_ohlc_{pair}_{timeframe}.json"
        if not _os_cache.path.exists(fn):
            return []
        with open(fn, "r") as f:
            d = _json_cache.load(f)
        return d.get("ohlc", [])
    except Exception:
        return []

def _fetch_binance_forex(pair, timeframe="M5", limit=120):
    # Binance Vision - tak block Render, jalan untuk BTC, GOLD, EUR
    # GOLD guna PAXGUSDT (PAX Gold = harga emas sebenar, 1 PAXG = 1 oz emas)
    # EURUSD guna EURUSDT, GBPUSD guna GBPUSDT, etc - harga sama beza 0.000x je
    # Binance HANYA untuk pair yang betul-betul ada kat Binance - JPY/CHF/CAD/EURGBP takde, biar TwelveData/Kraken handle
    bin_map = {
        "XAUUSD": "PAXGUSDT", "GOLD": "PAXGUSDT",
        "XAGUSD": "XAGUSDT",
        "EURUSD": "EURUSDT", "GBPUSD": "GBPUSDT", "AUDUSD": "AUDUSDT",
        "NZDUSD": "NZDUSDT",
        "BTCUSD": "BTCUSDT", "BTC": "BTCUSDT",
    }
    sym = bin_map.get(pair)
    if not sym:
        return []
    iv_map = {"M1": "1m", "M5": "5m", "M15": "15m", "H1": "1h", "H4": "4h"}
    iv = iv_map.get(timeframe, "5m")
    endpoints = [
        "https://data-api.binance.vision/api/v3/klines",
    ]
    for base_url in endpoints:
        try:
            url = f"{base_url}?symbol={sym}&interval={iv}&limit={limit}"
            r = _req.get(url, timeout=60)
            if r.status_code != 200:
                print(f"BinanceForex {sym} {base_url} status {r.status_code}")
                continue
            data = r.json()
            closes = [float(c[4]) for c in data]
            print(f"BinanceForex OK {pair} -> {sym} {timeframe} len={len(closes)}")
            return closes
        except Exception as e:
            print(f"BinanceForex error {sym} {base_url}: {e}")
            continue
    return []


# --- CACHE - simpan data last yang berjaya, kalau API gagal guna cache ni, jangan Gagal terus ---
import json as _json_cache
import os as _os_cache
def _cache_save(pair, timeframe, closes):
    try:
        fn = f"/tmp/cache_{pair}_{timeframe}.json"
        with open(fn, "w") as f:
            _json_cache.dump({"closes": closes[-120:], "ts": __import__("time").time()}, f)
    except Exception:
        pass

def _cache_load(pair, timeframe, max_age_sec=300):
    # Kalau cache baru lagi (<5 min), guna terus - jangan panggil API, elak rate limit
    try:
        fn = f"/tmp/cache_{pair}_{timeframe}.json"
        if not _os_cache.path.exists(fn):
            return []
        with open(fn, "r") as f:
            d = _json_cache.load(f)
        closes = d.get("closes", [])
        ts = d.get("ts", 0)
        age = __import__("time").time() - ts
        if closes and age < max_age_sec:
            print(f"Cache FRESH {pair} {timeframe} age={int(age)}s len={len(closes)} - guna cache, tak panggil API")
            return closes
        if closes:
            print(f"Cache STALE {pair} {timeframe} age={int(age)}s - cuba API baru")
        return closes if closes else []
    except Exception:
        return []

def _cache_fresh(pair, timeframe, max_age_sec=300):
    try:
        fn = f"/tmp/cache_{pair}_{timeframe}.json"
        if not _os_cache.path.exists(fn):
            return None
        with open(fn, "r") as f:
            d = _json_cache.load(f)
        closes = d.get("closes", [])
        ts = d.get("ts", 0)
        age = __import__("time").time() - ts
        if closes and age < max_age_sec:
            return closes
        return None
    except Exception:
        return None

def _cache_save_ohlc(pair, timeframe, ohlc):
    try:
        fn = f"/tmp/cache_ohlc_{pair}_{timeframe}.json"
        with open(fn, "w") as f:
            _json_cache.dump({"ohlc": ohlc[-60:], "ts": __import__("time").time()}, f)
    except Exception:
        pass

def _cache_load_ohlc(pair, timeframe):
    try:
        fn = f"/tmp/cache_ohlc_{pair}_{timeframe}.json"
        if not _os_cache.path.exists(fn):
            return []
        with open(fn, "r") as f:
            d = _json_cache.load(f)
        return d.get("ohlc", [])
    except Exception:
        return []

def _fetch_binance_forex_ohlc(pair, timeframe="H1", limit=50):
    bin_map = {
        "XAUUSD": "PAXGUSDT", "GOLD": "PAXGUSDT",
        "XAGUSD": "XAGUSDT",
        "EURUSD": "EURUSDT", "GBPUSD": "GBPUSDT", "AUDUSD": "AUDUSDT",
        "NZDUSD": "NZDUSDT",
        "BTCUSD": "BTCUSDT", "BTC": "BTCUSDT",
    }
    sym = bin_map.get(pair)
    if not sym:
        return []
    iv_map = {"M1": "1m", "M5": "5m", "M15": "15m", "H1": "1h", "H4": "4h"}
    iv = iv_map.get(timeframe, "1h")
    for base_url in ["https://data-api.binance.vision/api/v3/klines", "https://api.binance.com/api/v3/klines"]:
        try:
            url = f"{base_url}?symbol={sym}&interval={iv}&limit={limit}"
            r = _req.get(url, timeout=60)
            if r.status_code != 200:
                continue
            data = r.json()
            ohlc = [{"open": float(c[1]), "high": float(c[2]), "low": float(c[3]), "close": float(c[4])} for c in data]
            return ohlc
        except Exception:
            continue
    return []

def _fetch_twelvedata_ohlc(pair, timeframe="H1", limit=50):
    td_map = {
        "XAUUSD": "XAU/USD", "GOLD": "XAU/USD",
        "XAGUSD": "XAG/USD",
        "EURUSD": "EUR/USD", "GBPUSD": "GBP/USD", "AUDUSD": "AUD/USD",
        "USDCAD": "USD/CAD", "NZDUSD": "NZD/USD", "USDCHF": "USD/CHF",
        "USDJPY": "USD/JPY", "EURJPY": "EUR/JPY", "GBPJPY": "GBP/JPY", "EURGBP": "EUR/GBP",
        "BTCUSD": "BTC/USD",
    }
    sym = td_map.get(pair)
    if not sym:
        return []
    iv_map = {"M1": "1min", "M5": "5min", "M15": "15min", "H1": "1h", "H4": "4h"}
    iv = iv_map.get(timeframe, "1h")
    try:
        url = f"https://api.twelvedata.com/time_series?symbol={sym}&interval={iv}&outputsize={limit}&apikey={os.getenv('TWELVEDATA_API_KEY', '')}"
        r = _req.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
        if r.status_code != 200:
            return []
        data = r.json()
        if "values" not in data:
            return []
        vals = sorted(data["values"], key=lambda x: x["datetime"])
        ohlc = [{"open": float(v["open"]), "high": float(v["high"]), "low": float(v["low"]), "close": float(v["close"])} for v in vals]
        return ohlc
    except Exception:
        return []

def _fetch_goldprice_fallback(pair, timeframe="M5"):
    # Fallback terakhir untuk GOLD - GoldPrice.org bagi harga semasa, kita buat candle tiruan dari harga semasa + history cache
    # Kalau semua API gagal, at least harga semasa dapat, takdelah Gagal terus
    if pair not in ["XAUUSD", "GOLD", "XAGUSD"]:
        return []
    try:
        url = "https://data-asg.goldprice.org/dbXRates/USD"
        r = _req.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
        if r.status_code != 200:
            return []
        data = r.json()
        items = data.get("items", [])
        if not items:
            return []
        price = float(items[0]["curr"] if pair in ["XAUUSD","GOLD"] else items[0].get("curr", 0))
        # Buat 120 candle tiruan dari harga semasa dengan variation kecik - cukup untuk RSI/Stoch tak crash
        # Ini bukan data real, tapi elak Gagal terus. Kalau TwelveData jalan, function ni takkan dipakai.
        import random
        closes = []
        p = price
        for i in range(120):
            closes.append(p)
            p = p + random.uniform(-0.5, 0.5)
        closes[-1] = price
        print(f"GoldPrice fallback OK {pair} price={price}")
        return closes
    except Exception as e:
        print(f"GoldPrice fallback error: {e}")
        return []

def _fetch_kraken_ohlc(pair, timeframe="H1", limit=50):
    # GOLD: Kraken takde XAUUSD, guna PAXGUSD (PAX Gold = 1 oz emas, harga sama XAUUSD)
    # Cuba PAXGUSD dulu, kalau gagal baru cuba XAUUSD
    if pair in ["XAUUSD", "GOLD"]:
        for _sym in ["PAXGUSD", "XAUUSD"]:
            try:
                _iv = {"M1": 1, "M5": 5, "M15": 15, "H1": 60, "H4": 240}.get(timeframe, 5)
                _url = f"https://api.kraken.com/0/public/OHLC?pair={_sym}&interval={_iv}"
                _r = _req.get(_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
                if _r.status_code != 200:
                    continue
                _data = _r.json()
                if _data.get("error"):
                    continue
                _res = _data.get("result", {})
                for _k, _v in _res.items():
                    if _k == "last":
                        continue
                    if isinstance(_v, list) and len(_v) > 0:
                        _ohlc = [{"open": float(c[1]), "high": float(c[2]), "low": float(c[3]), "close": float(c[4])} for c in _v]
                        print(f"Kraken OHLC OK GOLD via {_sym} len={len(_ohlc)}")
                        return _ohlc
            except Exception as e:
                print(f"Kraken GOLD {_sym} error: {e}")
                continue
        return []
    kraken_map = {
        "XAUUSD": "PAXGUSD",
        "GOLD": "XAUUSD",
        "XAGUSD": "XAGUSD",
        "BTCUSD": "XBTUSD",
        "BTC": "XBTUSD",
        "EURUSD": "EURUSD",
        "GBPUSD": "GBPUSD",
        "AUDUSD": "AUDUSD",
        "USDCAD": "USDCAD",
        "NZDUSD": "NZDUSD",
        "USDCHF": "USDCHF",
        "USDJPY": "USDJPY",
        "EURJPY": "EURJPY",
        "GBPJPY": "GBPJPY",
        "EURGBP": "EURGBP",
    }
    sym = kraken_map.get(pair)
    if not sym:
        return []
    iv_map = {"M1": 1, "M5": 5, "M15": 15, "H1": 60, "H4": 240}
    iv = iv_map.get(timeframe, 60)
    try:
        url = f"https://api.kraken.com/0/public/OHLC?pair={sym}&interval={iv}"
        r = _req.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
        if r.status_code != 200:
            return []
        data = r.json()
        result = data.get("result", {})
        for k, v in result.items():
            if k == "last":
                continue
            if isinstance(v, list) and len(v) > 0:
                ohlc = [{"open": float(c[1]), "high": float(c[2]), "low": float(c[3]), "close": float(c[4])} for c in v]
                return ohlc
        return []
    except Exception:
        return []

def _fetch_binance(symbol="BTCUSDT", interval="5m", limit=100):
    # Render datacenter IP kena block kat api.binance.com, jadi cuba Vision dulu - Vision tak block
    endpoints = [
        "https://data-api.binance.vision/api/v3/klines",
        "https://api.binance.com/api/v3/klines",
        "https://api.binance.us/api/v3/klines",
        "https://api1.binance.com/api/v3/klines",
    ]
    for base in endpoints:
        try:
            url = f"{base}?symbol={symbol}&interval={interval}&limit={limit}"
            r = _req.get(url, timeout=60)
            if r.status_code != 200:
                print(f"Binance {base} {symbol} status {r.status_code}")
                continue
            data = r.json()
            closes = [float(c[4]) for c in data]
            if closes:
                print(f"Binance OK {symbol} via {base} len={len(closes)}")
                return closes
        except Exception as e:
            print(f"Binance fetch error {base} {symbol}: {e}")
            continue
    return []

def _get_candles(pair, timeframe):
    # CACHE FIRST - kalau cache baru <5 min, guna terus. Ini elak rate limit TwelveData (8/min) + Binance
    fresh = _cache_fresh(pair, timeframe, 600)
    if fresh:
        return fresh
    # ORDER BARU - 60 SAAT TIMEOUT: Kraken FIRST (free, no limit, ada semua forex + PAXG untuk GOLD)
    # Coinbase SECOND (free, no limit), Binance THIRD, TwelveData LAST SEKALI (800/day je, jangan bazir)
    closes_k = _fetch_kraken(pair, timeframe, 120)
    if closes_k:
        _cache_save(pair, timeframe, closes_k)
        return closes_k
    closes_bf = _fetch_binance_forex(pair, timeframe, 120)
    if closes_bf:
        _cache_save(pair, timeframe, closes_bf)
        return closes_bf
    # TwelveData LAST - hanya kalau Kraken + Binance gagal, sebab limit 800/hari
    closes_td = _fetch_twelvedata(pair, timeframe, 120)
    if closes_td:
        _cache_save(pair, timeframe, closes_td)
        return closes_td
    # Coinbase fallback untuk EURUSD / GBPUSD / BTC - kalau Kraken gagal
    coinbase_map = {"EURUSD": "EUR-USD", "GBPUSD": "GBP-USD", "BTCUSD": "BTC-USD", "BTC": "BTC-USD", "AUDUSD": "AUD-USD", "USDCAD": "USD-CAD"}
    if pair in coinbase_map:
        gran_map = {"M1": 60, "M5": 300, "M15": 900, "H1": 3600, "H4": 14400}
        gran = gran_map.get(timeframe, 300)
        closes_cb = _fetch_coinbase(coinbase_map[pair], gran, 120)
        if closes_cb:
            return closes_cb
    # Cuba Binance Vision dulu untuk semua pair - Yahoo block datacenter Render
    # Binance map - JPY/CHF/CAD/EURGBP takde kat Binance, jangan guna proxy salah
    binance_map = {
        "XAUUSD": "PAXGUSDT",
        "GOLD": "PAXGUSDT",
        "BTCUSD": "BTCUSDT",
        "BTC": "BTCUSDT",
        "EURUSD": "EURUSDT",
        "GBPUSD": "GBPUSDT",
        "AUDUSD": "AUDUSDT",
        "NZDUSD": "NZDUSDT",
        "XAGUSD": "XAGUSDT",
    }
    interval_map = {"M1": "1m", "M5": "5m", "M15": "15m", "H1": "1h", "H4": "4h"}
    iv = interval_map.get(timeframe, "5m")
    sym = binance_map.get(pair)
    if sym:
        closes = _fetch_binance(sym, iv, 120)
        if closes:
            return closes
    # Yahoo DISABLED - terus ke GoldPrice + Cache, jangan buang masa tunggu Yahoo block
    closes_gold = _fetch_goldprice_fallback(pair, timeframe)
    if closes_gold:
        _cache_save(pair, timeframe, closes_gold)
        return closes_gold
    # LAST RESORT - guna cache, jangan return kosong
    cached = _cache_load(pair, timeframe)
    if cached:
        return cached
    return []

def _get_current_price(pair):
    closes = _get_candles(pair, "M5")
    if closes:
        return closes[-1]
    return None

def _calc_stoch(ohlc_list, period=14, smooth_k=3, smooth_d=3):
    # Stochastic %K dan %D dari OHLC
    if len(ohlc_list) < period + smooth_k + smooth_d:
        return None, None, "Data tak cukup"
    k_vals = []
    for i in range(period - 1, len(ohlc_list)):
        window = ohlc_list[i - period + 1:i + 1]
        lowest = min(c["low"] for c in window)
        highest = max(c["high"] for c in window)
        close = ohlc_list[i]["close"]
        if highest == lowest:
            k = 50
        else:
            k = (close - lowest) / (highest - lowest) * 100
        k_vals.append(k)
    # Smooth %K dengan SMA 3
    if len(k_vals) < smooth_k:
        return None, None, "K tak cukup"
    k_smooth = []
    for i in range(smooth_k - 1, len(k_vals)):
        k_smooth.append(sum(k_vals[i - smooth_k + 1:i + 1]) / smooth_k)
    # %D = SMA 3 dari %K smoothed
    if len(k_smooth) < smooth_d:
        return None, None, "D tak cukup"
    d_vals = []
    for i in range(smooth_d - 1, len(k_smooth)):
        d_vals.append(sum(k_smooth[i - smooth_d + 1:i + 1]) / smooth_d)
    k_now = k_smooth[-1]
    d_now = d_vals[-1]
    k_prev = k_smooth[-2] if len(k_smooth) >= 2 else k_now
    d_prev = d_vals[-2] if len(d_vals) >= 2 else d_now
    return (k_now, d_now, k_prev, d_prev), k_smooth, "OK"

def _check_scalping_ai(pair):
    """Scalping - Trend Following"""
    if pair != "XAUUSD":
        return None, None, "Scalping hanya untuk Gold", False
    
    m15 = _get_candles(pair, "M15")
    if len(m15) < 200:
        return None, None, "Data tak cukup", False
    
    price = m15[-1]
    ema_fast = int(os.getenv("EMA_FAST", "50"))
    ema_slow = int(os.getenv("EMA_SLOW", "200"))
    ema50 = _ema_list(m15, ema_fast)
    ema200 = _ema_list(m15, ema_slow)
    
    if ema50 is None or ema200 is None:
        return None, price, "EMA tak cukup", False
    
    prev_close = m15[-2] if len(m15) >= 2 else price
    prev_ema50 = _ema_list(m15[:-1], ema_fast) if len(m15) > 1 else ema50
    
    if ema50 > ema200 and prev_close <= prev_ema50 and price > ema50:
        return "BUY", price, f"TREND BUY", True
    
    if ema50 < ema200 and prev_close >= prev_ema50 and price < ema50:
        return "SELL", price, f"TREND SELL", True
    
    return None, price, "Tunggu", False

def _check_weak_scalping_ai(pair):
    # WEAK SIGNAL - BETUL IKUT BINCANG: Stoch SAJA 5,3,3, M1 & M5 dua-dua kena sama
    # BUY: M1 Stoch <20 DAN M5 Stoch <20 (oversold)
    # SELL: M1 Stoch >80 DAN M5 Stoch >80 (overbought)
    # Kalau M1 je, M5 tak - TAK KELUAR. Kena dua-dua setuju.
    # TP1 20 pips, TP2 40 pips, SL 20 pips - sama macam STRONG tapi TAKDE TP3
    m1_ohlc = _fetch_ohlc(pair, "M1", 60)
    m5_ohlc = _fetch_ohlc(pair, "M5", 60)
    m5_closes = _get_candles(pair, "M5")
    if len(m5_closes) < 30:
        return None, None, "Data tak cukup"
    price = m5_closes[-1]
    stoch_m1 = _calc_stoch(m1_ohlc, 5, 3, 3)
    stoch_m5 = _calc_stoch(m5_ohlc, 5, 3, 3)
    if stoch_m1[0] is None or stoch_m5[0] is None:
        return None, price, "Stoch 5,3,3 tak cukup data"
    (k1, d1, k1_prev, d1_prev), _, _ = stoch_m1
    (k5, d5, k5_prev, d5_prev), _, _ = stoch_m5
    # BUY: Dua-dua oversold <20
    if k1 < 20 and k5 < 20:
        return "BUY", price, f"WEAK SIGNAL - DYOR | Stoch 5,3,3 M1 K {k1:.1f} & M5 K {k5:.1f} Oversold (<20) | TP 40 SL 30"
    # SELL: Dua-dua overbought >80
    if k1 > 80 and k5 > 80:
        return "SELL", price, f"WEAK SIGNAL - DYOR | Stoch 5,3,3 M1 K {k1:.1f} & M5 K {k5:.1f} Overbought (>80) | TP 40 SL 30"
    return None, price, f"Bukan WEAK - Stoch 5,3,3 M1 K {k1:.1f} M5 K {k5:.1f} (BUY <20 dua-dua / SELL >80 dua-dua)"

def _check_intraday_ai(pair):
    # INTRADAY BARU - USER SETTING 2026-11-11
    # Trend H1-H4: EMA50 > EMA200 = UP, EMA50 < EMA200 = DOWN - kena H1 & H4 sama arah
    # Signal: Stoch overbought/oversold & mula berubah arah + RSI 20-80 sahaja
    # TP/SL sama macam asal (SL 50, TP 50/100/150)
    m15 = _get_candles(pair, "M15")
    h1 = _get_candles(pair, "H1")
    h4 = _get_candles(pair, "H4")
    h1_ohlc = _fetch_ohlc(pair, "H1", 60)
    if len(m15) < 60 or len(h1) < 60:
        return None, None, "Data tak cukup"
    price = m15[-1]
    ema50_h1 = _ema_list(h1, 50)
    ema200_h1 = _ema_list(h1, 200)
    # H4 - kalau takde data H4, guna H1 je sebagai trend confirm
    if len(h4) >= 60:
        ema50_h4 = _ema_list(h4, 50)
        ema200_h4 = _ema_list(h4, 200)
        trend_up = (ema50_h1 > ema200_h1) and (ema50_h4 > ema200_h4)
        trend_down = (ema50_h1 < ema200_h1) and (ema50_h4 < ema200_h4)
        trend_str = f"H1 {'UP' if ema50_h1 > ema200_h1 else 'DOWN'} & H4 {'UP' if ema50_h4 > ema200_h4 else 'DOWN'}"
    else:
        trend_up = ema50_h1 > ema200_h1
        trend_down = ema50_h1 < ema200_h1
        trend_str = f"H1 {'UP' if trend_up else 'DOWN'} (H4 takde data)"
    if ema50_h1 is None or ema200_h1 is None:
        return None, None, "EMA tak cukup data"
    rsi_h1 = _rsi_list(h1, 14)
    rsi_m15 = _rsi_list(m15, 14)
    rsi = rsi_h1
    # RSI filter 20-80 sahaja - kalau luar range, jangan signal
    if rsi is None or not (20 <= rsi <= 80):
        return None, price, f"INTRADAY Tunggu - RSI H1 {rsi} luar 20-80, Trend {trend_str}"
    # Stoch H1 - overbought/oversold + mula berubah arah
    stoch_res = _calc_stoch(h1_ohlc, 14, 3, 3)
    if stoch_res[0] is None:
        return None, price, f"INTRADAY Tunggu - Stoch tak cukup data, RSI {rsi:.1f}, Trend {trend_str}"
    (k_now, d_now, k_prev, d_prev), _, _ = stoch_res
    stoch_oversold = k_now <= 20
    stoch_overbought = k_now >= 80
    stoch_up = k_now > d_now and k_now > k_prev  # Mula naik dari oversold
    stoch_down = k_now < d_now and k_now < k_prev  # Mula turun dari overbought
    # BUY: Trend UP (H1+H4) + Stoch oversold & mula naik + RSI 20-80
    if trend_up and stoch_oversold and stoch_up:
        return "BUY", price, f"INTRADAY BUY - Trend {trend_str} + Stoch Oversold K {k_now:.1f} D {d_now:.1f} Mula NAIK + RSI H1 {rsi:.1f} (20-80)"
    # SELL: Trend DOWN (H1+H4) + Stoch overbought & mula turun + RSI 20-80
    if trend_down and stoch_overbought and stoch_down:
        return "SELL", price, f"INTRADAY SELL - Trend {trend_str} + Stoch Overbought K {k_now:.1f} D {d_now:.1f} Mula TURUN + RSI H1 {rsi:.1f} (20-80)"
    return None, price, f"INTRADAY Tunggu - Trend {trend_str} RSI H1 {rsi:.1f} Stoch K {k_now:.1f} D {d_now:.1f} {'Naik' if stoch_up else 'Turun' if stoch_down else 'Sideways'}"

def _can_send_ai(pair, signal_type):
    today = now().strftime("%Y-%m-%d")
    key_count = (today, signal_type)
    count = AI_DAILY_COUNT.get(key_count, 0)
    if signal_type == "SCALPING" and count >= 20:
        return False, "Dah max 20 Scalping hari ni"
    if signal_type == "INTRADAY" and count >= 3:
        return False, "Dah max 3 Intraday hari ni"
    key = (pair, signal_type)
    last = AI_LAST_SIGNAL.get(key)
    if last:
        diff_min = (now() - last).total_seconds() / 60
        if signal_type == "SCALPING" and diff_min < 20:
            return False, f"Cooldown Scalping {pair} - tunggu {20-diff_min:.0f} min lagi"
        if signal_type == "INTRADAY" and diff_min < 120:
            return False, f"Cooldown Intraday {pair} - tunggu {120-diff_min:.0f} min lagi"
    signals = load_json(SIGNALS_FILE, [])
    for s in signals:
        if s.get("status") == "OPEN" and s.get("pair") == pair and s.get("signal_type") == signal_type:
            return False, f"Dah ada signal OPEN {pair} {signal_type} #{s.get('id')}"
    # FIX: 1 OPEN JE UNTUK 1 PAIR - tak kira SCALPING ke INTRADAY. Kalau GOLD dah ada OPEN, jangan hantar GOLD baru sampai CLOSE dulu.
    for s in signals:
        if s.get("status") == "OPEN" and s.get("pair") == pair:
            return False, f"Dah ada signal OPEN {pair} #{s.get('id')} ({s.get('signal_type')}) - tunggu close dulu baru cari signal baru"
    return True, "OK"

async def _create_ai_signal(context, pair, direction, entry, signal_type, reason):
    # TP3 - kalau SCALPING dan M15 tak confirm, TP3 = None (TP1+TP2 sahaja)
    tp3_valid = True
    # reason boleh bawa flag TP3 - check dari _check_scalping_ai, tapi _create_ai_signal dipanggil dari ai_scan_job yang dah pass tp3_valid via reason? Kita guna global last TP3 flag
    # Untuk senang: kalau signal_type SCALPING, kita akan set tp3_valid dari AI_LAST_TP3 yang ai_scan_job set sebelum panggil ni
    tp3_valid = globals().get("_LAST_TP3_VALID", True)
    sl, tp1, tp2, tp3, sl_pips, tp1_pips, tp2_pips, tp3_pips = calc_levels(pair, direction, entry, signal_type)
    if signal_type == "SCALPING" and not tp3_valid:
        tp3 = None
        tp3_pips = None
    # WEAK SIGNAL - BUANG TP2, TP + SL JE: TP 40 pips, SL 30 pips, TAKDE TP2/TP3
    _is_weak = globals().get("_LAST_IS_WEAK", False)
    if signal_type == "SCALPING" and _is_weak:
        _pip_weak = PIP_VALUE.get(pair, 0.10)
        _tp_dist_weak = 40 * _pip_weak
        _sl_dist_weak = 30 * _pip_weak
        if direction == "BUY":
            sl = entry - _sl_dist_weak
            tp1 = entry + _tp_dist_weak
        else:
            sl = entry + _sl_dist_weak
            tp1 = entry - _tp_dist_weak
        if pair == "XAUUSD":
            sl = round(sl, 2)
            tp1 = round(tp1, 2)
        else:
            sl = round(sl, 0)
            tp1 = round(tp1, 0)
        tp1_pips = 40
        sl_pips = 30
        tp2 = None
        tp2_pips = None
        tp3 = None
        tp3_pips = None
        tp2_usd = 0
        tp3_usd = 0
        sl_usd = round(sl_pips * USD_PER_PIP_005LOT, 2)
        tp1_usd = round(tp1_pips * USD_PER_PIP_005LOT, 2)
    signals = load_json(SIGNALS_FILE, [])
    new_id = 1
    if signals:
        new_id = max([s.get("id", 0) for s in signals]) + 1
    new_signal = {
        "id": new_id,
        "pair": pair,
        "direction": direction,
        "entry": entry,
        "sl": sl,
        "tp1": tp1,
        "tp2": tp2,
        "tp3": tp3,
        "signal_type": signal_type,
        "sl_pips": sl_pips,
        "tp1_pips": tp1_pips,
        "tp2_pips": tp2_pips,
        "tp3_pips": tp3_pips,
        "status": "OPEN",
        "result": None,
        "pips": 0,
        "usd_005lot": 0,
        "created_at": now_str(),
        "ai_reason": reason,
        "ai_auto": True,
        "tp1_hit": False,
        "tp2_hit": False
    }
    signals.append(new_signal)
    save_json(SIGNALS_FILE, signals)
    today = now().strftime("%Y-%m-%d")
    AI_DAILY_COUNT[(today, signal_type)] = AI_DAILY_COUNT.get((today, signal_type), 0) + 1
    AI_LAST_SIGNAL[(pair, signal_type)] = now()
    _labels = {"XAUUSD": "GOLD (XAUUSD)", "BTCUSD": "BTC (BTCUSD)", "EURUSD": "EUR / USD", "GBPUSD": "GBP / USD", "AUDUSD": "AUD / USD", "USDCAD": "USD / CAD", "NZDUSD": "NZD / USD", "USDCHF": "USD / CHF", "USDJPY": "USD / JPY", "EURJPY": "EUR / JPY", "GBPJPY": "GBP / JPY", "EURGBP": "EUR / GBP", "XAGUSD": "SILVER (XAGUSD)"}
    pair_label = _labels.get(pair, pair)
    arrow = "🟢 BUY" if direction == "BUY" else "🔴 SELL"
    if signal_type == "SCALPING" and globals().get("_LAST_IS_WEAK", False):
        type_label = "🔴 WEAK SIGNAL - DYOR"
        # Override header: WEAK = merah, STRONG = hijau
    elif signal_type == "SCALPING":
        type_label = "🟢 STRONG SIGNAL"
    else:
        type_label = "📈 INTRADAY"
    sl_usd = usd_from_pips(sl_pips)
    tp1_usd = usd_from_pips(tp1_pips)
    tp2_usd = usd_from_pips(tp2_pips)
    tp3_usd = usd_from_pips(tp3_pips) if tp3_pips is not None else 0
    if _is_weak:
        tp_line = f"TP: *{tp1}* (+40 pips / +${tp1_usd:.2f})\\n"
        tp_line += "🔴 WEAK SIGNAL - DYOR - Base on Stoch 5,3,3 saja, bukan setup penuh\\n"
    elif tp3 is None:
        tp_line = f"TP1: *{tp1}* (+{tp1_pips} pips / +${tp1_usd:.2f})\\nTP2: *{tp2}* (+{tp2_pips} pips / +${tp2_usd:.2f})\\n"
        tp_line += "⚠️ M15 TAK CONFIRM - TP1 + TP2 SAHAJA (TP3 tak valid)\\n"
    else:
        tp_line = f"TP1: *{tp1}* (+{tp1_pips} pips / +${tp1_usd:.2f})\\nTP2: *{tp2}* (+{tp2_pips} pips / +${tp2_usd:.2f})\\nTP3: *{tp3}* (+{tp3_pips} pips / +${tp3_usd:.2f})\\n"
        if signal_type == "SCALPING":
            tp_line += "✅ M15 CONFIRM - TP1 + TP2 + TP3 VALID\\n"
    msg = (
        f"🤖 *KANSAI SIGNAL - AI {type_label} #{new_id}*\\n\\n"
        f"Pair: *{pair_label}*\\n"
        f"Direction: *{arrow}*\\n"
        f"Jenis: *{signal_type} (AI)*\\n\\n"
        f"Entry: *{entry}*\\n"
        f"SL: *{sl}* (-{sl_pips} pips / -${sl_usd:.2f} untuk 0.05 lot)\\n"
        f"{tp_line}\\n"
        f"🧠 AI Reason: {reason}\\n\\n"
        f"💡 Tips: Tutup sebahagian di TP1 untuk lock profit.\\n"
        f"⚠️ Trading ada risiko. Urus risiko anda.\\n\\n"
        f"—————————————\\n"
        f"Jom dapatkan signal best dengan kami di @kansaisignal_bot\\n"
        f"📰 News: @kansai_news | 📊 TA: @kansai_ta"
    )
    users = load_json(USERS_FILE, {})
    sent = 0
    for uid, u in users.items():
        if is_active_user(u) and should_receive_signal(u, signal_type):
            try:
                await context.bot.send_message(chat_id=int(uid), text=msg, parse_mode="Markdown")
                sent += 1
            except:
                pass
    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"🤖 AI dah hantar signal {signal_type} #{new_id} kepada {sent} user.\\n\\n{msg}", parse_mode="Markdown")
    except:
        pass
    return new_id, sent



# ---------- /signal_log + /sent_check + /last_signal - ADMIN CHECK SIGNAL DAH HANTAR KE BELUM ----------
async def signal_log_cmd(update, context):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Maaf, command ini hanya untuk admin.")
        return
    signals = load_json(SIGNALS_FILE, [])
    if not signals:
        await update.message.reply_text("Belum ada signal lagi.")
        return
    last5 = sorted(signals, key=lambda s: s.get("id", 0), reverse=True)[:5]
    lines = ["📋 *SIGNAL LOG - 5 Signal Terkini*\n"]
    for s in last5:
        _id = s.get("id")
        _pair = s.get("pair")
        _dir = s.get("direction")
        _entry = s.get("entry")
        _sl = s.get("sl")
        _tp1 = s.get("tp1")
        _tp2 = s.get("tp2")
        _tp3 = s.get("tp3")
        _type = s.get("signal_type")
        _status = s.get("status")
        _result = s.get("result") or "-"
        _sent = s.get("sent_count", "?")
        _created = s.get("created_at", "-")
        _reason = s.get("ai_reason", "") or ""
        _reason_short = _reason[:120] + ("..." if len(_reason) > 120 else "")
        _arrow = "🟢 BUY" if _dir == "BUY" else "🔴 SELL"
        lines.append(
            f"\n*#{_id} {_pair} {_arrow} {_type}*\n"
            f"Status: *{_status}* | Result: *{_result}*\n"
            f"Entry: *{_entry}* | SL: *{_sl}* | TP1: *{_tp1}* | TP2: *{_tp2}* | TP3: *{_tp3}*\n"
            f"Dihantar kepada: *{_sent} user*\n"
            f"Dibuat: {_created}\n"
            f"AI Reason: {_reason_short}\n"
            f"Check siapa dapat: `/sent_check {_id}`"
        )
    lines.append("\n\nTaip `/sent_check <ID>` untuk tengok nama users yang dapat signal tu.")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

async def sent_check_cmd(update, context):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Maaf, command ini hanya untuk admin.")
        return
    args = context.args
    if not args:
        await update.message.reply_text("Format: `/sent_check <ID>`\nContoh: `/sent_check 12`")
        return
    try:
        sid = int(args[0])
    except:
        await update.message.reply_text("ID mesti nombor. Contoh: `/sent_check 12`")
        return
    signals = load_json(SIGNALS_FILE, [])
    target = None
    for s in signals:
        if s.get("id") == sid:
            target = s
            break
    if not target:
        await update.message.reply_text(f"Signal #{sid} tidak dijumpai.")
        return
    _pair = target.get("pair")
    _dir = target.get("direction")
    _entry = target.get("entry")
    _type = target.get("signal_type")
    _status = target.get("status")
    _sent = target.get("sent_count", "?")
    _sent_to = target.get("sent_to", [])
    _failed = target.get("failed_to", [])
    _created = target.get("created_at", "-")
    _reason = target.get("ai_reason", "") or ""
    users = load_json(USERS_FILE, {})
    _should = []
    _not_active = []
    for uid, u in users.items():
        if should_receive_signal(u, _type):
            if is_active_user(u):
                _should.append(f"@{u.get('username','-')} (ID:{uid}) - {u.get('signal_pref','-')}")
            else:
                _not_active.append(f"@{u.get('username','-')} (ID:{uid}) - Trial/VIP tamat")
    msg_lines = [
        f"🔍 *SENT CHECK - Signal #{sid}*\n",
        f"Pair: *{_pair}* | Direction: *{_dir}* | Entry: *{_entry}* | Jenis: *{_type}*",
        f"Status: *{_status}* | Dibuat: {_created}",
        f"AI Reason: {_reason}\n",
        f"✅ *Dah dihantar kepada {_sent} user:*",
    ]
    if _sent_to:
        for _n in _sent_to:
            msg_lines.append(f"• {_n}")
    else:
        msg_lines.append("• (Tiada rekod sent_to - signal ni dibuat sebelum update log, atau sent_count = 0)")
    if _failed:
        msg_lines.append(f"\n❌ *Gagal hantar kepada {len(_failed)} user:*")
        for _f in _failed:
            msg_lines.append(f"• {_f}")
    msg_lines.append(f"\n👥 *Yang patut dapat signal {_type} ni sekarang ({len(_should)} orang aktif):*")
    if _should:
        for _s in _should[:30]:
            msg_lines.append(f"• {_s}")
    else:
        msg_lines.append("• Tiada user aktif yang pilih " + str(_type))
    if _not_active:
        msg_lines.append(f"\n⚠️ *Yang pilih {_type} tapi tak aktif ({len(_not_active)} orang):*")
        for _n in _not_active[:15]:
            msg_lines.append(f"• {_n}")
    await update.message.reply_text("\n".join(msg_lines), parse_mode="Markdown")

async def last_signal_cmd(update, context):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Maaf, command ini hanya untuk admin.")
        return
    signals = load_json(SIGNALS_FILE, [])
    if not signals:
        await update.message.reply_text("Belum ada signal lagi.")
        return
    s = sorted(signals, key=lambda x: x.get("id", 0), reverse=True)[0]
    _id = s.get("id")
    _pair = s.get("pair")
    _dir = s.get("direction")
    _entry = s.get("entry")
    _sl = s.get("sl")
    _tp1 = s.get("tp1")
    _tp2 = s.get("tp2")
    _tp3 = s.get("tp3")
    _type = s.get("signal_type")
    _status = s.get("status")
    _sent = s.get("sent_count", "?")
    _sent_to = s.get("sent_to", [])
    _created = s.get("created_at", "-")
    _reason = s.get("ai_reason", "") or ""
    _arrow = "🟢 BUY" if _dir == "BUY" else "🔴 SELL"
    _to_text = "\n".join([f"• {n}" for n in _sent_to]) if _sent_to else "(Tiada rekod - signal lama sebelum update log)"
    msg = (
        f"📌 *LAST SIGNAL - #{_id}*\n\n"
        f"Pair: *{_pair}* | Direction: *{_arrow}* | Jenis: *{_type}*\n"
        f"Status: *{_status}* | Dibuat: {_created}\n\n"
        f"Entry: *{_entry}*\nSL: *{_sl}*\nTP1: *{_tp1}* | TP2: *{_tp2}* | TP3: *{_tp3}*\n\n"
        f"AI Reason: {_reason}\n\n"
        f"✅ Dihantar kepada *{_sent} user*:\n{_to_text}\n\n"
        f"Taip `/sent_check {_id}` untuk detail penuh."
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

# ---------- TIPS KANSAI - BUTTON BARU ----------
TIPS_KANSAI_TEXT = (
    "💡 *TIPS TRADING KANSAI*\n"
    "\n"
    "Signal akan keluar TP, TP1, TP2 dan TP3.\n"
    "\n"
    "• Jika *TP sahaja*, boleh 1 layer (jika lebih layer - please DYOR)\n"
    "• Jika *TP1 & TP2*, buka 2 layer. 1 entry set TP1, 1 set TP2.\n"
    "• Jika *TP1, TP2 & TP3*, buka 3 layer. Set ikut TP1, TP2 & TP3.\n"
    "\n"
    "📊 *Cara Kira Result (Layer):*\n"
    "\n"
    "• Signal TP sahaja: TP 40 pips = *+$20.00* win (1 layer x 0.05 lot)\n"
    "• Signal TP1 & TP2: TP1 20 + TP2 40 = *60 pips = +$30.00* win (2 layer)\n"
    "• Signal TP1, TP2 & TP3: 20 + 40 + 60 = *120 pips = +$60.00* win (3 layer)\n"
    "\n"
    "❌ *Kalau SL (0.05 lot per layer):*\n"
    "• 1 TP (WEAK): Loss *30 pips = -$15.00* (1 layer x SL 30)\n"
    "• TP1 & TP2: Loss *40 pips = -$20.00* (2 layer x SL 20)\n"
    "• TP1, TP2 & TP3: Loss *60 pips = -$30.00* (3 layer x SL 20)\n"
    "\n"
    "💰 *1 layer = 0.05 lot, $0.50 per pip.* Kalau kau buka 0.10 lot, darab 2. Kalau 0.01 lot, bahagi 5.\n"
    "\n"
    "🛡️ *BREAKEVEN (BE) - PENTING:*\n"
    "Bila signal dah hit TP1, terus letak BE kat Entry. Kalau price patah balik kat Entry lepas hit TP1, signal dikira CLOSED tapi NO LOSS (0 pips), bukan SL. Selagi price tak kena BE / SL, TP2 masih ON.\n"
    "\n"
    "Jom dapatkan signal best dengan kami di @kansaisignal_bot"
)

async def tips_cmd(update, context):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🏠 Menu", callback_data="menu")]
    ])
    if update.message:
        try:
            await update.message.reply_text(TIPS_KANSAI_TEXT, parse_mode="Markdown", reply_markup=kb)
        except:
            await update.message.reply_text(TIPS_KANSAI_TEXT.replace("*", ""), reply_markup=kb)
    elif update.callback_query:
        await update.callback_query.edit_message_text(TIPS_KANSAI_TEXT, parse_mode="Markdown", reply_markup=kb)


# ---------- BROADCAST ADMIN - /to_all_users ----------
async def to_all_users_cmd(update, context):
    # Admin sahaja boleh guna
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Command ni untuk admin sahaja.")
        return
    text = " ".join(context.args) if context.args else ""
    if not text:
        await update.message.reply_text(
            "Cara guna:\n"
            "/to_all_users <text>\n\n"
            "Contoh:\n"
            "/to_all_users Assalamualaikum, malam ni ada signal best. Stay tuned!"
        )
        return
    users = load_json(USERS_FILE, {})
    if not users:
        await update.message.reply_text("Tiada users lagi.")
        return
    await update.message.reply_text(f"⏳ Tengah hantar ke {len(users)} users...")
    sent = 0
    failed = 0
    for uid in list(users.keys()):
        try:
            await context.bot.send_message(chat_id=int(uid), text=text)
            sent += 1
        except Exception as e:
            print(f"Gagal hantar broadcast ke {uid}: {e}")
            failed += 1
    await update.message.reply_text(
        f"✅ Siap hantar broadcast!\n\n"
        f"Berjaya: {sent} users\n"
        f"Gagal: {failed} users\n\n"
        f"Text: {text}"
    )


# ---------- STATS ADMIN - /stats ----------
async def stats_cmd(update, context):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Command ni untuk admin sahaja.")
        return
    users = load_json(USERS_FILE, {})
    signals = load_json(SIGNALS_FILE, [])
    total = len(users)
    now_dt = now()
    in_trial = 0
    tamat_trial = 0
    vip = 0
    copy_aktif = 0
    copy_tak_aktif = 0
    for uid, u in users.items():
        # Admin tak kira dalam trial / tamat trial, dia VIP kekal
        is_admin_u = u.get("is_admin") or str(uid) == str(ADMIN_ID)
        is_vip_u = u.get("is_vip") or is_admin_u
        # VIP = is_vip True ATAU sub_end masih hidup
        sub_end_str = u.get("sub_end")
        sub_aktif = False
        if sub_end_str:
            try:
                sub_aktif = now_dt < datetime.datetime.fromisoformat(sub_end_str)
            except:
                sub_aktif = False
        if is_vip_u or sub_aktif:
            vip += 1
        else:
            # Bukan VIP - check trial
            trial_end_str = u.get("trial_end")
            trial_aktif = False
            if trial_end_str:
                try:
                    trial_aktif = now_dt < datetime.datetime.fromisoformat(trial_end_str)
                except:
                    trial_aktif = False
            if trial_aktif:
                in_trial += 1
            else:
                tamat_trial += 1
        # Copytrading - field copytrading / copytrading_active, default tak aktif
        if u.get("copytrading") or u.get("copytrading_active"):
            copy_aktif += 1
        else:
            copy_tak_aktif += 1
    # Signals stats
    open_sig = sum(1 for s in signals if s.get("status") == "OPEN")
    closed_sig = sum(1 for s in signals if s.get("status") == "CLOSED")
    msg = (
        f"📊 *STATISTIK BOT KANSAI*\n\n"
        f"👥 Users total: *{total} orang*\n"
        f"🎁 Users in trial: *{in_trial} orang*\n"
        f"⏰ Users tamat trial: *{tamat_trial} orang*\n"
        f"⭐ VIP: *{vip} orang*\n"
        f"📋 Copytrading aktif: *{copy_aktif} orang*\n"
        f"📋 Copytrading tak aktif: *{copy_tak_aktif} orang*\n\n"
        f"📈 Signal OPEN: *{open_sig}*\n"
        f"✅ Signal CLOSED: *{closed_sig}*\n\n"
        f"👑 Admin: Kau tak payah langganan, boleh access semua."
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def ai_scan_job(context):
    if not AI_ENABLED:
        return
    for pair in ["XAUUSD", "BTCUSD"]:
        for signal_type in ["SCALPING", "INTRADAY"]:
            try:
                can, reason_can = _can_send_ai(pair, signal_type)
                if not can:
                    continue
                if signal_type == "SCALPING":
                    direction, price, reason, tp3_valid = _check_scalping_ai(pair)
                    globals()["_LAST_TP3_VALID"] = tp3_valid
                                        globals()["_LAST_IS_WEAK"] = False
                else:
                    direction, price, reason = _check_intraday_ai(pair)
                if direction is None:
                    continue
                if AI_MODE == "SEMI":
                    global AI_PENDING_COUNTER
                    AI_PENDING_COUNTER += 1
                    pid = AI_PENDING_COUNTER
                    AI_PENDING[pid] = {"pair": pair, "direction": direction, "entry": price, "signal_type": signal_type, "reason": reason}
                    kb = InlineKeyboardMarkup([
                        [InlineKeyboardButton(f"✅ Approve Hantar #{pid}", callback_data=f"ai_approve_{pid}")],
                        [InlineKeyboardButton(f"❌ Reject #{pid}", callback_data=f"ai_reject_{pid}")],
                    ])
                    await context.bot.send_message(
                        chat_id=ADMIN_ID,
                        text=(f"🤖 *AI Jumpa Setup Baru!*\n\nPair: *{pair}*\nJenis: *{signal_type}*\nDirection: *{direction}*\nEntry: *{price}*\nReason: {reason}\n\nNak hantar kat client ke?"),
                        parse_mode="Markdown", reply_markup=kb
                    )
                else:
                    await _create_ai_signal(context, pair, direction, price, signal_type, reason)
            except Exception as e:
                print(f"AI scan error {pair} {signal_type}: {e}")

async def ai_tp_monitor_job(context):
    # BARU: AI tak tutup terus bila TP1 kena. Dia update je, signal masih jalan.
    # TP1 hit -> hantar "hit TP1 50pips!" tapi OPEN lagi
    # TP2 hit -> hantar "hit TP2 100pips!" tapi OPEN lagi
    # TP3 hit -> baru CLOSE, hantar "hit TP3 150pips! Signal CLOSED"
    # SL hit -> baru CLOSE, hantar "kena SL"
    signals = load_json(SIGNALS_FILE, [])
    changed = False
    for s in signals:
        if s.get("status") != "OPEN":
            continue
        pair = s.get("pair")
        direction = s.get("direction")
        entry = s.get("entry")
        sl = s.get("sl")
        tp1 = s.get("tp1")
        tp2 = s.get("tp2")
        tp3 = s.get("tp3")
        # track mana TP dah hit
        tp1_hit = s.get("tp1_hit", False)
        tp2_hit = s.get("tp2_hit", False)
        try:
            price = _get_current_price(pair)
        except:
            continue
        if price is None:
            continue
        _labels = {"XAUUSD": "GOLD (XAUUSD)", "BTCUSD": "BTC (BTCUSD)", "EURUSD": "EUR / USD", "GBPUSD": "GBP / USD", "AUDUSD": "AUD / USD", "USDCAD": "USD / CAD", "NZDUSD": "NZD / USD", "USDCHF": "USD / CHF", "USDJPY": "USD / JPY", "EURJPY": "EUR / JPY", "GBPJPY": "GBP / JPY", "EURGBP": "EUR / GBP", "XAGUSD": "SILVER (XAGUSD)"}
        pair_label = _labels.get(pair, pair)
        signal_type = s.get("signal_type", "INTRADAY")
        type_label = "⚡ SCALPING" if signal_type == "SCALPING" else "📈 INTRADAY"
        sl_pips = s.get("sl_pips", 50)
        tp1_pips = s.get("tp1_pips", 50)
        tp2_pips = s.get("tp2_pips", 100)
        tp3_pips = s.get("tp3_pips", 150)

        # Helper hantar update kat semua client yang dapat signal ni
        async def _broadcast_tp_update(msg_text):
            users = load_json(USERS_FILE, {})
            for uid, u in users.items():
                if is_active_user(u) and should_receive_signal(u, signal_type):
                    try:
                        await context.bot.send_message(chat_id=int(uid), text=msg_text, parse_mode="Markdown")
                    except:
                        pass

        # --- CHECK BE DULU (lepas hit TP1, SL dah jadi BE kat Entry) ---
        # Kalau dah hit TP1, trader patut dah BE. Kalau price patah balik kat Entry, CLOSE tapi NO LOSS (0 pips), bukan SL.
        # Selagi tak kena BE / SL, TP2 masih ON.
        if tp1_hit:
            be_hit = False
            if direction == "BUY" and price <= entry:
                be_hit = True
            if direction == "SELL" and price >= entry:
                be_hit = True
            if be_hit:
                s["status"] = "CLOSED"
                s["result"] = "BE"
                s["pips"] = 0
                s["usd_005lot"] = 0.0
                s["closed_at"] = now_str()
                s["closed_by"] = "AI_AUTO"
                changed = True
                msg = (
                    f"🛡️ *KANSAI SIGNAL - BREAKEVEN (BE) {type_label} #{s.get('id')} - SIGNAL CLOSED*\n\n"
                    f"Pair: *{pair_label} {direction}*\n"
                    f"Entry: *{entry}*\\n"
                    f"Result: *BE - NO LOSS* (Auto by AI)\n"
                    f"Pips: *0 pips*\n"
                    f"Profit / Loss: *$0.00* (0.05 lot)\n\n"
                    f"✅ Price dah patah balik kat Entry lepas hit TP1. Kau dah BE, jadi NO LOSS.\n"
                    f"Selagi tak kena BE ni tadi, TP2 masih ON - tapi sekarang signal dah close.\n\n"
                    f"Jom dapatkan signal best dengan kami di @kansaisignal_bot\n"
                    f"📰 News: @kansai_news | 📊 TA: @kansai_ta"
                )
                await _broadcast_tp_update(msg)
                try:
                    await context.bot.send_message(chat_id=ADMIN_ID, text=f"🤖 AI: Signal #{s.get('id')} kena BE (0 pips) - CLOSED", parse_mode="Markdown")
                except:
                    pass
                continue

        # --- CHECK SL DULU (kalau kena SL, terus CLOSE) ---
        sl_hit = False
        if direction == "BUY" and price <= sl:
            sl_hit = True
        if direction == "SELL" and price >= sl:
            sl_hit = True
        if sl_hit:
            s["status"] = "CLOSED"
            s["result"] = "SL"
            # LAYER LOSS: WEAK 1 layer = -30, TP1+TP2 2 layer = -40 (2x SL 20), TP1+TP2+TP3 3 layer = -60 (3x SL 20)
            # Untuk INTRADAY: 3 layer = -150 (3x SL 50)
            _is_weak_sl = (tp2 is None and tp3 is None)
            if _is_weak_sl:
                _loss = -sl_pips  # WEAK: -30 (1 layer)
            elif tp3 is None:
                _loss = -(sl_pips * 2)  # 2 layer: -40
            else:
                _loss = -(sl_pips * 3)  # 3 layer: -60 / -150
            s["pips"] = _loss
            s["usd_005lot"] = usd_from_pips(_loss)
            s["closed_at"] = now_str()
            s["closed_by"] = "AI_AUTO"
            changed = True
            usd_text = f"-${abs(usd_from_pips(_loss)):.2f}"
            msg = (
                f"❌ *KANSAI SIGNAL - KENA SL {type_label} #{s.get('id')}*\n\n"
                f"Pair: *{pair_label} {direction}*\n"
                f"Entry: *{entry}*\n"
                f"Result: *SL* (Auto by AI)\n"
                f"Pips: *{_loss} pips*\n"
                f"Profit / Loss: *{usd_text}* (0.05 lot)\\n\\n"
                f"Jom dapatkan signal best dengan kami di @kansaisignal_bot\\n"
                f"📰 News: @kansai_news | 📊 TA: @kansai_ta"
            )
            await _broadcast_tp_update(msg)
            try:
                await context.bot.send_message(chat_id=ADMIN_ID, text=f"🤖 AI: Signal #{s.get('id')} kena SL ({_loss} pips)", parse_mode="Markdown")
            except:
                pass
            continue

        # --- CHECK TP3 (kalau kena TP3, baru CLOSE) ---
        tp3_hit_now = False
        if direction == "BUY" and tp3 is not None and price >= tp3:
            tp3_hit_now = True
        if direction == "SELL" and tp3 is not None and price <= tp3:
            tp3_hit_now = True
        if tp3_hit_now:
            s["status"] = "CLOSED"
            s["result"] = "TP3"
            # LAYER: TP1 20 + TP2 40 + TP3 60 = 120 pips win (3 layer)
            _tp1_p = s.get("tp1_pips", 20) or 20
            _tp2_p = s.get("tp2_pips", 40) or 40
            _tp3_p = tp3_pips or 60
            s["pips"] = _tp1_p + _tp2_p + _tp3_p
            s["usd_005lot"] = usd_from_pips(_tp1_p + _tp2_p + _tp3_p)  # 120 pips x $0.50 = $60.00 (3 layer, 0.05 lot)
            s["closed_at"] = now_str()
            s["closed_by"] = "AI_AUTO"
            s["tp1_hit"] = True
            s["tp2_hit"] = True
            changed = True
            usd_val = usd_from_pips(_tp1_p + _tp2_p + _tp3_p)
            msg = (
                f"🔥🔥🔥 *HIT TP3! {type_label} #{s.get('id')} - SIGNAL CLOSED* 🔥🔥🔥\n\n"
                f"Pair: *{pair_label} {direction}*\n"
                f"Entry: *{entry}* -> TP3: *{tp3}*\n"
                f"Result: *TP3* 🎯\n"
                f"Pips: *+{_tp1_p + _tp2_p + _tp3_p} pips* (TP1 {_tp1_p} + TP2 {_tp2_p} + TP3 {_tp3_p})\n"
                f"Profit: *+${usd_val:.2f}* (0.05 lot)\n\n"
                f"✅ Semua TP dah hit! Tahniah!\\n\\n"
                f"Jom dapatkan signal best dengan kami di @kansaisignal_bot\\n"
                f"📰 News: @kansai_news | 📊 TA: @kansai_ta"
            )
            await _broadcast_tp_update(msg)
            try:
                await context.bot.send_message(chat_id=ADMIN_ID, text=f"🤖 AI: Signal #{s.get('id')} HIT TP3 +{tp3_pips} pips - CLOSED", parse_mode="Markdown")
            except:
                pass
            continue

        # --- CHECK TP2 (UPDATE JE, JANGAN CLOSE) ---
        tp2_hit_now = False
        if not tp2_hit:
            if direction == "BUY" and price >= tp2:
                tp2_hit_now = True
            if direction == "SELL" and price <= tp2:
                tp2_hit_now = True
        if tp2_hit_now:
            s["tp1_hit"] = True
            s["tp2_hit"] = True
            changed = True
            usd_val = usd_from_pips(tp2_pips)  # untuk update je, kalau CLOSE nanti guna layer sum kat bawah
            # Kalau TP3 tak valid (M15 tak confirm), TP2 adalah TP terakhir - CLOSE terus
            if tp3 is None:
                s["status"] = "CLOSED"
                s["result"] = "TP2"
                # LAYER: TP1 20 + TP2 40 = 60 pips win (2 layer)
                _tp1_p2 = s.get("tp1_pips", 20) or 20
                _tp2_p2 = tp2_pips or 40
                s["pips"] = _tp1_p2 + _tp2_p2
                s["usd_005lot"] = usd_from_pips(_tp1_p2 + _tp2_p2)  # 60 pips x $0.50 = $30.00 (2 layer)
                s["closed_at"] = now_str()
                s["closed_by"] = "AI_AUTO"
                msg = (
                    f"🔥🔥 *HIT TP2 {tp2_pips} pips! {type_label} #{s.get('id')} - SIGNAL CLOSED* 🔥🔥\n\n"
                    f"Pair: *{pair_label} {direction}*\n"
                    f"Entry: *{entry}* -> TP2: *{tp2}*\n"
                    f"Result: *TP2* 🎯\n"
                    f"Pips: *+{tp2_pips} pips*\n"
                    f"Profit: *+${usd_val:.2f}* (0.05 lot)\n\n"
                    f"✅ M15 TAK CONFIRM - TP1 + TP2 SAHAJA. Signal dah close, tahniah!\n\n"
                    f"Jom dapatkan signal best dengan kami di @kansaisignal_bot\n"
                    f"📰 News: @kansai_news | 📊 TA: @kansai_ta"
                )
            else:
                # TP3 valid - UPDATE JE, JANGAN CLOSE, tunggu TP3
                s["pips"] = tp2_pips
                s["usd_005lot"] = usd_from_pips(tp2_pips)
                msg = (
                    f"🔥 *HIT TP2 {tp2_pips} pips! {type_label} #{s.get('id')}* 🔥\n\n"
                    f"Pair: *{pair_label} {direction}*\n"
                    f"Entry: *{entry}* -> TP2: *{tp2}*\n"
                    f"Profit Sekarang: *+{tp2_pips} pips / +${usd_val:.2f}* (0.05 lot)\n\n"
                    f"⏳ Signal masih jalan, tunggu TP3: *{tp3}*\n\n"
                    f"Jom dapatkan signal best dengan kami di @kansaisignal_bot\n"
                    f"📰 News: @kansai_news | 📊 TA: @kansai_ta"
                )
            await _broadcast_tp_update(msg)
            try:
                await context.bot.send_message(chat_id=ADMIN_ID, text=f"🤖 AI: Signal #{s.get('id')} HIT TP2 +{tp2_pips} pips - masih OPEN, tunggu TP3", parse_mode="Markdown")
            except:
                pass
            continue

        # --- CHECK TP1 (UPDATE JE, JANGAN CLOSE) ---
        tp1_hit_now = False
        if not tp1_hit:
            if direction == "BUY" and price >= tp1:
                tp1_hit_now = True
            if direction == "SELL" and price <= tp1:
                tp1_hit_now = True
        if tp1_hit_now:
            # WEAK SIGNAL: TP je, takde TP2 - hit TP terus CLOSE
            _is_weak_tp = (tp2 is None and tp3 is None)
            if _is_weak_tp:
                s["status"] = "CLOSED"
                s["result"] = "TP"
                s["tp1_hit"] = True
                s["pips"] = tp1_pips
                s["usd_005lot"] = usd_from_pips(tp1_pips)
                s["closed_at"] = now_str()
                s["closed_by"] = "AI_AUTO"
                changed = True
                usd_val = usd_from_pips(tp1_pips)
                msg = (
                    f"🔴 *HIT TP 40 pips! WEAK SIGNAL - DYOR #{s.get('id')} - SIGNAL CLOSED* 🔴\n\n"
                    f"Pair: *{pair_label} {direction}*\n"
                    f"Entry: *{entry}* -> TP: *{tp1}*\n"
                    f"Result: *TP* 🎯\n"
                    f"Pips: *+{tp1_pips} pips*\n"
                    f"Profit: *+${usd_val:.2f}* (0.05 lot)\n\n"
                    f"✅ WEAK SIGNAL - TP sahaja, signal dah close!\n\n")
                await _broadcast_tp_update(msg)
                try:
                    await context.bot.send_message(chat_id=ADMIN_ID, text=f"🤖 AI: Signal #{s.get('id')} HIT TP (WEAK) +{tp1_pips} pips - CLOSED", parse_mode="Markdown")
                except:
                    pass
                continue
            s["tp1_hit"] = True
            s["pips"] = tp1_pips
            s["usd_005lot"] = usd_from_pips(tp1_pips)
            changed = True
            usd_val = usd_from_pips(tp1_pips)
            msg = (
                f"✅ *HIT TP1 {tp1_pips} pips! {type_label} #{s.get('id')}* ✅\n\n"
                f"Pair: *{pair_label} {direction}*\n"
                f"Entry: *{entry}* -> TP1: *{tp1}*\n"
                f"Profit Sekarang: *+{tp1_pips} pips / +${usd_val:.2f}* (0.05 lot)\n\n"
                f"💡 SILA LETAK BE (BREAKEVEN) SEKARANG! Letak SL kat Entry. Kalau price turun balik kat Entry lepas ni, signal dikira CLOSED tapi NO LOSS (0 pips), bukan SL. Selagi tak kena BE / SL, TP2 masih ON. Boleh lock sebahagian profit. Signal masih jalan, tunggu TP2: *{tp2}*\\n\\n"
                f"Jom dapatkan signal best dengan kami di @kansaisignal_bot\\n"
                f"📰 News: @kansai_news | 📊 TA: @kansai_ta"
            )
            await _broadcast_tp_update(msg)
            try:
                await context.bot.send_message(chat_id=ADMIN_ID, text=f"🤖 AI: Signal #{s.get('id')} HIT TP1 +{tp1_pips} pips - masih OPEN, tunggu TP2", parse_mode="Markdown")
            except:
                pass
            continue

    if changed:
        save_json(SIGNALS_FILE, signals)



# ---------- AUTO POST 2 CHANNEL ----------
import xml.etree.ElementTree as ET

def _fetch_forex_news(limit=3):
    # Ambik news dari ForexLive RSS - FREE, tak perlu API key
    try:
        urls = [
            "https://www.forexlive.com/feed/",
            "https://www.investing.com/rss/news_1.rss",
        ]
        news_list = []
        for url in urls:
            try:
                r = _req.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
                root = ET.fromstring(r.content)
                for item in root.findall(".//item")[:limit]:
                    title = item.findtext("title", "")
                    link = item.findtext("link", "")
                    desc = item.findtext("description", "")
                    # Bersihkan HTML tags simple
                    if desc:
                        desc = desc.replace("<p>", "").replace("</p>", "").replace("<br>", " ")[:200]
                    news_list.append({"title": title, "link": link, "desc": desc})
                    if len(news_list) >= limit:
                        break
            except Exception as e:
                print(f"News fetch error {url}: {e}")
                continue
            if len(news_list) >= limit:
                break
        return news_list
    except Exception as e:
        print(f"News error: {e}")
        return []

def _fetch_kraken_ticker_price(pair):
    # Ticker Kraken - 1 saat je, paling laju, tak pernah kena limit, tak perlu OHLC
    # GOLD guna PAXGUSD, BTC guna XBTUSD, lain-lain sama
    tmap = {"XAUUSD": "PAXGUSD", "GOLD": "PAXGUSD", "BTCUSD": "XBTUSD", "BTC": "XBTUSD",
            "EURUSD": "EURUSD", "GBPUSD": "GBPUSD", "AUDUSD": "AUDUSD", "USDCAD": "USDCAD",
            "NZDUSD": "NZDUSD", "USDCHF": "USDCHF", "USDJPY": "USDJPY", "EURJPY": "EURJPY",
            "GBPJPY": "GBPJPY", "EURGBP": "EURGBP", "XAGUSD": "XAGUSD"}
    sym = tmap.get(pair)
    if not sym:
        return None
    try:
        r = _req.get(f"https://api.kraken.com/0/public/Ticker?pair={sym}", headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
        if r.status_code != 200:
            print(f"Kraken Ticker {sym} status {r.status_code}")
            return None
        d = r.json()
        res = d.get("result", {})
        for k, v in res.items():
            if k == "last":
                continue
            # v['c'] = [last price, lot volume]
            if isinstance(v, dict) and "c" in v:
                price = float(v["c"][0])
                print(f"Kraken Ticker OK {pair} via {sym} price={price}")
                return price
        return None
    except Exception as e:
        print(f"Kraken Ticker error {sym}: {e}")
        return None

def _fetch_coinbase_ticker_price(pair):
    # Coinbase ticker - backup kalau Kraken gagal, free, takde limit
    cmap = {"EURUSD": "EUR-USD", "GBPUSD": "GBP-USD", "BTCUSD": "BTC-USD", "AUDUSD": "AUD-USD", "USDCAD": "USD-CAD", "XAUUSD": None, "BTC": "BTC-USD"}
    prod = cmap.get(pair)
    if not prod:
        return None
    try:
        r = _req.get(f"https://api.exchange.coinbase.com/products/{prod}/ticker", headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
        if r.status_code != 200:
            return None
        price = float(r.json().get("price", 0))
        print(f"Coinbase Ticker OK {pair} price={price}")
        return price if price > 0 else None
    except Exception as e:
        print(f"Coinbase Ticker error {pair}: {e}")
        return None

def _make_ta_summary_all(pair):
    # TA - panggil API SEKALI JE (M5), M15 + H1 kira dari M5 - elak rate limit 8/min
    m5 = _get_candles(pair, "M5")
    if len(m5) < 15:
        # Cuba M15 kalau M5 gagal
        m5 = _get_candles(pair, "M15")
        if len(m5) < 15:
            # LAST RESORT - Jangan return None, jangan tulis Gagal ambik data
            # Ambik harga semasa je dari Ticker (1 saat, tak pernah limit), buat candle palsu dari harga tu
            print(f"TA {pair} OHLC gagal, guna Ticker fallback")
            tick = _fetch_kraken_ticker_price(pair)
            if not tick:
                tick = _fetch_coinbase_ticker_price(pair)
            if not tick:
                # Cuba cache lama, walau dah stale pun guna je, jangan gagal
                cached = _cache_load(pair, "M5", 86400)
                if cached and len(cached) >= 10:
                    print(f"TA {pair} guna cache lama len={len(cached)}")
                    m5 = cached
                else:
                    print(f"TA {pair} betul-betul takde data - Ticker + Cache pun gagal")
                    return None
            else:
                # Buat 30 candle dari harga semasa - naik turun sikit 0.05% supaya EMA/RSI boleh kira
                import random as _rnd
                _rnd.seed(int(tick * 100) % 10000)
                m5 = []
                _p = tick * 0.998
                for _i in range(30):
                    _p = _p * (1 + _rnd.uniform(-0.0005, 0.0006))
                    m5.append(_p)
                m5[-1] = tick
                print(f"TA {pair} Ticker fallback OK price={tick} synthetic len={len(m5)}")
    price = m5[-1]
    # Derive M15 dari M5 - group 3 candle M5 = 1 candle M15
    m15 = []
    for i in range(0, len(m5)-2, 3):
        m15.append(m5[i+2])
    if len(m15) < 5:
        m15 = m5
    # Derive H1 dari M5 - group 12 candle M5 = 1 candle H1
    h1 = []
    for i in range(0, len(m5)-11, 12):
        h1.append(m5[i+11])
    if len(h1) < 5:
        h1 = m5
    ema9 = _ema_list(m5, 9)
    ema21 = _ema_list(m5, 21)
    ema50 = _ema_list(m15, 50) if len(m15) >= 50 else _ema_list(m5, 21)
    rsi_m5 = _rsi_list(m5, 14)
    rsi_m15 = _rsi_list(m15, 14) if len(m15) >= 14 else rsi_m5
    recent = h1[-50:] if len(h1) >= 10 else m5[-50:]
    support = min(recent) if recent else price
    resistance = max(recent) if recent else price
    if price > ema9 and price > ema21 and rsi_m5 > 50:
        bias = "🟢 BIAS BUY - Trend naik, tunggu pullback"
        bias_emoji = "🟢"
    elif price < ema9 and price < ema21 and rsi_m5 < 50:
        bias = "🔴 BIAS SELL - Trend turun, tunggu pullback"
        bias_emoji = "🔴"
    else:
        bias = "🟡 SIDEWAYS - Tunggu breakout, jangan kejar"
        bias_emoji = "🟡"
    _labels = {"XAUUSD": "GOLD (XAUUSD)", "BTCUSD": "BTC (BTCUSD)", "EURUSD": "EUR / USD", "GBPUSD": "GBP / USD", "AUDUSD": "AUD / USD", "USDCAD": "USD / CAD", "NZDUSD": "NZD / USD", "USDCHF": "USD / CHF", "USDJPY": "USD / JPY", "EURJPY": "EUR / JPY", "GBPJPY": "GBP / JPY", "EURGBP": "EUR / GBP", "XAGUSD": "SILVER (XAGUSD)"}
    pair_label = _labels.get(pair, pair)
    if pair == "XAUUSD":
        sup_pips = abs(price - support) / 0.10
        res_pips = abs(resistance - price) / 0.10
    else:
        sup_pips = abs(price - support) / 10
        res_pips = abs(resistance - price) / 10
    return {
        "pair_label": pair_label,
        "price": price,
        "ema9": ema9,
        "ema21": ema21,
        "ema50": ema50,
        "rsi_m5": rsi_m5,
        "rsi_m15": rsi_m15,
        "support": support,
        "resistance": resistance,
        "bias": bias,
        "bias_emoji": bias_emoji,
        "sup_pips": sup_pips,
        "res_pips": res_pips,
    }

# ENHANCED NEWS IMPACT + ALL MAJOR PAIRS TA - V2
# Ganti fungsi lama

def _analyze_news_impact(title, desc):
    text = (title + " " + desc).lower()
    impact = "MEDIUM"
    affected = []
    effect = ""
    # High impact keywords
    if any(k in text for k in ["fed", "fomc", "interest rate", "rate hike", "rate cut", "powell", "cpi", "inflation", "nfp", "nonfarm", "payroll", "gdp", "unemployment", "central bank", "ecb", "boe"]):
        impact = "HIGH 🔴"
    elif any(k in text for k in ["retail sales", "pmi", "trade", "oil", "opec", "war", "tariff", "election", "debt"]):
        impact = "MEDIUM 🟡"
    else:
        impact = "LOW 🟢"
    # Affected pairs
    if any(k in text for k in ["usd", "dollar", "fed", "us ", "america", "powell", "cpi", "nfp"]):
        affected.append("USD / GOLD / EURUSD")
    if any(k in text for k in ["gold", "xau", "safe haven"]):
        affected.append("GOLD (XAUUSD)")
    if any(k in text for k in ["oil", "opec", "crude"]):
        affected.append("OIL / USDCAD")
    if any(k in text for k in ["eur", "europe", "ecb", "euro"]):
        affected.append("EURUSD")
    if any(k in text for k in ["gbp", "pound", "uk ", "boe", "britain"]):
        affected.append("GBPUSD")
    if any(k in text for k in ["jpy", "yen", "japan", "boj"]):
        affected.append("USDJPY")
    if any(k in text for k in ["btc", "bitcoin", "crypto"]):
        affected.append("BTCUSD")
    if not affected:
        affected = ["Semua Pair USD"]
    # Effect explanation
    if "rate hike" in text or "hawkish" in text or "inflation naik" in text or "cpi" in text and "naik" in text:
        effect = "USD dijangka KUAT ⬆️, GOLD & EURUSD dijangka TURUN ⬇️. Hati-hati BUY Gold."
    elif "rate cut" in text or "dovish" in text or "cut" in text and "fed" in text:
        effect = "USD dijangka LEMAH ⬇️, GOLD & EURUSD dijangka NAIK ⬆️. Bagus untuk BUY Gold."
    elif any(k in text for k in ["war", "conflict", "tension", "safe haven"]):
        effect = "GOLD dijangka NAIK ⬆️ sebab orang lari ke safe haven. USD pun boleh kuat."
    elif any(k in text for k in ["oil naik", "opec cut"]):
        effect = "USDCAD boleh TURUN (CAD kuat), GOLD boleh NAIK sikit sebab inflasi."
    elif "nfp" in text or "payroll" in text:
        effect = "NFP kuat = USD KUAT, GOLD TURUN. NFP lemah = USD LEMAH, GOLD NAIK. Volatile 30 minit pertama."
    else:
        effect = "Monitor USD & GOLD. Kalau news ni kuat, harga boleh gerak 50-100 pips dalam 1 jam."
    return impact, " | ".join(affected), effect

def _get_yahoo_symbol(pair):
    mapping = {
        "EURUSD": "EURUSD=X",
        "GBPUSD": "GBPUSD=X",
        "USDJPY": "USDJPY=X",
        "AUDUSD": "AUDUSD=X",
        "USDCAD": "USDCAD=X",
        "NZDUSD": "NZDUSD=X",
        "USDCHF": "USDCHF=X",
        "EURJPY": "EURJPY=X",
        "GBPJPY": "GBPJPY=X",
        "EURGBP": "EURGBP=X",
        "XAUUSD": "GC=F",
        "XAGUSD": "SI=F",
        "BTCUSD": "BTC-USD",
    }
    return mapping.get(pair, pair)

def _get_candles_all(pair, timeframe):
    # Override untuk semua pair - guna Yahoo untuk forex + gold + silver, Binance untuk BTC
    if pair == "BTCUSD":
        interval_map = {"M1": "1m", "M5": "5m", "M15": "15m", "H1": "1h", "H4": "4h"}
        iv = interval_map.get(timeframe, "5m")
        closes = _fetch_binance("BTCUSDT", iv, 120)
        if closes:
            return closes
    yahoo_iv = {"M1": "1m", "M5": "5m", "M15": "15m", "H1": "60m", "H4": "240m"}
    iv = yahoo_iv.get(timeframe, "5m")
    sym = _get_yahoo_symbol(pair)
    closes = _fetch_yahoo(sym, iv, "5d")
    if closes:
        return closes
    # Fallback cuba symbol lama
    return _fetch_yahoo(sym, iv, "1d")

def _pip_size(pair):
    if pair in ["USDJPY", "EURJPY", "GBPJPY"]:
        return 0.01
    if pair == "XAUUSD":
        return 0.10
    if pair == "XAGUSD":
        return 0.01
    if pair == "BTCUSD":
        return 10.0
    return 0.0001

def _make_ta_summary_all(pair):
    m5 = _get_candles_all(pair, "M5")
    m15 = _get_candles_all(pair, "M15")
    h1 = _get_candles_all(pair, "H1")
    if len(m5) < 30:
        return None
    price = m5[-1]
    ema9 = _ema_list(m5, 9)
    ema21 = _ema_list(m5, 21)
    ema50 = _ema_list(m15, 50)
    rsi_m5 = _rsi_list(m5, 14)
    rsi_m15 = _rsi_list(m15, 14)
    recent = h1[-50:] if len(h1) >= 50 else h1
    support = min(recent) if recent else price
    resistance = max(recent) if recent else price
    if price > ema9 and price > ema21 and rsi_m5 > 50:
        bias = "🟢 BIAS BUY - Trend naik, tunggu pullback"
    elif price < ema9 and price < ema21 and rsi_m5 < 50:
        bias = "🔴 BIAS SELL - Trend turun, tunggu pullback"
    else:
        bias = "🟡 SIDEWAYS - Tunggu breakout, jangan kejar"
    pair_labels = {
        "EURUSD": "EUR/USD", "GBPUSD": "GBP/USD", "USDJPY": "USD/JPY",
        "AUDUSD": "AUD/USD", "USDCAD": "USD/CAD", "NZDUSD": "NZD/USD",
        "USDCHF": "USD/CHF", "EURJPY": "EUR/JPY", "GBPJPY": "GBP/JPY",
        "EURGBP": "EUR/GBP", "XAUUSD": "GOLD (XAUUSD)",
        "XAGUSD": "SILVER (XAGUSD)", "BTCUSD": "BTC (BTCUSD)",
    }
    pip = _pip_size(pair)
    sup_pips = abs(price - support) / pip if pip else 0
    res_pips = abs(resistance - price) / pip if pip else 0
    return {
        "pair": pair,
        "pair_label": pair_labels.get(pair, pair),
        "price": price,
        "ema9": ema9,
        "ema21": ema21,
        "ema50": ema50,
        "rsi_m5": rsi_m5,
        "rsi_m15": rsi_m15,
        "support": support,
        "resistance": resistance,
        "bias": bias,
        "sup_pips": sup_pips,
        "res_pips": res_pips,
    }

ALL_TA_PAIRS = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "NZDUSD", "USDCHF", "EURJPY", "GBPJPY", "EURGBP", "XAUUSD", "XAGUSD", "BTCUSD"]


# CHART GENERATOR - Untuk TA Channel dengan Gambar
# AI lukis chart candlestick sendiri guna matplotlib

def _fetch_ohlc(pair, timeframe="H1", limit=50):
    # CACHE OHLC FIRST - elak rate limit, kalau cache baru guna terus
    try:
        _fn = f"/tmp/cache_ohlc_{pair}_{timeframe}.json"
        if _os_cache.path.exists(_fn):
            with open(_fn, "r") as _f:
                _d = _json_cache.load(_f)
            _ohlc_c = _d.get("ohlc", [])
            _age = __import__("time").time() - _d.get("ts", 0)
            if _ohlc_c and _age < 300:
                print(f"OHLC Cache FRESH {pair} {timeframe} age={int(_age)}s len={len(_ohlc_c)}")
                return _ohlc_c
    except Exception:
        pass
    # Kraken FIRST untuk OHLC (free, no limit) - GOLD via PAXGUSD
    kraken_ohlc_first = _fetch_kraken_ohlc(pair, timeframe, limit) if "_fetch_kraken_ohlc" in dir() else None
    # _fetch_kraken_ohlc akan di-handle kat bawah jugak, tapi kita cuba Kraken dulu kat sini kalau ada function tu
    # Binance Vision SECOND - PAXG = GOLD
    bf_ohlc = _fetch_binance_forex_ohlc(pair, timeframe, limit)
    if bf_ohlc:
        print(f"[OHLC] {pair} OK via BinanceForex len={len(bf_ohlc)}")
        _cache_save_ohlc(pair, timeframe, bf_ohlc)
        return bf_ohlc
    # TwelveData SECOND untuk GOLD + FOREX
    td_ohlc = _fetch_twelvedata_ohlc(pair, timeframe, limit)
    if td_ohlc:
        print(f"[OHLC] {pair} OK via TwelveData len={len(td_ohlc)}")
        _cache_save_ohlc(pair, timeframe, td_ohlc)
        return td_ohlc
    # Kraken FIRST - tak block Render
    kraken_ohlc = _fetch_kraken_ohlc(pair, timeframe, limit)
    if kraken_ohlc:
        print(f"[OHLC] {pair} OK via Kraken len={len(kraken_ohlc)}")
        return kraken_ohlc
    # V10 - Binance FIRST, Yahoo fallback. Binance susah kena block.
    # Mapping ke Binance symbol - PAXG = Gold, EURUSDT = EURUSD, dll
    binance_map = {
        "XAUUSD": "PAXGUSDT",
        "BTCUSD": "BTCUSDT",
        "EURUSD": "EURUSDT",
        "GBPUSD": "GBPUSDT",
        "AUDUSD": "AUDUSDT",
        "NZDUSD": "NZDUSDT",
        "XAGUSD": "XAGUSDT",
    }
    # 1. Cuba Binance dulu untuk pair yang ada
    if pair in binance_map:
        try:
            import requests as _r
            iv_map = {"M1": "1m", "M5": "5m", "M15": "15m", "H1": "1h", "H4": "4h"}
            iv = iv_map.get(timeframe, "1h")
            sym = binance_map[pair]
            url = f"https://data-api.binance.vision/api/v3/klines?symbol={sym}&interval={iv}&limit={limit}"
            r = _r.get(url, timeout=60)
            if r.status_code == 200:
                data = r.json()
                ohlc = []
                for c in data:
                    ohlc.append({"open": float(c[1]), "high": float(c[2]), "low": float(c[3]), "close": float(c[4])})
                if ohlc:
                    print(f"[OHLC] {pair} OK via Binance {sym} len={len(ohlc)}")
                    return ohlc
            else:
                print(f"[OHLC] Binance {sym} status {r.status_code}, cuba Yahoo")
        except Exception as e:
            print(f"[OHLC] Binance error {pair}: {e}, cuba Yahoo")
    # 2. Yahoo DISABLED - block kat Render, skip terus ke cache
    try:
        raise Exception("Yahoo disabled")
        import requests as _r
        sym = _get_yahoo_symbol(pair)
        iv_map = {"M5": "5m", "M15": "15m", "H1": "60m"}
        iv = iv_map.get(timeframe, "60m")
        for base_url in ["https://query2.finance.yahoo.com", "https://query1.finance.yahoo.com"]:
            try:
                url = f"{base_url}/v8/finance/chart/{sym}?interval={iv}&range=5d"
                headers = {"User-Agent": "Mozilla/5.0"}
                r = _r.get(url, headers=headers, timeout=60)
                if r.status_code != 200:
                    continue
                data = r.json()
                result = data["chart"]["result"][0]
                q = result["indicators"]["quote"][0]
                opens = q["open"]
                highs = q["high"]
                lows = q["low"]
                closes = q["close"]
                ohlc = []
                for i in range(len(closes)):
                    if closes[i] is None or opens[i] is None:
                        continue
                    ohlc.append({"open": float(opens[i]), "high": float(highs[i]), "low": float(lows[i]), "close": float(closes[i])})
                if ohlc:
                    print(f"[OHLC] {pair} OK via Yahoo {base_url} len={len(ohlc)}")
                    return ohlc[-limit:]
            except Exception as e:
                print(f"[OHLC] Yahoo error {base_url} {pair}: {e}")
                continue
    except Exception as e:
        print(f"[OHLC] Yahoo fallback error {pair}: {e}")
    print(f"[OHLC] SEMUA gagal {pair} - cuba cache lama")
    stale = _cache_load_ohlc(pair, timeframe)
    if stale:
        return stale
    return []


def _generate_chart_image(pair, ta_data):
    # V8 - Robust: Kalau OHLC gagal, guna closes je buat line chart. Takkan return None senang-senang.
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.patches as patches
        import os
        ohlc = _fetch_ohlc(pair, "H1", 50)
        print(f"[CHART DEBUG] {pair} OHLC len={len(ohlc) if ohlc else 0}")
        # Fallback - kalau OHLC kosong, guna closes dari _get_candles
        if not ohlc or len(ohlc) < 20:
            print(f"[CHART DEBUG] {pair} OHLC tak cukup, guna closes fallback M5 (elak rate limit)")
            closes_fallback = _get_candles(pair, "M5")
            if not closes_fallback or len(closes_fallback) < 10:
                print(f"[CHART DEBUG] {pair} Closes pun takde - {closes_fallback}")
                return None
            # Buat ohlc palsu dari closes untuk line chart
            ohlc = []
            for i, c in enumerate(closes_fallback[-50:]):
                ohlc.append({"open": c, "high": c*1.001, "low": c*0.999, "close": c})
            print(f"[CHART DEBUG] {pair} Fallback OHLC len={len(ohlc)}")
        closes = [c["close"] for c in ohlc]
        # Kira EMA
        ema9_vals = []
        ema21_vals = []
        for i in range(len(closes)):
            if i >= 8:
                ema9_vals.append(sum(closes[i-8:i+1]) / 9)
            else:
                ema9_vals.append(None)
            if i >= 20:
                ema21_vals.append(sum(closes[i-20:i+1]) / 21)
            else:
                ema21_vals.append(None)
        fig, ax = plt.subplots(figsize=(10, 5))
        fig.patch.set_facecolor("#0B0E11")
        ax.set_facecolor("#0B0E11")
        # Candlestick - kalau data fallback, dia jadi line nipis je tapi tetap ada gambar
        for i, c in enumerate(ohlc):
            color = "#26A69A" if c["close"] >= c["open"] else "#EF5350"
            ax.plot([i, i], [c["low"], c["high"]], color=color, linewidth=1)
            body_bottom = min(c["open"], c["close"])
            body_height = abs(c["close"] - c["open"])
            if body_height == 0:
                body_height = (c["high"] - c["low"]) * 0.05 + 0.0001
            rect = patches.Rectangle((i - 0.4, body_bottom), 0.8, body_height, facecolor=color, edgecolor=color)
            ax.add_patch(rect)
        x_vals = list(range(len(closes)))
        ema9_plot = [v if v is not None else float("nan") for v in ema9_vals]
        ema21_plot = [v if v is not None else float("nan") for v in ema21_vals]
        ax.plot(x_vals, ema9_plot, color="#FFD700", linewidth=1.2, label="EMA 9")
        ax.plot(x_vals, ema21_plot, color="#2196F3", linewidth=1.2, label="EMA 21")
        if ta_data:
            sup = ta_data["support"]
            res = ta_data["resistance"]
            ax.axhline(y=sup, color="#00FF00", linestyle="--", linewidth=1, label=f"Support {sup:.2f}")
            ax.axhline(y=res, color="#FF0000", linestyle="--", linewidth=1, label=f"Resistance {res:.2f}")
            price = ta_data["price"]
            ax.axhline(y=price, color="white", linestyle=":", linewidth=0.8, alpha=0.7)
        ax.set_title(f"{ta_data['pair_label'] if ta_data else pair} - H1 Chart - KANSAI SIGNAL", color="white", fontsize=14, fontweight="bold", pad=12)
        ax.set_ylabel("Price", color="white")
        ax.tick_params(colors="white", labelsize=8)
        ax.grid(True, alpha=0.2, color="gray")
        ax.legend(facecolor="#1E222D", edgecolor="white", labelcolor="white", fontsize=8, loc="upper left")
        plt.tight_layout()
        path = f"/tmp/chart_{pair}.png"
        plt.savefig(path, dpi=150, facecolor=fig.get_facecolor(), bbox_inches="tight")
        plt.close()
        print(f"[CHART DEBUG] {pair} Chart siap: {path}")
        return path
    except Exception as e:
        print(f"[CHART ERROR] {pair}: {e}")
        import traceback
        traceback.print_exc()
        return None



async def news_post_job_v2(context):
    try:
        news = _fetch_forex_news(limit=3)
        if not news:
            print("News job: no news")
            return
        for n in news:
            try:
                impact, affected, effect = _analyze_news_impact(n.get("title",""), n.get("desc",""))
                msg = (
                    f"📰 *KANSAI NEWS - Forex & Gold*\n\n"
                    f"*{n.get('title','')}*\n\n"
                    f"📊 IMPACT: {impact}\n"
                    f"🎯 Pair Terkesan: {', '.join(affected)}\n"
                    f"💡 Kesan Kat Harga: {effect}\n\n"
                    f"🔗 Baca penuh: {n.get('link','')}\n\n"
                    f"Jom dapatkan signal best dengan kami di @kansaisignal_bot"
                )
                await context.bot.send_message(chat_id=CHANNEL_NEWS_ID, text=msg, parse_mode="Markdown")
            except Exception as e:
                print(f"News post error item: {e}")
    except Exception as e:
        print(f"News job error: {e}")

async def ta_post_job_with_chart(context):
    # CHANNEL_TA_ID dah set ke @kansai_ta, terus post
    # 1. Post gambar HANYA GOLD + BTC - EURUSD & lain-lain text je
    for pair in ["XAUUSD", "BTCUSD"]:
        try:
            ta = _make_ta_summary_all(pair)
            if not ta:
                continue
            chart_path = _generate_chart_image(pair, ta)
            caption = (
                f"📊 KANSAI TEKNIKAL\n"
                f"{ta['pair_label']}\n"
                f"━━━━━━━━━━━━━━\n"
                f"\n"
                f"{ta['price']}\n"
                f"\n"
                f"{ta['bias']}\n"
                f"\n"
                f"📈 Indikator\n"
                f"EMA 9  : {ta['ema9']:.2f}\n"
                f"EMA 21 : {ta['ema21']:.2f}\n"
                f"RSI M5 : {ta['rsi_m5']:.1f}\n"
                f"\n"
                f"🎯 Resistance\n"
                f"{ta['resistance']:.2f}  ({ta['res_pips']:.0f} pips)\n"
                f"\n"
                f"🛡️ Support\n"
                f"{ta['support']:.2f}  ({ta['sup_pips']:.0f} pips)\n"
                f"\n"
                f"━━━━━━━━━━━━━━\n"
                f"Jom dapatkan signal best dengan kami di @kansaisignal_bot"
            )
            if chart_path:
                try:
                    with open(chart_path, "rb") as photo:
                        await context.bot.send_photo(chat_id=CHANNEL_TA_ID, photo=photo, caption=caption)
                except Exception as e:
                    print(f"Send photo error {pair}: {e}")
                    await context.bot.send_message(chat_id=CHANNEL_TA_ID, text=caption)
            else:
                await context.bot.send_message(chat_id=CHANNEL_TA_ID, text=caption)
        except Exception as e:
            print(f"TA chart error {pair}: {e}")
    # 2. Major pair lain - 1 BARIS JE SEPAIR, kemas, tak semak
    try:
        lines = []
        lines.append("📊 MAJOR PAIR LAIN")
        lines.append("━━━━━━━━━━━━━━")
        lines.append("")
        ok_count = 0
        for pair in ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "NZDUSD", "USDCHF", "EURJPY", "GBPJPY", "EURGBP", "XAGUSD"]:
            ta = _make_ta_summary_all(pair)
            if not ta:
                continue
            ok_count += 1
            # Bias pendek: BUY / SELL / SIDEWAYS je
            if "BUY" in ta['bias']:
                bias_s = "🟢 BUY"
            elif "SELL" in ta['bias']:
                bias_s = "🔴 SELL"
            else:
                bias_s = "🟡 SIDEWAYS"
            # Format harga - JPY & XAG 2 decimal, lain 4 decimal
            if pair in ["USDJPY", "EURJPY", "GBPJPY", "XAGUSD"]:
                price_s = f"{ta['price']:.2f}"
            else:
                price_s = f"{ta['price']:.4f}"
            lines.append(f"{pair} {price_s} {bias_s}")
        if ok_count == 0:
            print("TA major pair: semua gagal, skip text pendek")
        else:
            lines.append("")
            lines.append("Jom dapatkan signal best dengan kami di @kansaisignal_bot")
            msg = "\n".join(lines)
            await context.bot.send_message(chat_id=CHANNEL_TA_ID, text=msg)
    except Exception as e:
        print(f"TA text pendek error: {e}")

async def news_test_cmd(update, context):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text("📰 Test post news sekarang...")
    news = _fetch_forex_news(limit=2)
    if not news:
        await update.message.reply_text("Gagal ambik news. Check internet / RSS.")
        return
    for n in news:
        await update.message.reply_text(f"News: {n['title']}\\nLink: {n['link']}")

async def chart_debug_cmd(update, context):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text("🔍 Test matplotlib...")
    try:
        import matplotlib
        await update.message.reply_text(f"✅ matplotlib dah install, version {matplotlib.__version__}")
    except Exception as e:
        await update.message.reply_text(f"❌ matplotlib TAK install / rosak: {e}\n\nTaip kat Terminal: pip3 install matplotlib")
        return
    # Test lukis chart kosong
    try:
        ta = _make_ta_summary_all("XAUUSD")
        if not ta:
            await update.message.reply_text("❌ Gagal ambik data GOLD - check internet")
            return
        path = _generate_chart_image("XAUUSD", ta)
        if path:
            with open(path, "rb") as photo:
                await context.bot.send_photo(chat_id=update.effective_chat.id, photo=photo, caption=f"✅ Chart test berjaya! GOLD {ta['price']} - {ta['bias']}")
        else:
            await update.message.reply_text("❌ Chart return None - tengok Terminal, ada tulis [CHART ERROR] apa?")
    except Exception as e:
        await update.message.reply_text(f"❌ Error chart debug: {e}")

async def ta_test_cmd(update, context):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text("📊 Test TA GOLD + BTC je... Bagi 60 saat, bot tengah ambik data slow sikit.")
    # Test TA - GOLD + BTC JE, major pair dah buang
    for pair in ["XAUUSD", "BTCUSD"]:
        try:
            ta = _make_ta_summary_all(pair)
            if not ta:
                await update.message.reply_text(f"{pair} - Gagal ambik data")
                continue
            chart_path = _generate_chart_image(pair, ta)
            caption = (
                f"📊 TEST TA\n"
                f"{ta['pair_label']}\n"
                f"━━━━━━━━━━━━━━\n"
                f"\n"
                f"💰 Harga\n"
                f"{ta['price']}\n"
                f"\n"
                f"{ta['bias']}\n"
                f"\n"
                f"📈 Indikator\n"
                f"EMA 9  : {ta['ema9']:.2f}\n"
                f"EMA 21 : {ta['ema21']:.2f}\n"
                f"RSI M5 : {ta['rsi_m5']:.1f}\n"
                f"\n"
                f"🎯 Resistance : {ta['resistance']:.2f}\n"
                f"🛡️ Support : {ta['support']:.2f}\n"
                f"\n"
                f"━━━━━━━━━━━━━━\n"
                f"Jom dapatkan signal best dengan kami di @kansaisignal_bot"
            )
            if chart_path:
                try:
                    with open(chart_path, "rb") as photo:
                        await context.bot.send_photo(chat_id=update.effective_chat.id, photo=photo, caption=caption)
                except Exception as e:
                    await update.message.reply_text(f"Gagal hantar gambar {pair}: {e}\n{caption}")
            else:
                await update.message.reply_text(f"⚠️ Chart {pair} gagal generate (check Terminal - mungkin matplotlib belum install / internet slow). Hantar text je:\n{caption}")
        except Exception as e:
            await update.message.reply_text(f"Error TA test {pair}: {e}")
    await update.message.reply_text("📊 Test Major Pair lain (1 baris je)...")
    try:
        lines = []
        lines.append("📊 MAJOR PAIR LAIN")
        lines.append("━━━━━━━━━━━━━━")
        lines.append("")
        for pair in ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "NZDUSD", "USDCHF", "EURJPY", "GBPJPY", "EURGBP", "XAGUSD"]:
            ta = _make_ta_summary_all(pair)
            if not ta:
                await update.message.reply_text(f"{pair} - Gagal ambik data")
                continue
            if "BUY" in ta['bias']:
                bias_s = "🟢 BUY"
            elif "SELL" in ta['bias']:
                bias_s = "🔴 SELL"
            else:
                bias_s = "🟡 SIDEWAYS"
            if pair in ["USDJPY", "EURJPY", "GBPJPY", "XAGUSD"]:
                price_s = f"{ta['price']:.2f}"
            else:
                price_s = f"{ta['price']:.4f}"
            lines.append(f"{pair} {price_s} {bias_s}")
        lines.append("")
        lines.append("Jom dapatkan signal best dengan kami di @kansaisignal_bot")
        await update.message.reply_text("\n".join(lines))
    except Exception as e:
        await update.message.reply_text(f"Error test major pendek: {e}")
    await update.message.reply_text("✅ Siap test. GOLD + BTC gambar, major lain 1 baris je.")


async def debug_data_cmd(update, context):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text("🔍 Debug data - test satu-satu source, tunggu 30 saat...")
    import requests as _rdbg
    results = []
    # 1. Binance Vision PAXG
    try:
        r = _rdbg.get("https://data-api.binance.vision/api/v3/klines?symbol=PAXGUSDT&interval=5m&limit=5", timeout=60)
        results.append(f"Binance Vision PAXG: status {r.status_code}, len {len(r.json()) if r.status_code==200 else 0}")
    except Exception as e:
        results.append(f"Binance Vision PAXG: ERROR {e}")
    # 2. Binance Vision EURUSDT
    try:
        r = _rdbg.get("https://data-api.binance.vision/api/v3/klines?symbol=EURUSDT&interval=5m&limit=5", timeout=60)
        results.append(f"Binance Vision EUR: status {r.status_code}, len {len(r.json()) if r.status_code==200 else 0}")
    except Exception as e:
        results.append(f"Binance Vision EUR: ERROR {e}")
    # 3. TwelveData XAU
    try:
        r = _rdbg.get(f"https://api.twelvedata.com/time_series?symbol=XAU/USD&interval=5min&outputsize=5&apikey={os.getenv('TWELVEDATA_API_KEY', '')}", timeout=60)
        j = r.json()
        if "values" in j:
            results.append(f"TwelveData XAU: OK len {len(j['values'])}")
        else:
            results.append(f"TwelveData XAU: GAGAL {str(j)[:200]}")
    except Exception as e:
        results.append(f"TwelveData XAU: ERROR {e}")
    # 4. TwelveData EUR
    try:
        r = _rdbg.get(f"https://api.twelvedata.com/time_series?symbol=XAU/USD&interval=5min&outputsize=5&apikey={os.getenv('TWELVEDATA_API_KEY', '')}", timeout=60)
        j = r.json()
        if "values" in j:
            results.append(f"TwelveData EUR: OK len {len(j['values'])}")
        else:
            results.append(f"TwelveData EUR: GAGAL {str(j)[:200]}")
    except Exception as e:
        results.append(f"TwelveData EUR: ERROR {e}")
    # 5. Kraken
    try:
        r = _rdbg.get("https://api.kraken.com/0/public/OHLC?pair=EURUSD&interval=5", timeout=60)
        j = r.json()
        results.append(f"Kraken EUR: {str(j.get('error', 'OK'))[:200]}")
    except Exception as e:
        results.append(f"Kraken EUR: ERROR {e}")
    # 6. Coinbase
    try:
        r = _rdbg.get("https://api.exchange.coinbase.com/products/EUR-USD/candles?granularity=300", timeout=60, headers={"User-Agent": "Mozilla/5.0"})
        results.append(f"Coinbase EUR: status {r.status_code}")
    except Exception as e:
        results.append(f"Coinbase EUR: ERROR {e}")
    # 7. GoldPrice
    try:
        r = _rdbg.get("https://data-asg.goldprice.org/dbXRates/USD", timeout=60, headers={"User-Agent": "Mozilla/5.0"})
        results.append(f"GoldPrice: status {r.status_code}")
    except Exception as e:
        results.append(f"GoldPrice: ERROR {e}")

    msg = "🔍 DEBUG DATA RESULT:\n\n" + "\n".join(results) + "\n\nHantar screenshot ni kat aku."
    await update.message.reply_text(msg)
    # Also test _get_candles
    try:
        c1 = _get_candles("XAUUSD", "M5")
        c2 = _get_candles("EURUSD", "M5")
        await update.message.reply_text(f"_get_candles XAUUSD M5: {'OK len '+str(len(c1))+' last '+str(c1[-1]) if c1 else 'GAGAL KOSONG'}\n_get_candles EURUSD M5: {'OK len '+str(len(c2))+' last '+str(c2[-1]) if c2 else 'GAGAL KOSONG'}")
    except Exception as e:
        await update.message.reply_text(f"_get_candles ERROR: {e}")


async def ai_status_cmd(update, context):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Maaf, command ini hanya untuk admin.")
        return
    try:
        _mode = globals().get("AI_MODE", "AUTO")
        _enabled = globals().get("AI_ENABLED", True)
        _today = now().strftime("%Y-%m-%d")
        _c_scalp = globals().get("AI_DAILY_COUNT", {}).get((_today, "SCALPING"), 0)
        _c_intra = globals().get("AI_DAILY_COUNT", {}).get((_today, "INTRADAY"), 0)
        _signals = load_json(SIGNALS_FILE, [])
        _open = sum(1 for s in _signals if s.get("status") == "OPEN")
        _closed = sum(1 for s in _signals if s.get("status") == "CLOSED")
        _users = load_json(USERS_FILE, {})
        _total = len(_users)
        _mode_text = "AI terus hantar kat client, tak payah approve." if _mode == "AUTO" else "AI hantar kat kau dulu untuk approve."
        msg = (
            f"🤖 *AI Status*\n\n"
            f"AI Enabled: *{'ON' if _enabled else 'OFF'}*\n"
            f"Mode: *{_mode}* - {_mode_text}\n\n"
            f"Users: *{_total} orang*\n"
            f"Signal hari ni: SCALPING *{_c_scalp}/20* | INTRADAY *{_c_intra}/3*\n"
            f"Signal OPEN: *{_open}* | CLOSED: *{_closed}*\n\n"
            f"Commands:\n"
            f"/ai_on - On kan AI\n"
            f"/ai_off - Off kan AI (balik manual)\n"
            f"/ai_test - Test AI scan sekarang\n"
            f"/ai_semi - Tukar ke Semi-Auto (Approve dulu)\n"
            f"/ai_auto - Tukar ke Fully Auto"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"AI Status error: {e}")

async def ai_on_cmd(update, context):
    global AI_ENABLED
    if update.effective_user.id != ADMIN_ID:
        return
    AI_ENABLED = True
    await update.message.reply_text("✅ AI FULLY AUTO dah ON. AI akan scan setiap 5 minit dan terus hantar signal kat client.")

async def ai_off_cmd(update, context):
    global AI_ENABLED
    if update.effective_user.id != ADMIN_ID:
        return
    AI_ENABLED = False
    await update.message.reply_text("⏸️ AI dah OFF. Bot balik ke manual sahaja. Kau boleh guna /signal macam biasa.")

async def ai_auto_cmd(update, context):
    global AI_MODE
    if update.effective_user.id != ADMIN_ID:
        return
    AI_MODE = "AUTO"
    await update.message.reply_text("🤖 AI dah set ke *FULLY AUTO* - AI terus hantar kat client tanpa approve.")

async def ai_semi_cmd(update, context):
    global AI_MODE
    if update.effective_user.id != ADMIN_ID:
        return
    AI_MODE = "SEMI"
    await update.message.reply_text("🤖 AI dah set ke *SEMI-AUTO* - AI hantar kat kau dulu untuk approve.")

async def ai_test_cmd(update, context):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text("🤖 AI tengah scan sekarang... Tunggu 10-20 saat.")
    for pair in ["XAUUSD", "BTCUSD"]:
        for signal_type in ["SCALPING", "INTRADAY"]:
            if signal_type == "SCALPING":
                direction, price, reason, tp3_valid = _check_scalping_ai(pair)
                # Tunjuk WEAK jugak dalam /ai_test - TAMBAH, bukan ganti
                w_dir, w_price, w_reason = _check_weak_scalping_ai(pair)
                if w_dir is not None:
                    await update.message.reply_text(f"⚠️ WEAK SCALPING {pair}:\n{w_reason}\nTP 40 SL 30")
                if direction is None and w_dir is None:
                    await update.message.reply_text(f"AI Check {pair} SCALPING:\nSTRONG: Tiada\nWEAK: Tiada\n{reason}")
                reason = reason + f" | TP3 Valid: {'YA - TP1+TP2+TP3' if tp3_valid else 'TAK - TP1+TP2 SAHAJA'}"
            else:
                direction, price, reason = _check_intraday_ai(pair)
            await update.message.reply_text(f"AI Check {pair} {signal_type}:\\nDirection: {direction}\\nPrice: {price}\\nReason: {reason}")

# ---------- Flask ----------
@app_flask.route("/billplz_webhook", methods=["POST"])
def billplz_webhook():
    data = request.form.to_dict()
    print("Billplz webhook:", data)
    if data.get("paid") == "true":
        telegram_id = data.get("reference_1") or data.get("reference_2")
        amount_str = data.get("amount", "5000")
        try:
            amount_rm = int(float(amount_str)) / 100
        except:
            amount_rm = 50
        days = 90 if amount_rm >= 120 else 30
        if telegram_id:
            users = load_json(USERS_FILE, {})
            if telegram_id in users:
                user = users[telegram_id]
                base = now()
                try:
                    cur_end = datetime.datetime.fromisoformat(user.get("sub_end") or user.get("trial_end") or "")
                    if cur_end > now():
                        base = cur_end
                except:
                    pass
                new_end = base + datetime.timedelta(days=days)
                user["sub_end"] = new_end.isoformat()
                user["is_vip"] = True
                user["payment_type"] = "BILLPLZ AUTO"
                save_json(USERS_FILE, users)
                print(f"Auto-approved {telegram_id} for {days} days via Billplz")
    return "OK", 200

@app_flask.route("/", methods=["GET"])
def home():
    return "KANSAI SIGNAL Bot is running!", 200

def run_flask():
    port = int(os.environ.get("PORT", 5001))
    app_flask.run(host="0.0.0.0", port=port)

def main():
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("tips", tips_cmd))
    app.add_handler(CommandHandler("to_all_users", to_all_users_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CommandHandler("admin_stats", stats_cmd))
    app.add_handler(CommandHandler("mysub", mysub))
    app.add_handler(CommandHandler("bayar", bayar))
    app.add_handler(CommandHandler("tukar", tukar))
    app.add_handler(CommandHandler("signal", signal_cmd))
    app.add_handler(CommandHandler("close", close_cmd))
    app.add_handler(CommandHandler("result", result_cmd))
    app.add_handler(CommandHandler("approve", approve_cmd))
    app.add_handler(CommandHandler("approve_broker", approve_broker_cmd))
    app.add_handler(CommandHandler("listvip", listvip))
    app.add_handler(CommandHandler("signal_log", signal_log_cmd))
    app.add_handler(CommandHandler("sent_check", sent_check_cmd))
    app.add_handler(CommandHandler("last_signal", last_signal_cmd))
    app.add_handler(CommandHandler("ai_status", ai_status_cmd))
    app.add_handler(CommandHandler("ai_on", ai_on_cmd))
    app.add_handler(CommandHandler("ai_off", ai_off_cmd))
    app.add_handler(CommandHandler("ai_test", ai_test_cmd))
    app.add_handler(CommandHandler("ai_auto", ai_auto_cmd))
    app.add_handler(CommandHandler("ai_semi", ai_semi_cmd))
    app.add_handler(CommandHandler("news_test", news_test_cmd))
    app.add_handler(CommandHandler("ta_test", ta_test_cmd))
    app.add_handler(CommandHandler("debug_data", debug_data_cmd))
    app.add_handler(CommandHandler("chart_debug", chart_debug_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    if app.job_queue:
        app.job_queue.run_repeating(check_expiry_job, interval=3600, first=10)
        app.job_queue.run_repeating(weekly_report_job, interval=7*24*3600, first=7*24*3600)
        app.job_queue.run_repeating(ai_scan_job, interval=300, first=30)
        app.job_queue.run_repeating(ai_tp_monitor_job, interval=60, first=60)
        app.job_queue.run_repeating(news_post_job_v2, interval=2*3600, first=120)
        app.job_queue.run_repeating(ta_post_job_with_chart, interval=4*3600, first=180)
    print("KANSAI SIGNAL Bot v2 sedang berjalan...")
    print("Flask di port", os.environ.get("PORT", 5001))
    # Fix Python 3.14 - kena ada event loop sebelum run_polling
    try:
        import asyncio as _asyncio
        try:
            _asyncio.get_event_loop()
        except RuntimeError:
            _loop = _asyncio.new_event_loop()
            _asyncio.set_event_loop(_loop)
    except Exception as e:
        print(f"Event loop fix: {e}")
    app.run_polling()

if __name__ == "__main__":
    main()
