import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, F, Router
from aiogram.types import (
    Message, CallbackQuery,
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

# =============================================
# SOZLAMALAR
# =============================================
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ADMIN_IDS = [7980523374]
ADMIN_CARD = "9860 0466 1364 6200"
ADMIN_CARD_HOLDER = "Kamron Qayumov"

WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://rivomc.onrender.com")
PORT = int(os.getenv("PORT", 3001))

# =============================================
# RANKLAR 
# =============================================
RANKS = [
    {"id": "elvarox",  "name": "🔹 ᴇʟᴠᴀʀᴏх",  "price": 6000,  "group": "elvarox"},
    {"id": "zorvex",   "name": "🔸 ᴢᴏʀᴠᴇх",   "price": 11000, "group": "zorvex"},
    {"id": "nexora",   "name": "🟡 ɴᴇхᴏʀᴀ",   "price": 16000, "group": "nexora"},
    {"id": "veltrixa", "name": "🟠 ᴠᴇʟᴛʀɪхᴀ", "price": 23000, "group": "veltrixa"},
    {"id": "kyronex",  "name": "🔴 ᴋʏʀᴏɴᴇх",  "price": 29000, "group": "kyronex"},
    {"id": "zenthra",  "name": "🟣 ᴢᴇɴᴛʜʀᴀ",  "price": 36000, "group": "zenthra"},
    {"id": "aurexis",  "name": "🔵 ᴀᴜʀᴇхɪѕ",  "price": 45000, "group": "aurexis"},
    {"id": "vyronix",  "name": "👑 ᴠʏʀᴏɴɪх",  "price": 56000, "group": "vyronix"},
]

# =============================================
# XIZMATLAR
# =============================================
SERVICES = {
    "unban_1":     {"name": "🔓 ᴜɴʙᴀɴ x1",       "price": 10000, "type": "unban",     "count": 1},
    "unban_3":     {"name": "🔓 ᴜɴʙᴀɴ x3",       "price": 25000, "type": "unban",     "count": 3},
    "unmute_1":    {"name": "🔊 ᴜɴᴍᴜᴛᴇ x1",      "price": 5000,  "type": "unmute",   "count": 1},
    "unmute_3":    {"name": "🔊 ᴜɴᴍᴜᴛᴇ x3",      "price": 10000, "type": "unmute",   "count": 3},
    "donatkase_1": {"name": "🎁 ᴅᴏɴᴀᴛ ᴋᴀꜱᴇ x1", "price": 15000, "type": "donatkase","count": 1},
    "donatkase_3": {"name": "🎁 ᴅᴏɴᴀᴛ ᴋᴀꜱᴇ x3", "price": 30000, "type": "donatkase","count": 3},
}

# =============================================
# TOKEN NARXLARI
# =============================================
TOKEN_OPTIONS = [
    {"amount": 1000,  "price": 3000},
    {"amount": 5000,  "price": 15000},
    {"amount": 10000, "price": 25000},
    {"amount": 25000, "price": 60000},
    {"amount": 50000, "price": 110000},
]

def calc_token_price(amount: int) -> int:
    if amount >= 10000:
        return (amount // 10000) * 25000 + calc_token_price(amount % 10000)
    return (amount // 1000) * 3000 + (3000 if amount % 1000 > 0 else 0)

# =============================================
# YORDAMCHI
# =============================================
orders: dict = {}
order_counter = 1

def fmt(p: int) -> str:
    return f"{p:,}".replace(",", " ") + " so'm"

def is_admin(uid: int) -> bool:
    return uid in ADMIN_IDS

# =============================================
# FSM STATES
# =============================================
class OrderState(StatesGroup):
    enter_nick = State()
    wait_chek_confirm = State()
    send_chek = State()
    enter_token_amount = State()



# =============================================
# KLAVIATURALAR
# =============================================
def main_menu(user_id: int) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text="🏆 ʀᴀɴᴋ ꜱᴏᴛɪʙ ᴏʟɪꜱʜ"), KeyboardButton(text="🪙 ᴛᴏᴋᴇɴ ꜱᴏᴛɪʙ ᴏʟɪꜱʜ")],
        [KeyboardButton(text="🔓 ᴜɴʙᴀɴ / ᴜɴᴍᴜᴛᴇ / ᴋᴀꜱᴇ"), KeyboardButton(text="📦 ʙᴜʏᴜʀᴛᴍᴀʟᴀʀɪᴍ")],
        [KeyboardButton(text="❓ ʏᴏʀᴅᴀᴍ")],
    ]
    if is_admin(user_id):
        rows.append([KeyboardButton(text="⚙️ ᴀᴅᴍɪɴ ᴘᴀɴᴇʟ")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)

def rank_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    for r in RANKS:
        buttons.append([InlineKeyboardButton(
            text=f"{r['name']} — {fmt(r['price'])}",
            callback_data=f"rank_{r['id']}"
        )])
    buttons.append([InlineKeyboardButton(text="🔙 ᴏʀQᴀɢᴀ", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def token_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    for opt in TOKEN_OPTIONS:
        buttons.append([InlineKeyboardButton(
            text=f"{opt['amount']:,} token — {fmt(opt['price'])}".replace(",", " "),
            callback_data=f"token_{opt['amount']}"
        )])
    buttons.append([InlineKeyboardButton(text="✍️ ʙᴏꜱʜQᴀ ᴍɪQᴅᴏʀ", callback_data="token_custom")])
    buttons.append([InlineKeyboardButton(text="🔙 ᴏʀQᴀɢᴀ", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def service_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    for key, s in SERVICES.items():
        buttons.append([InlineKeyboardButton(
            text=f"{s['name']} — {fmt(s['price'])}",
            callback_data=f"service_{key}"
        )])
    buttons.append([InlineKeyboardButton(text="🔙 ᴏʀQᴀɢᴀ", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📸 ᴄʜᴇᴋ ʏᴜʙᴏʀɪꜱʜɢᴀ ᴛᴀʏʏᴏʀ", callback_data="ready_chek")],
        [InlineKeyboardButton(text="❌ ʙᴇᴋᴏʀ Qɪʟɪꜱʜ", callback_data="back_main")]
    ])

def back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 ᴏʀQᴀɢᴀ", callback_data="back_main")]
    ])

# =============================================
# ROUTER
# =============================================
router = Router()

# /start
@router.message(CommandStart())
async def cmd_start(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer(
        "🌑 <b>RivoMC Donate Botga xush kelibsiz!</b>\n\n"
        "⚔️ Server: <b>Anarxiya</b>\n\n"
        "🏆 Rank sotib olish\n🪙 Token sotib olish\n"
        "🔓 Unban / Unmute / Kase\n📦 Buyurtmalarni kuzatish\n\n"
        "👇 Tugmani tanlang:",
        parse_mode="HTML",
        reply_markup=main_menu(msg.from_user.id)
    )

# ─── RANK ───
@router.message(F.text == "🏆 ʀᴀɴᴋ ꜱᴏᴛɪʙ ᴏʟɪꜱʜ")
async def menu_rank(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer(
        "🏆 <b>⚔️ Anarxiya — Rank tanlang:</b>\n",
        parse_mode="HTML",
        reply_markup=rank_keyboard()
    )

# ─── TOKEN ───
@router.message(F.text == "🪙 ᴛᴏᴋᴇɴ ꜱᴏᴛɪʙ ᴏʟɪꜱʜ")
async def menu_token(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer(
        "🪙 <b>Token sotib olish</b>\n\n"
        "💰 Narx:\n"
        "1,000 token = 3,000 so'm\n"
        "10,000 token = 25,000 so'm\n\n"
        "Qancha token kerak?",
        parse_mode="HTML",
        reply_markup=token_keyboard()
    )

# ─── XIZMAT ───
@router.message(F.text == "🔓 ᴜɴʙᴀɴ / ᴜɴᴍᴜᴛᴇ / ᴋᴀꜱᴇ")
async def menu_service(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer(
        "🔓 <b>Xizmat tanlang:</b>",
        parse_mode="HTML",
        reply_markup=service_keyboard()
    )

# ─── BUYURTMALARIM ───
@router.message(F.text == "📦 ʙᴜʏᴜʀᴛᴍᴀʟᴀʀɪᴍ")
async def menu_orders(msg: Message):
    uid = msg.from_user.id
    my = [o for o in orders.values() if o["user_id"] == uid][-5:]
    if not my:
        await msg.answer("📦 Sizda hali buyurtma yo'q.", reply_markup=main_menu(uid))
        return
    txt = "📦 <b>So'nggi buyurtmalar:</b>\n\n"
    for o in reversed(my):
        e = "⏳" if o["status"] == "pending" else ("✅" if o["status"] == "completed" else "❌")
        txt += f"{e} #{o['id']} — {o['type']}\n💰 {fmt(o['price'])} | 🎮 {o['nick']}\n\n"
    await msg.answer(txt, parse_mode="HTML", reply_markup=main_menu(uid))

# ─── YORDAM ───
@router.message(F.text == "❓ ʏᴏʀᴅᴀᴍ")
async def menu_help(msg: Message):
    await msg.answer(
        "❓ <b>Yordam</b>\n\n"
        "1️⃣ Rank, Token yoki xizmat tanlang\n"
        "2️⃣ Minecraft nickingizni kiriting\n"
        "3️⃣ Karta raqamiga pul o'tkazing\n"
        "4️⃣ Chek rasmini yuboring\n"
        "5️⃣ Admin tasdiqlaganda avtomatik beriladi!\n\n"
        "💰 <b>Token narxi:</b>\n"
        "1,000 token = 3,000 so'm\n"
        "10,000 token = 25,000 so'm\n\n"
        "🌐 Server: RivoMC.Uz",
        parse_mode="HTML",
        reply_markup=main_menu(msg.from_user.id)
    )

# ─── ADMIN PANEL ───
@router.message(F.text == "⚙️ ᴀᴅᴍɪɴ ᴘᴀɴᴇʟ")
async def menu_admin(msg: Message):
    if not is_admin(msg.from_user.id):
        return
    await show_admin_panel(msg.from_user.id, msg.bot)

async def show_admin_panel(uid: int, bot: Bot):
    pending = sum(1 for o in orders.values() if o["status"] == "pending")
    await bot.send_message(
        uid,
        f"⚙️ <b>Admin Panel</b>\n⏳ Kutayotgan: <b>{pending}</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📦 ʙᴀʀᴄʜᴀ ʙᴜʏᴜʀᴛᴍᴀʟᴀʀ", callback_data="admin_orders")]
        ])
    )

# ─── TOKEN MIQDORI (custom) ───
@router.message(OrderState.enter_token_amount)
async def handle_token_amount(msg: Message, state: FSMContext):
    try:
        amount = int(msg.text.strip())
        if amount < 100:
            raise ValueError
    except ValueError:
        await msg.answer("❌ Noto'g'ri miqdor! Kamida 100 token kiriting.")
        return
    price = calc_token_price(amount)
    item_name = f"🪙 {amount:,} ᴛᴏᴋᴇɴ".replace(",", " ")
    await state.update_data(item_name=item_name, price=price, service_type="tokens", token_amount=amount)
    await state.set_state(OrderState.enter_nick)
    await msg.answer(
        f"{item_name}\n💰 <b>{fmt(price)}</b>\n\n🎮 Minecraft nickingizni kiriting:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔙 ᴏʀQᴀɢᴀ", callback_data="back_main")
        ]])
    )

# ─── NICK KIRITISH ───
@router.message(OrderState.enter_nick)
async def handle_nick(msg: Message, state: FSMContext):
    nick = msg.text.strip()
    if len(nick) < 2 or len(nick) > 20 or not nick.replace("_", "").isalnum():
        await msg.answer("❌ Noto'g'ri nick! Faqat harflar, raqamlar va _ ishlatiladi.")
        return
    data = await state.get_data()
    await state.update_data(nick=nick)
    await state.set_state(OrderState.wait_chek_confirm)
    await msg.answer(
        f"✅ <b>Nick:</b> <code>{nick}</code>\n"
        f"📋 <b>Buyurtma:</b> {data['item_name']}\n"
        f"💰 <b>Summa:</b> {fmt(data['price'])}\n\n"
        f"💳 <b>Karta:</b>\n<code>{ADMIN_CARD}</code>\n"
        f"👤 <b>Egasi:</b> {ADMIN_CARD_HOLDER}\n\n"
        f"⚠️ <b>{fmt(data['price'])}</b> o'tkazib, chek rasmini yuboring!",
        parse_mode="HTML",
        reply_markup=confirm_keyboard()
    )

# ─── CHEK FOTO ───
@router.message(OrderState.send_chek, F.photo)
async def handle_chek(msg: Message, state: FSMContext):
    global order_counter
    data = await state.get_data()
    uid = msg.from_user.id
    oid = order_counter
    order_counter += 1

    order = {
        "id": oid,
        "user_id": uid,
        "nick": data["nick"],
        "type": data["item_name"],
        "price": data["price"],
        "group": data.get("group"),
        "service_type": data.get("service_type"),
        "token_amount": data.get("token_amount"),
        "status": "pending",
        "photo_file_id": msg.photo[-1].file_id,
        "username": f"@{msg.from_user.username}" if msg.from_user.username else msg.from_user.first_name,
    }
    orders[oid] = order
    await state.clear()

    await msg.answer(
        f"✅ <b>Buyurtma qabul qilindi!</b>\n\n"
        f"📦 #{oid} — {order['type']}\n"
        f"🎮 Nick: <code>{order['nick']}</code>\n"
        f"💰 {fmt(order['price'])}\n\n"
        f"⏳ Admin tekshirgandan so'ng <b>avtomatik</b> beriladi!",
        parse_mode="HTML",
        reply_markup=main_menu(uid)
    )

    caption = (
        f"🧾 <b>Yangi buyurtma #{oid}!</b>\n\n"
        f"👤 {order['username']} (ID: <code>{uid}</code>)\n"
        f"🎮 Nick: <code>{order['nick']}</code>\n"
        f"🛒 {order['type']}\n"
        f"💰 {fmt(order['price'])}"
    )
    admin_kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=f"✅ ᴛᴀꜱᴅɪQʟᴀꜱʜ #{oid}", callback_data=f"confirm_{oid}"),
        InlineKeyboardButton(text=f"❌ ʀᴀᴅ ᴇᴛɪꜱʜ #{oid}",  callback_data=f"reject_{oid}"),
    ]])
    for admin_id in ADMIN_IDS:
        try:
            await msg.bot.send_photo(
                admin_id,
                photo=order["photo_file_id"],
                caption=caption,
                parse_mode="HTML",
                reply_markup=admin_kb
            )
        except Exception as e:
            logging.error(e)

