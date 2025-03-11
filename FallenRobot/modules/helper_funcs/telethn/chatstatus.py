from telethon.tl.types import ChannelParticipantsAdmins
from FallenRobot import DRAGONS
from FallenRobot.modules.helper_funcs.telethn import IMMUNE_USERS, telethn

# بررسی محافظت کاربر از بن
async def user_is_ban_protected(user_id: int, message):
    status = False
    if message.is_private or user_id in (IMMUNE_USERS):
        return True

    async for user in telethn.iter_participants(
        message.chat_id, filter=ChannelParticipantsAdmins
    ):
        if user_id == user.id:
            status = True
            break
    return status

# بررسی ادمین بودن کاربر
async def user_is_admin(user_id: int, message):
    status = False
    if message.is_private:
        return True

    async for user in telethn.iter_participants(
        message.chat_id, filter=ChannelParticipantsAdmins
    ):
        if user_id == user.id or user_id in DRAGONS:
            status = True
            break
    return status

# بررسی ادمین بودن کاربر در یک گروه خاص
async def is_user_admin(user_id: int, chat_id):
    status = False
    async for user in telethn.iter_participants(
        chat_id, filter=ChannelParticipantsAdmins
    ):
        if user_id == user.id or user_id in DRAGONS:
            status = True
            break
    return status

# بررسی ادمین بودن ربات
async def fallen_is_admin(chat_id: int):
    status = False
    fallen = await telethn.get_me()
    async for user in telethn.iter_participants(
        chat_id, filter=ChannelParticipantsAdmins
    ):
        if fallen.id == user.id:
            status = True
            break
    return status

# بررسی حضور کاربر در گروه
async def is_user_in_chat(chat_id: int, user_id: int):
    status = False
    async for user in telethn.iter_participants(chat_id):
        if user_id == user.id:
            status = True
            break
    return status

# بررسی دسترسی تغییر اطلاعات گروه
async def can_change_info(message):
    status = False
    if message.chat.admin_rights:
        status = message.chat.admin_rights.change_info
    return status

# بررسی دسترسی بن کردن کاربران
async def can_ban_users(message):
    status = False
    if message.chat.admin_rights:
        status = message.chat.admin_rights.ban_users
    return status

# بررسی دسترسی سنجاق کردن پیام‌ها
async def can_pin_messages(message):
    status = False
    if message.chat.admin_rights:
        status = message.chat.admin_rights.pin_messages
    return status

# بررسی دسترسی دعوت کاربران
async def can_invite_users(message):
    status = False
    if message.chat.admin_rights:
        status = message.chat.admin_rights.invite_users
    return status

# بررسی دسترسی افزودن ادمین
async def can_add_admins(message):
    status = False
    if message.chat.admin_rights:
        status = message.chat.admin_rights.add_admins
    return status

# بررسی دسترسی حذف پیام‌ها
async def can_delete_messages(message):
    if message.is_private:
        return True
    elif message.chat.admin_rights:
        status = message.chat.admin_rights.delete_messages
        return status
    else:
        return False
