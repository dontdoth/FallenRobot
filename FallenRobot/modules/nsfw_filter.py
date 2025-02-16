from Fallen import app
from Fallen.mongo import mongodb
from Fallen import SUDO_USERS
from pyrogram import filters
from pyrogram.types import Message
import os
import tempfile
from datetime import datetime
from nudenet import NudeDetector

# تنظیمات NSFW
nude_detector = NudeDetector()
NSFW_THRESHOLD = 0.98

# کالکشن برای تنظیمات NSFW
nsfw_settings = mongodb.nsfw_settings
nsfw_stats = mongodb.nsfw_stats

async def is_nsfw_enabled(chat_id: int) -> bool:
    """بررسی فعال بودن فیلتر NSFW"""
    settings = await nsfw_settings.find_one({'chat_id': chat_id})
    return settings['enabled'] if settings else True

async def is_nsfw_content(file_path: str) -> bool:
    """بررسی محتوای NSFW"""
    try:
        result = nude_detector.detect(file_path)
        for detection in result:
            if detection['score'] > NSFW_THRESHOLD:
                return True
        return False
    except Exception as e:
        print(f"NSFW detection error: {e}")
        return False

async def update_nsfw_stats(chat_id: int):
    """آپدیت آمار NSFW"""
    stats = await nsfw_stats.find_one({'chat_id': chat_id})
    if not stats:
        await nsfw_stats.insert_one({
            'chat_id': chat_id,
            'total_deleted': 1,
            'last_updated': datetime.now()
        })
    else:
        await nsfw_stats.update_one(
            {'chat_id': chat_id},
            {'$inc': {'total_deleted': 1},
             '$set': {'last_updated': datetime.now()}}
        )

@app.on_message(filters.group & (filters.photo | filters.video | filters.animation | filters.sticker))
async def nsfw_filter(_, message: Message):
    """فیلتر محتوای NSFW"""
    try:
        chat_id = message.chat.id
        
        # بررسی فعال بودن فیلتر
        if not await is_nsfw_enabled(chat_id):
            return
        
        # دریافت فایل
        if message.photo:
            file_id = message.photo.file_id
        elif message.video:
            file_id = message.video.file_id
        elif message.animation:
            file_id = message.animation.file_id
        elif message.sticker:
            file_id = message.sticker.file_id
        else:
            return

        # دانلود و بررسی فایل
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            file_path = temp_file.name
            await message.download(file_path)
            
            if await is_nsfw_content(file_path):
                try:
                    # حذف پیام
                    await message.delete()
                    
                    # ارسال هشدار
                    warn_msg = (
                        f"⚠️ پیام کاربر {message.from_user.mention} به دلیل محتوای نامناسب حذف شد.\n"
                        "🔞 لطفاً از ارسال محتوای نامناسب خودداری کنید."
                    )
                    warn = await message.reply_text(warn_msg)
                    
                    # حذف هشدار بعد از 10 ثانیه
                    await asyncio.sleep(10)
                    await warn.delete()
                    
                    # آپدیت آمار
                    await update_nsfw_stats(chat_id)
                    
                except Exception as e:
                    print(f"Error deleting NSFW content: {e}")
            
            # حذف فایل موقت
            os.unlink(file_path)

    except Exception as e:
        print(f"NSFW filter error: {e}")

# دستورات مدیریت NSFW
@app.on_message(filters.command("nsfw") & filters.group)
async def nsfw_command(_, message: Message):
    """مدیریت تنظیمات NSFW"""
    # فقط ادمین‌ها
    if message.from_user.id not in SUDO_USERS:
        return await message.reply_text("⛔️ شما دسترسی ندارید!")
        
    chat_id = message.chat.id
    args = message.text.split()
    
    if len(args) == 1:
        # نمایش وضعیت فعلی
        enabled = await is_nsfw_enabled(chat_id)
        stats = await nsfw_stats.find_one({'chat_id': chat_id})
        
        status_text = (
            "🔞 وضعیت فیلتر NSFW:\n\n"
            f"• وضعیت: {'فعال ✅' if enabled else 'غیرفعال ❌'}\n"
            f"• دقت تشخیص: {NSFW_THRESHOLD * 100}%\n"
            f"• تعداد حذف شده: {stats['total_deleted'] if stats else 0}\n"
            f"• آخرین بروزرسانی: {stats['last_updated'].strftime('%Y-%m-%d %H:%M:%S') if stats else 'هیچ'}\n\n"
            "📝 راهنما:\n"
            "• /nsfw on - فعال کردن فیلتر\n"
            "• /nsfw off - غیرفعال کردن فیلتر\n"
            "• /nsfw stats - مشاهده آمار"
        )
        
        await message.reply_text(status_text)
        
    elif args[1] in ['on', 'off']:
        # تغییر وضعیت
        enabled = args[1] == 'on'
        await nsfw_settings.update_one(
            {'chat_id': chat_id},
            {'$set': {'enabled': enabled}},
            upsert=True
        )
        
        await message.reply_text(
            f"✅ فیلتر NSFW {'فعال' if enabled else 'غیرفعال'} شد."
        )
        
    elif args[1] == 'stats':
        # نمایش آمار
        stats = await nsfw_stats.find_one({'chat_id': chat_id})
        if not stats:
            return await message.reply_text("📊 هیچ آماری موجود نیست!")
            
        stats_text = (
            "📊 آمار فیلتر NSFW:\n\n"
            f"• تعداد کل حذف شده: {stats['total_deleted']}\n"
            f"• آخرین بروزرسانی: {stats['last_updated'].strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        await message.reply_text(stats_text)
