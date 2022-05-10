import os
import sys
import traceback
from inspect import getfullargspec
from io import StringIO
from time import time

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from jmthon import app
from jmthon.config import OWNER_ID, BOT_NAME
from jmthon.database.chats import blacklist_chat, blacklisted_chats, whitelist_chat
from jmthon.utils.decorators import sudo_users_only
from jmthon.utils.filters import command
from jmthon.modules import check_heroku


@app.on_message(command(["ريستارت", "restart"]) & filters.user(OWNER_ID))
@check_heroku
async def gib_restart(client, message, hap):
    msg_ = await message.reply_text(f"⪼ {BOT_NAME} - جار اعادة تشغيله الان ...")
    hap.restart()


async def aexec(code, client, message):
    exec(
        "async def __aexec(client, message): "
        + "".join(f"\n {a}" for a in code.split("\n"))
    )
    return await locals()["__aexec"](client, message)


async def edit_or_reply(msg: Message, **kwargs):
    func = msg.edit_text if msg.from_user.is_self else msg.reply
    spec = getfullargspec(func.__wrapped__).args
    await func(**{k: v for k, v in kwargs.items() if k in spec})



@app.on_callback_query(filters.regex(r"runtime"))
async def runtime_func_cq(_, cq):
    runtime = cq.data.split(None, 1)[1]
    await cq.answer(runtime, show_alert=True)