@router.message(OrderState.send_chek)
async def handle_chek_wrong(msg: Message):
    await msg.answer("📸 Iltimos, chek rasmini <b>rasm</b> sifatida yuboring.", parse_mode="HTML")

# =============================================
# CALLBACK QUERY
# =============================================
@router.callback_query()
async def handle_callback(cb: CallbackQuery, state: FSMContext):
    uid = cb.from_user.id
    data = cb.data
    await cb.answer()

    # ─── RANK TANLASH ───
    if data.startswith("rank_"):
        rank_id = data[5:]
        rank = next((r for r in RANKS if r["id"] == rank_id), None)
        if not rank:
            return
        await state.update_data(item_name=rank["name"], price=rank["price"], group=rank["group"], service_type=None)
        await state.set_state(OrderState.enter_nick)
        await cb.message.edit_text(
            f"{rank['name']}\n💰 <b>{fmt(rank['price'])}</b>\n\n🎮 Minecraft nickingizni kiriting:",
            parse_mode="HTML",
            reply_markup=back_keyboard()
        )

    # ─── TOKEN TANLASH ───
    elif data.startswith("token_"):
        amount_str = data[6:]
        if amount_str == "custom":
            await state.set_state(OrderState.enter_token_amount)
            await cb.message.edit_text(
                "✍️ <b>Token miqdorini kiriting:</b>\n\nMasalan: 3000, 7500, 15000\nMinimum: 100 token",
                parse_mode="HTML",
                reply_markup=back_keyboard()
            )
            return
        amount = int(amount_str)
        price = calc_token_price(amount)
        item_name = f"🪙 {amount:,} ᴛᴏᴋᴇɴ".replace(",", " ")
        await state.update_data(item_name=item_name, price=price, service_type="tokens", token_amount=amount)
        await state.set_state(OrderState.enter_nick)
        await cb.message.edit_text(
            f"{item_name}\n💰 <b>{fmt(price)}</b>\n\n🎮 Minecraft nickingizni kiriting:",
            parse_mode="HTML",
            reply_markup=back_keyboard()
        )

    # ─── XIZMAT TANLASH ───
    elif data.startswith("service_"):
        svc_key = data[8:]
        svc = SERVICES.get(svc_key)
        if not svc:
            return
        await state.update_data(item_name=svc["name"], price=svc["price"], service_type=svc["type"], svc_count=svc["count"])
        await state.set_state(OrderState.enter_nick)
        await cb.message.edit_text(
            f"{svc['name']}\n💰 <b>{fmt(svc['price'])}</b>\n\n🎮 Minecraft nickingizni kiriting:",
            parse_mode="HTML",
            reply_markup=back_keyboard()
        )

    # ─── CHEK TAYYOR ───
    elif data == "ready_chek":
        await state.set_state(OrderState.send_chek)
        await cb.message.answer(
            "📸 Bank ilovangizdan to'lov cheki rasmini yuboring:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="🔙 ᴏʀQᴀɢᴀ", callback_data="back_main")
            ]])
        )

    # ─── ORQAGA ───
    elif data == "back_main":
        await state.clear()
        await cb.message.answer("🏠 Asosiy menyu:", reply_markup=main_menu(uid))

    # ─── ADMIN: TASDIQLASH ───
    elif data.startswith("confirm_") and is_admin(uid):
        oid = int(data[8:])
        order = orders.get(oid)
        if not order:
            await cb.message.answer("❌ Buyurtma topilmadi.")
            return
        if order["status"] != "pending":
            await cb.message.answer("⚠️ Buyurtma allaqachon ko'rib chiqilgan.")
            return

        order["status"] = "completed"

        # Foydalanuvchiga xabar yuborish
        await cb.bot.send_message(
            order["user_id"],
            f"✅ <b>To'lovingiz tasdiqlandi!</b>\n\n"
            f"📦 #{oid} — {order['type']}\n"
            f"🎮 Nick: <code>{order['nick']}</code>\n"
            f"💰 {fmt(order['price'])}\n\n"
            f"🎉 Tez orada serverga kirib tekshiring!\n"
            f"❓ Muammo bo'lsa admin bilan bog'laning.",
            parse_mode="HTML"
        )

        # Admin xabarini yangilash
        try:
            await cb.message.edit_caption(
                f"✅ <b>TASDIQLANDI #{oid}</b>\n"
                f"🎮 {order['nick']} | {order['type']}\n"
                f"👨‍💼 Admin: @{cb.from_user.username or cb.from_user.first_name}",
                parse_mode="HTML"
            )
        except Exception:
            pass

    # ─── ADMIN: RAD ETISH ───
    elif data.startswith("reject_") and is_admin(uid):
        oid = int(data[7:])
        order = orders.get(oid)
        if not order:
            return
        order["status"] = "rejected"
        await cb.bot.send_message(
            order["user_id"],
            f"❌ <b>Buyurtmangiz rad etildi.</b>\n"
            f"📦 #{oid} — {order['type']}\n"
            f"❓ Savol bo'lsa admin bilan bog'laning.",
            parse_mode="HTML"
        )
        try:
            await cb.message.edit_caption(
                f"❌ <b>RAD ETILDI #{oid}</b>\n🎮 {order['nick']} | {order['type']}\n"
                f"👨‍💼 @{cb.from_user.username or cb.from_user.first_name}",
                parse_mode="HTML"
            )
        except Exception:
            pass

    # ─── ADMIN: BARCHA BUYURTMALAR ───
    elif data == "admin_orders" and is_admin(uid):
        all_orders = list(orders.values())[-10:]
        if not all_orders:
            await cb.message.answer("📦 Hali buyurtma yo'q.")
            return
        txt = "📦 <b>So'nggi 10 buyurtma:</b>\n\n"
        for o in reversed(all_orders):
            e = "⏳" if o["status"] == "pending" else ("✅" if o["status"] == "completed" else "❌")
            txt += f"{e} #{o['id']} | {o['nick']} | {o['type']} | {fmt(o['price'])}\n"
        await cb.message.answer(txt, parse_mode="HTML")

# =============================================
# MAIN
# =============================================
async def main():
    logging.basicConfig(level=logging.INFO)

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    webhook_path = f"/bot{BOT_TOKEN}"
    webhook_full_url = f"{WEBHOOK_URL}{webhook_path}"

    # Simple HTTP server — bot is running
    app_web = web.Application()

    async def health(request):
        return web.Response(text="✅ RivoMC Bot is running!")

    app_web.router.add_get("/", health)
    app_web.router.add_get("/health", health)

    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app_web, path=webhook_path)
    setup_application(app_web, dp, bot=bot)

    await bot.set_webhook(webhook_full_url)
    logging.info(f"✅ Webhook: {webhook_full_url}")
    logging.info(f"🚀 RivoMC Bot is running on port {PORT}")

    runner = web.AppRunner(app_web)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
