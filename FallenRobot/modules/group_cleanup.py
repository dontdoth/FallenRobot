from Fallen import app
from Fallen.mongo import mongodb
from Fallen import SUDO_USERS
from pyrogram import filters
from pyrogram.types import (
    Message, 
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery
)
from pyrogram.errors import UserAlreadyParticipant, FloodWait
import asyncio
import time
from datetime import datetime

# تنظیمات
ADMINS = SUDO_USERS
bot = app
stats_collection = mongodb.cleanup_stats  # تغییر نام کالکشن برای جلوگیری از تداخل
COOLDOWN = 3

# کیبورد اصلی
MAIN_KEYBOARD = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("🗑 پاکسازی پیام‌ها", callback_data="cleanup_menu"),
        InlineKeyboardButton("📊 آمار", callback_data="cleanup_stats")
    ],
    [InlineKeyboardButton("⚙️ تنظیمات", callback_data="cleanup_settings")]
])

# کیبورد پاکسازی
CLEAN_KEYBOARD = InlineKeyboardMarkup([
    [
        InlineKeyboardButton("🖼 عکس", callback_data="cleanup_photo"),
        InlineKeyboardButton("🎥 ویدیو", callback_data="cleanup_video"),
        InlineKeyboardButton("🎭 گیف", callback_data="cleanup_gif")
    ],
    [
        InlineKeyboardButton("🎵 صدا", callback_data="cleanup_voice"),
        InlineKeyboardButton("📄 متن", callback_data="cleanup_text"),
        InlineKeyboardButton("🏷 استیکر", callback_data="cleanup_sticker")
    ],
    [InlineKeyboardButton("🔙 برگشت", callback_data="cleanup_main")]
])

async def update_stats(deleted_count: int):
    """آپدیت آمار در دیتابیس"""
    stats = await stats_collection.find_one({'_id': 'cleanup_stats'})
    if not stats:
        await stats_collection.insert_one({
            '_id': 'cleanup_stats',
            'total_deleted': deleted_count,
            'today_deleted': deleted_count,
            'last_updated': datetime.now()
        })
    else:
        await stats_collection.update_one(
            {'_id': 'cleanup_stats'},
            {'$inc': {
                'total_deleted': deleted_count,
                'today_deleted': deleted_count
            },
             '$set': {'last_updated': datetime.now()}}
        )

@app.on_message(filters.command("cleanup"))
async def cleanup_command(_, message: Message):
    """دستور پاکسازی"""
    if message.from_user.id not in ADMINS:
        return await message.reply_text("⛔️ شما دسترسی ندارید!")

    await message.reply_text(
        "🗑 منوی پاکسازی گروه\n\n"
        "نوع محتوا را انتخاب کنید:",
        reply_markup=CLEAN_KEYBOARD
    )

@app.on_callback_query(filters.regex("^cleanup_"))
async def handle_cleanup_callbacks(_, callback: CallbackQuery):
    """مدیریت کالبک‌های پاکسازی"""
    data = callback.data.replace("cleanup_", "")
    
    if data == "main":
        await callback.edit_message_text(
            "🏠 منوی اصلی پاکسازی\n\n"
            "از دکمه‌های زیر استفاده کنید:",
            reply_markup=MAIN_KEYBOARD
        )
        
    elif data == "menu":
        await callback.edit_message_text(
            "🗑 منوی پاکسازی گروه\n\n"
            "نوع محتوا را انتخاب کنید:",
            reply_markup=CLEAN_KEYBOARD
        )
        
    elif data in ["photo", "video", "gif", "voice", "text", "sticker"]:
        await start_cleanup(callback, data)
        
    elif data == "stats":
        await show_cleanup_stats(callback)

async def start_cleanup(callback: CallbackQuery, content_type: str):
    """شروع عملیات پاکسازی"""
    if callback.from_user.id not in ADMINS:
        return await callback.answer("⛔️ شما دسترسی ندارید!", show_alert=True)

    status_msg = await callback.edit_message_text(
        f"🔄 در حال پاکسازی {content_type}...\n"
        "لطفاً صبر کنید..."
    )

    deleted_count = 0
    try:
        async for msg in app.get_chat_history(callback.message.chat.id):
            should_delete = False
            
            if content_type == "photo" and msg.photo:
                should_delete = True
            elif content_type == "video" and msg.video:
                should_delete = True
            elif content_type == "gif" and msg.animation:
                should_delete = True
            elif content_type == "voice" and msg.voice:
                should_delete = True
            elif content_type == "text" and msg.text:
                should_delete = True
            elif content_type == "sticker" and msg.sticker:
                should_delete = True
                
            if should_delete:
                try:
                    await msg.delete()
                    deleted_count += 1
                    if deleted_count % 50 == 0:
                        await status_msg.edit_text(
                            f"🔄 در حال پاکسازی...\n"
                            f"تعداد پاک شده: {deleted_count}"
                        )
                    await asyncio.sleep(0.5)
                except Exception as e:
                    print(f"خطا در حذف پیام: {e}")

        await update_stats(deleted_count)
        
        await status_msg.edit_text(
            f"✅ پاکسازی با موفقیت انجام شد!\n\n"
            f"📊 نتیجه:\n"
            f"• نوع محتوا: {content_type}\n"
            f"• تعداد پاک شده: {deleted_count}\n"
            f"• زمان: {datetime.now().strftime('%H:%M:%S')}",
            reply_markup=CLEAN_KEYBOARD
        )
    except Exception as e:
        await status_msg.edit_text(
            f"❌ خطا در پاکسازی:\n{str(e)}",
            reply_markup=CLEAN_KEYBOARD
        )

async def show_cleanup_stats(callback: CallbackQuery):
    """نمایش آمار پاکسازی"""
    stats = await stats_collection.find_one({'_id': 'cleanup_stats'})
    if not stats:
        return await callback.edit_message_text(
            "📊 هیچ آماری موجود نیست!",
            reply_markup=MAIN_KEYBOARD
        )

    await callback.edit_message_text(
        f"📊 آمار پاکسازی گروه:\n\n"
        f"• کل پیام‌های پاک شده: {stats['total_deleted']}\n"
        f"• پاک شده امروز: {stats['today_deleted']}\n"
        f"• آخرین بروزرسانی: {stats['last_updated'].strftime('%Y-%m-%d %H:%M:%S')}",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 برگشت", callback_data="cleanup_main")
        ]])
    )

# ریست کردن آمار روزانه در نیمه شب
async def reset_daily_stats():
    while True:
        now = datetime.now()
        if now.hour == 0 and now.minute == 0:
            await stats_collection.update_one(
                {'_id': 'cleanup_stats'},
                {'$set': {'today_deleted': 0}}
            )
        await asyncio.sleep(60)

# شروع تسک ریست آمار روزانه
app.loop.create_task(reset_daily_stats())
