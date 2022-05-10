import asyncio

from pyrogram import Client, filters
from pyrogram.errors import UserAlreadyParticipant, FloodWait

from jmthon import app, ASSUSERNAME
from jmthon.utils.decorators import sudo_users_only, errors
from jmthon.utils.administrator import adminsOnly
from jmthon.utils.filters import command
from jmthon.tgcalls import client as USER


@app.on_message(
    command(["join", "انضمام", "jmthon"]) & ~filters.private & ~filters.bot
)
@errors
async def addchannel(client, message):
    if message.sender_chat:
        return await message.reply_text(
            "**⌔∮ يبدو انك مفعل وضع الاختفاء\n\n⪼ ارجع حسابك الى وضعه الطبيعي اولا"
        )
    permission = "can_delete_messages"
    m = await adminsOnly(permission, message)
    if m == 1:
        return
    chid = message.chat.id
    try:
        invite_link = await message.chat.export_invite_link()
        if "+" in invite_link:
            kontol = (invite_link.replace("+", "")).split("t.me/")[1]
            link_bokep = f"https://t.me/joinchat/{kontol}"
    except:
        await message.reply_text(
            "**⌔∮ يجب عليك رفعي مشرف اولا**",
        )
        return

    try:
        user = await USER.get_me()
    except:
        user.first_name = f"{ASSUSERNAME}"

    try:
        await USER.join_chat(link_bokep)
    except UserAlreadyParticipant:
        await message.reply_text(
            f"⪼ **{user.first_name} بالفعل مضاف في هذه الدردشة**",
        )
    except Exception as e:
        print(e)
        await message.reply_text(
            f"❃ **المساعد ({user.first_name}) لا يمكنه الانضمام لمجموعتك بسبب الضغط على بوتك **\n⌔∮ تأكد من أن الحساب غير محظور في المجموعه"
            f"\n\n⪼ قم يدويا بأضافه الحساب {user.first_name} للدردشة",
        )
        return


@USER.on_message(filters.group & command(["مغادرة", "مغادره", "leave"]))
async def rem(USER, message):
    if message.sender_chat:
        return await message.reply_text(
            "**⌔∮ يبدو انك مفعل وضع الاختفاء\n\n⪼ ارجع حسابك الى وضعه الطبيعي اولا"
        )
    permission = "can_delete_messages"
    m = await adminsOnly(permission, message)
    if m == 1:
        return
    try:
        await USER.send_message(
            message.chat.id,
            "**❃ تم بنجاح مغادره الحساب المساعد من الدردشه**",
        )
        await USER.leave_chat(message.chat.id)
    except:
        await message.reply_text(
            "❃ الحساب المساعد لا يمكنه المغادره يدويا بسبب الضغط على الحساب اطرده يدويا </b>"
        )

        return


@app.on_message(command(["leaveall", "خروج"]))
@sudo_users_only
async def bye(client, message):
    left = 0
    sleep_time = 0.1
    lol = await message.reply("**⪼ يتم مغادره جميع المجموعات انتظر قليلا**")
    async for dialog in USER.iter_dialogs():
        try:
            await USER.leave_chat(dialog.chat.id)
            await asyncio.sleep(sleep_time)
            left += 1
        except FloodWait as e:
            await asyncio.sleep(int(e.x))
        except Exception:
            pass
    await lol.edit(f"⪼ **تم بنجاح مغادره {left} من المجموعات**.")
