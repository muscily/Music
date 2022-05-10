from asyncio import QueueEmpty

from pytgcalls.types.input_stream import InputAudioStream
from pytgcalls.types.input_stream import InputStream

from pyrogram import Client, filters
from pyrogram.types import Message

from jmthon import app
from jmthon.config import que
from jmthon.database.queue import (
    is_active_chat,
    add_active_chat,
    remove_active_chat,
    music_on,
    is_music_playing,
    music_off,
)
from jmthon.tgcalls import calls
from jmthon.utils.filters import command, other_filters
from jmthon.utils.decorators import sudo_users_only
from jmthon.tgcalls.queues import clear, get, is_empty, put, task_done


async def member_permissions(chat_id: int, user_id: int):
    perms = []
    try:
        member = await app.get_chat_member(chat_id, user_id)
    except Exception:
        return []
    if member.can_post_messages:
        perms.append("can_post_messages")
    if member.can_edit_messages:
        perms.append("can_edit_messages")
    if member.can_delete_messages:
        perms.append("can_delete_messages")
    if member.can_restrict_members:
        perms.append("can_restrict_members")
    if member.can_promote_members:
        perms.append("can_promote_members")
    if member.can_change_info:
        perms.append("can_change_info")
    if member.can_invite_users:
        perms.append("can_invite_users")
    if member.can_pin_messages:
        perms.append("can_pin_messages")
    if member.can_manage_voice_chats:
        perms.append("can_manage_voice_chats")
    return perms


from jmthon.utils.administrator import adminsOnly


@app.on_message(command(["pause", "ايقاف"]) & other_filters)
async def pause(_, message: Message):
    if message.sender_chat:
        return await message.reply_text(
            "**⌔∮ يبدو انك مفعل وضع الاختفاء\n\n⪼ ارجع حسابك الى وضعه الطبيعي اولا"
        )
    permission = "can_delete_messages"
    m = await adminsOnly(permission, message)
    if m == 1:
        return
    checking = message.from_user.mention
    chat_id = message.chat.id
    if not await is_active_chat(chat_id):
        return await message.reply_text(
            "**⌔∮ لم يتم تشغيل اي شيء بالاصل ليتم توقيفه**"
        )
    elif not await is_music_playing(message.chat.id):
        return await message.reply_text(
            "**⌔∮ لم يتم تشغيل اي شيء بالاصل ليتم توقيفه**"
        )
    await music_off(chat_id)
    await calls.pytgcalls.pause_stream(chat_id)
    await message.reply_text(
        f"**ايقاف مؤقت 🎧**\n\n تم ايقاف التشغيل مؤقتا {checking}"
    )


@app.on_message(command(["resume", "استئناف"]) & other_filters)
async def resume(_, message: Message):
    if message.sender_chat:
        return await message.reply_text(
            "**⌔∮ يبدو انك مفعل وضع الاختفاء\n\n⪼ ارجع حسابك الى وضعه الطبيعي اولا"
        )
    permission = "can_delete_messages"
    m = await adminsOnly(permission, message)
    if m == 1:
        return
    checking = message.from_user.mention
    chat_id = message.chat.id
    if not await is_active_chat(chat_id):
        return await message.reply_text(
            "**⌔∮ لا يوجد شيء مشغل ليتم استئنافه**"
        )
    elif await is_music_playing(chat_id):
        return await message.reply_text(
            "**⌔∮ لا يوجد شيء مشغل ليتم استئنافه**"
        )
    else:
        await music_on(chat_id)
        await calls.pytgcalls.resume_stream(chat_id)
        await message.reply_text(
            f"**أستئناف التشغيل 🎧**\n\nتم استئناف التشغيل بواسطة {checking}!"
        )


@app.on_message(command(["end", "انهاء"]) & other_filters)
async def stop(_, message: Message):
    if message.sender_chat:
        return await message.reply_text(
            "**⌔∮ يبدو انك مفعل وضع الاختفاء\n\n⪼ ارجع حسابك الى وضعه الطبيعي اولا"
        )
    permission = "can_delete_messages"
    m = await adminsOnly(permission, message)
    if m == 1:
        return
    checking = message.from_user.mention
    chat_id = message.chat.id
    if await is_active_chat(chat_id):
        try:
            clear(chat_id)
        except QueueEmpty:
            pass
        await remove_active_chat(chat_id)
        await calls.pytgcalls.leave_group_call(chat_id)
        await message.reply_text(
            f"**انهاء التشغيل 🎧**\n\nتم أنهاء التشغيل بواسطة {checking}!"
        )
    else:
        return await message.reply_text(
            "**⌔∮ عذرا لا يوجد اي شيء مشغل او غي الطابور ليتم الانهاء**"
        )


@app.on_message(command(["skip", "تخطي"]) & other_filters)
async def skip(_, message: Message):
    if message.sender_chat:
        return await message.reply_text(
            "**⌔∮ يبدو انك مفعل وضع الاختفاء\n\n⪼ ارجع حسابك الى وضعه الطبيعي اولا"
        )
    permission = "can_delete_messages"
    m = await adminsOnly(permission, message)
    if m == 1:
        return
    checking = message.from_user.mention
    chat_id = message.chat.id
    chat_title = message.chat.title
    if not await is_active_chat(chat_id):
        await message.reply_text("**⌔∮ لم يتم تشغيل اي شيء لبتم تخطيه**")
    else:
        task_done(chat_id)
        if is_empty(chat_id):
            await remove_active_chat(chat_id)
            await message.reply_text(
                "**تخطي المقطع الحالي 🎶**\n\nتم تخطي و مغادره المكالمه"
            )
            await calls.pytgcalls.leave_group_call(chat_id)
            return
        else:
            await calls.pytgcalls.change_stream(
                chat_id,
                InputStream(
                    InputAudioStream(
                        get(chat_id)["file"],
                    ),
                ),
            )
            await message.reply_text(
                f"**تخطي المقطع الحالي 🎶**\n\nتم التخطي بواسطة {checking}"
            )


@app.on_message(filters.command(["ضبط", "oc"]))
async def stop_cmd(_, message):
    if message.sender_chat:
        return await message.reply_text(
            "**⌔∮ يبدو انك مفعل وضع الاختفاء\n\n⪼ ارجع حسابك الى وضعه الطبيعي اولا"
        )
    permission = "can_delete_messages"
    m = await adminsOnly(permission, message)
    if m == 1:
        return
    chat_id = message.chat.id
    checking = message.from_user.mention
    try:
        clear(chat_id)
    except QueueEmpty:
        pass
    await remove_active_chat(chat_id)
    try:
        await calls.pytgcalls.leave_group_call(chat_id)
    except:
        pass
    await message.reply_text(
        f"⌔∮ حذف الطابور الحالي في **{message.chat.title}**\n\nتم مسح التخزين بواسطة {checking}"
    )
