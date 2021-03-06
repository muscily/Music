import asyncio
import requests
from pyrogram import Client
from pytgcalls import idle
from jmthon import app
from jmthon.database.functions import clean_restart_stage
from jmthon.database.queue import get_active_chats, remove_active_chat
from jmthon.tgcalls.calls import run
from jmthon.config import API_ID, API_HASH, BOT_TOKEN, BG_IMG


response = requests.get(BG_IMG)
with open("./etc/foreground.png", "wb") as file:
    file.write(response.content)


async def load_start():
    restart_data = await clean_restart_stage()
    if restart_data:
        print("[ملاحظه]: إرسال حالة إعادة التشغيل")
        try:
            await app.edit_message_text(
                restart_data["chat_id"],
                restart_data["message_id"],
                "**⪼ تم اعادة تشغيل البوت بنجاح**",
            )
        except Exception:
            pass
    served_chats = []
    try:
        chats = await get_active_chats()
        for chat in chats:
            served_chats.append(int(chat["chat_id"]))
    except Exception as e:
        print("حدث خطأ أثناء مسح التخزين")
    for served_chat in served_chats:
        try:
            await remove_active_chat(served_chat)
        except Exception as e:
            print("حدث خطأ اثناء مسح التخزين")
            pass
    print("[ملاحظة]: تم التشغيل")


loop = asyncio.get_event_loop_policy().get_event_loop()
loop.run_until_complete(load_start())

Client(
    ":memory:",
    API_ID,
    API_HASH,
    bot_token=BOT_TOKEN,
    plugins={"root": "jmthon.modules"},
).start()

run()
idle()
loop.close()
