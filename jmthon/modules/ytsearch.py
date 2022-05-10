import logging

from search_engine_parser import GoogleSearch
from youtube_search import YoutubeSearch

import pyrogram
from pyrogram import Client, filters
from pyrogram.types import Message

from jmthon import app
from jmthon.utils.filters import command


logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

logging.getLogger("pyrogram").setLevel(logging.WARNING)


@app.on_message(command(["search", "yt", "بحث"]))
async def ytsearch(_, message: Message):
    try:
        if len(message.command) < 2:
            await message.reply_text("`!بحث <عنوان>`")
            return
        query = message.text.split(None, 1)[1]
        m = await message.reply_text("⪼ جار البحث انتظر قليلا")
        results = YoutubeSearch(query, max_results=7).to_dict()
        text = ""
        for i in range(4):
            text += f"❂ **العنوان** - [{results[i]['title']}](https://youtube.com{results[i]['url_suffix']})\n"
            text += f"❂ **المدة** - {results[i]['duration']}\n"
            text += f"❂ **المشاهدات** - {results[i]['views']}\n"
            text += f"❂ **القناة** - {results[i]['channel']}\n\n"
        await m.edit(text, disable_web_page_preview=True)
    except Exception as e:
        await message.reply_text(str(e))
