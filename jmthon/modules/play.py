import aiofiles
import ffmpeg
import asyncio
import os
import shutil
import psutil
import subprocess
import requests
import aiohttp
import yt_dlp

from os import path
from typing import Union
from asyncio import QueueEmpty
from PIL import Image, ImageFont, ImageDraw
from typing import Callable

from pytgcalls import StreamType
from pytgcalls.types.input_stream import InputStream
from pytgcalls.types.input_stream import InputAudioStream

from youtube_search import YoutubeSearch

from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    Voice,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery,
)
from pyrogram.errors import UserAlreadyParticipant, UserNotParticipant

from jmthon.tgcalls import calls, queues
from jmthon.tgcalls.calls import client as ASS_ACC
from jmthon.database.queue import (
    get_active_chats,
    is_active_chat,
    add_active_chat,
    remove_active_chat,
    music_on,
    is_music_playing,
    music_off,
)
from jmthon import app
import jmthon.tgcalls
from jmthon.tgcalls import youtube
from jmthon.config import (
    DURATION_LIMIT,
    que,
    SUDO_USERS,
    BOT_ID,
    ASSNAME,
    ASSUSERNAME,
    ASSID,
    SUPPORT,
    UPDATE,
    BOT_USERNAME,
)
from jmthon.utils.filters import command
from jmthon.utils.decorators import errors, sudo_users_only
from jmthon.utils.administrator import adminsOnly
from jmthon.utils.errors import DurationLimitError
from jmthon.utils.gets import get_url, get_file_name
from jmthon.modules.admins import member_permissions


# plus
chat_id = None
DISABLED_GROUPS = []
useer = "NaN"
flex = {}


def transcode(filename):
    ffmpeg.input(filename).output(
        "input.raw", format="s16le", acodec="pcm_s16le", ac=2, ar="48k"
    ).overwrite_output().run()
    os.remove(filename)


# Convert seconds to mm:ss
def convert_seconds(seconds):
    seconds = seconds % (24 * 3600)
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return "%02d:%02d" % (minutes, seconds)


# Convert hh:mm:ss to seconds
def time_to_seconds(time):
    stringt = str(time)
    return sum(int(x) * 60**i for i, x in enumerate(reversed(stringt.split(":"))))


# Change image size
def changeImageSize(maxWidth, maxHeight, image):
    widthRatio = maxWidth / image.size[0]
    heightRatio = maxHeight / image.size[1]
    newWidth = int(widthRatio * image.size[0])
    newHeight = int(heightRatio * image.size[1])
    return image.resize((newWidth, newHeight))


async def generate_cover(requested_by, title, views, duration, thumbnail):
    async with aiohttp.ClientSession() as session:
        async with session.get(thumbnail) as resp:
            if resp.status == 200:
                f = await aiofiles.open("background.png", mode="wb")
                await f.write(await resp.read())
                await f.close()

    image1 = Image.open("./background.png")
    image2 = Image.open("etc/foreground.png")
    image3 = changeImageSize(1280, 720, image1)
    image4 = changeImageSize(1280, 720, image2)
    image5 = image3.convert("RGBA")
    image6 = image4.convert("RGBA")
    Image.alpha_composite(image5, image6).save("temp.png")
    img = Image.open("temp.png")
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("etc/font.otf", 32)
    draw.text((190, 550), f"Title: {title}", (255, 255, 255), font=font)
    draw.text((190, 590), f"Duration: {duration}", (255, 255, 255), font=font)
    draw.text((190, 630), f"Views: {views}", (255, 255, 255), font=font)
    draw.text(
        (190, 670),
        f"Added By: {requested_by}",
        (255, 255, 255),
        font=font,
    )
    img.save("final.png")
    os.remove("temp.png")
    os.remove("background.png")


@Client.on_message(
    command(["musicplayer", f"musicplayer@{BOT_USERNAME}"])
    & ~filters.edited
    & ~filters.bot
    & ~filters.private
)
async def hfmm(_, message):
    global DISABLED_GROUPS
    if message.sender_chat:
        return await message.reply_text(
            "**⌔∮ يبدو انك مفعل وضع الاختفاء\n\n⪼ ارجع حسابك الى وضعه الطبيعي اولا"
        )
    permission = "can_delete_messages"
    m = await adminsOnly(permission, message)
    if m == 1:
        return
    try:
        user_id = message.from_user.id
    except:
        return
    if len(message.command) != 2:
        await message.reply_text("استخدم الامر هكذا؛ `!المشغل تشغيل` و `!المشغل تعطيل`")
        return
    status = message.text.split(None, 1)[1]
    message.chat.id
    if status in ["ON", "on", "تشغيل"]:
        lel = await message.reply("⪼ جار التحقق")
        if message.chat.id not in DISABLED_GROUPS:
            await lel.edit(
                f"⌔∮ مشغل الموسيقى بالفعل شغال هنا **{message.chat.title}**"
            )
            return
        DISABLED_GROUPS.remove(message.chat.id)
        await lel.edit(
            f"⌔∮ تم بنجاح تشغيل وضع المشغل هنا **{message.chat.title}**"
        )

    elif status in ["OFF", "off", "تعطيل"]:
        lel = await message.reply("جار التحقق")

        if message.chat.id in DISABLED_GROUPS:
            await lel.edit(
                f"⌔∮ وضع المشغل بالفعل لم بتم تفعيله في **{message.chat.title}**__"
            )
            return
        DISABLED_GROUPS.append(message.chat.id)
        await lel.edit(
            f"⌔∮ وضع تعطيل المشغل تم تفعيله **{message.chat.title}**__"
        )
    else:
        await message.reply_text("استخدم الامر هكذا؛ `!المشغل تشغيل` و `!المشغل تعطيل`"))


@Client.on_callback_query(filters.regex(pattern=r"^(cls)$"))
async def closed(_, query: CallbackQuery):
    from_user = query.from_user
    permissions = await member_permissions(query.message.chat.id, from_user.id)
    permission = "can_restrict_members"
    if permission not in permissions:
        return await query.answer(
            "⪼ ليست لديك صلاحيات كافية لاستخدام هذه الميزه"
            + f"⪼ الصلاحيات المطلوبة : {permission}",
            show_alert=True,
        )
    await query.message.delete()


# play
@Client.on_message(
    command(["تشغيل", f"play@{BOT_USERNAME}"])
    & filters.group
    & ~filters.edited
    & ~filters.forwarded
    & ~filters.via_bot
)
async def play(_, message: Message):
    global que
    global useer
    user_id = message.from_user.id
    if message.sender_chat:
        return await message.reply_text(
            "**⌔∮ يبدو انك مفعل وضع الاختفاء\n\n⪼ ارجع حسابك الى وضعه الطبيعي اولا"
        )

    if message.chat.id in DISABLED_GROUPS:
        await message.reply(
            "**⌔∮ وضع تشغيل معطل هنا اسئل المشرفين لتفعيله**"
        )
        return
    lel = await message.reply("**⪼ يتم التعرف انتظر قليلا**")

    chid = message.chat.id

    c = await app.get_chat_member(message.chat.id, BOT_ID)
    if c.status != "administrator":
        await lel.edit(
            f"⪼ يجب ان اكون مشرف مع بعض الصلاحيات ."
        )
        return
    if not c.can_manage_voice_chats:
        await lel.edit(
            "⪼ لا امتلك صلاحيات كافية لاستخدام هذا الامر"
            + "\n**الصلاحيات المطلوبة:** تشغيل المكالمات في الدردشة"
        )
        return
    if not c.can_delete_messages:
        await lel.edit(
            "⪼ لا امتلك صلاحيات كافية لاستخدام هذا الامر"
            + "\n**الصلاحيات المطلوبة:** حذف الرسائل"
        )
        return
    if not c.can_invite_users:
        await lel.edit(
            "⪼ لا امتلك صلاحيات كافية لاستخدام هذا الامر"
            + "\n**الصلاحيات المطلوبة:** دعوة المستخدم بواسطه الرابط"
        )
        return
    if not c.can_restrict_members:
        await lel.edit(
            "⪼ لا امتلك صلاحيات كافية لاستخدام هذا الامر"
            + "\n**الصلاحيات المطلوبة:** حظر المستخدمين"
        )
        return

    try:
        b = await app.get_chat_member(message.chat.id, ASSID)
        if b.status == "kicked":
            await message.reply_text(
                f"⪼ {ASSNAME} (@{ASSUSERNAME}) هو محظور في هذه المجموعه **{message.chat.title}**\n\n ◂  يجب عليك الغاء حظره اولا لاستخدامه هنا"
            )
            return
    except UserNotParticipant:
        if message.chat.username:
            try:
                await ASS_ACC.join_chat(f"{message.chat.username}")
                await message.reply(
                    f"**⌔∮ الحساب المساعد {ASSNAME} تم الانضمام بنجاح**",
                )
                await remove_active_chat(chat_id)
            except Exception as e:
                await message.reply_text(
                    f"⪼ **فشل الحساب المساعد في الانضمام\n\n**السبب**:{e}"
                )
                return
        else:
            try:
                invite_link = await message.chat.export_invite_link()
                if "+" in invite_link:
                    kontol = (invite_link.replace("+", "")).split("t.me/")[1]
                    link_bokep = f"https://t.me/joinchat/{kontol}"
                await ASS_ACC.join_chat(link_bokep)
                await message.reply(
                    f"**⌔∮ الحساب المساعد {ASSNAME} تم الانضمام بنجاح**",
                )
                await remove_active_chat(message.chat.id)
            except UserAlreadyParticipant:
                pass
            except Exception as e:
                return await message.reply_text(
                    f"⪼ **فشل الحساب المساعد في الانضمام\n\n**السبب**:{e}"
                )

    await message.delete()
    audio = (
        (message.reply_to_message.audio or message.reply_to_message.voice)
        if message.reply_to_message
        else None
    )
    url = get_url(message)

    if audio:
        if round(audio.duration / 60) > DURATION_LIMIT:
            raise DurationLimitError(
                f"⪼ يبدو ان الفيديو اكبر من {DURATION_LIMIT} دقيقة لا يمكنك تشغيله هنا"
            )

        file_name = get_file_name(audio)
        url = f"https://t.me/jmthon"
        title = audio.title
        thumb_name = "https://telegra.ph/file/a7adee6cf365d74734c5d.png"
        thumbnail = thumb_name
        duration = round(audio.duration / 60)
        views = "Locally added"

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🚨 الدعم", url=f"t.me/jmthon_support"),
                    InlineKeyboardButton("📡 التحديثات", url=f"t.me/jmthon "),
                ],
                [InlineKeyboardButton(text="🗑 اغلاق", callback_data="cls")],
            ]
        )

        requested_by = message.from_user.first_name
        await generate_cover(requested_by, title, views, duration, thumbnail)
        file_path = await jmthon.tgcalls.convert(
            (await message.reply_to_message.download(file_name))
            if not path.isfile(path.join("downloads", file_name))
            else file_name
        )

    elif url:
        try:
            results = YoutubeSearch(url, max_results=1).to_dict()
            # print results
            title = results[0]["title"]
            thumbnail = results[0]["thumbnails"][0]
            thumb_name = f"thumb{title}.jpg"
            thumb = requests.get(thumbnail, allow_redirects=True)
            open(thumb_name, "wb").write(thumb.content)
            duration = results[0]["duration"]
            url_suffix = results[0]["url_suffix"]
            views = results[0]["views"]
            durl = url
            durl = durl.replace("youtube", "youtubepp")

            secmul, dur, dur_arr = 1, 0, duration.split(":")
            for i in range(len(dur_arr) - 1, -1, -1):
                dur += int(dur_arr[i]) * secmul
                secmul *= 60

            keyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("🚨 الدعم", url=f"t.me/jmthon_support"),
                        InlineKeyboardButton("📡 التحديثات", url=f"t.me/jmthon"),
                    ],
                    [InlineKeyboardButton(text="🗑 اغلاق", callback_data="cls")],
                ]
            )

        except Exception as e:
            title = "غير معرف"
            thumb_name = "https://telegra.ph/file/a7adee6cf365d74734c5d.png"
            duration = "غير معروف"
            views = "غير معروف"
            keyboard = InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="اليوتيوب 🎬", url="https://youtube.com")]]
            )

        if (dur / 60) > DURATION_LIMIT:
            await lel.edit(
                f"⪼ يبدو ان الفيديو اكبر من {DURATION_LIMIT} دقيقة لا يمكنك تشغيله هنا"
            )
            return
        requested_by = message.from_user.first_name
        await generate_cover(requested_by, title, views, duration, thumbnail)

        def my_hook(d):
            if d["status"] == "downloading":
                percentage = d["_percent_str"]
                per = (str(percentage)).replace(".", "", 1).replace("%", "", 1)
                per = int(per)
                eta = d["eta"]
                speed = d["_speed_str"]
                size = d["_total_bytes_str"]
                bytesx = d["total_bytes"]
                if str(bytesx) in flex:
                    pass
                else:
                    flex[str(bytesx)] = 1
                if flex[str(bytesx)] == 1:
                    flex[str(bytesx)] += 1
                    try:
                        if eta > 2:
                            lel.edit(
                                f"⪼ جار تحميل {title[:50]}\n\n**حجم الملف:** {size}\n**نسبه التنزيل:** {percentage}\n**السرعة:** {speed}\n**الوقت المستغرق:** {eta} ثانية"
                            )
                    except Exception as e:
                        pass
                if per > 250:
                    if flex[str(bytesx)] == 2:
                        flex[str(bytesx)] += 1
                        if eta > 2:
                            lel.edit(
                                f"**⪼ جار تحميل** {title[:50]}..\n\n**حجم الملف:** {size}\n**نسبه التنزيل:** {percentage}\n**السرعة:** {speed}\n**الوقت المستغرق:** {eta} ثانية"
                            )
                        print(
                            f"[{url_suffix}] نسبه التنزيل {percentage} بسرعه {speed} | : {eta} ثانية"
                        )
                if per > 500:
                    if flex[str(bytesx)] == 3:
                        flex[str(bytesx)] += 1
                        if eta > 2:
                            lel.edit(
                                f"**⪼ جار تحميل** {title[:50]}...\n\n**حجم الملف:** {size}\n**نسبه التنزيل:** {percentage}\n**السرعة:** {speed}\n**الوقت المستغرق:** {eta} ثانية"
                            )
                        print(
                            f"[{url_suffix}] نسبه التنزيل {percentage} بسرعه {speed} | ETA: {eta} ثانية"
                        )
                if per > 800:
                    if flex[str(bytesx)] == 4:
                        flex[str(bytesx)] += 1
                        if eta > 2:
                            lel.edit(
                                f"**⪼ جار تحميل** {title[:50]}....\n\n**حجم الملف:** {size}\n**نسبه التنزيل:** {percentage}\n**السرعة:** {speed}\n**الوقت المستغرق:** {eta} sec"
                            )
                        print(
                            f"[{url_suffix}] نسبه التنزيل {percentage} بسرعة {speed} | ETA: {eta} ثانية"
                        )
            if d["status"] == "finished":
                try:
                    taken = d["_elapsed_str"]
                except Exception as e:
                    taken = "00:00"
                size = d["_total_bytes_str"]
                lel.edit(
                    f"**جار تحميل** {title[:50]}.....\n\n**حجم الملف:** {size}\n**الوقت المستغرق:** {taken} ثانية"
                )
                print(f"[{url_suffix}] نسبه التنزيل|: {taken} ثانية")

        loop = asyncio.get_event_loop()
        x = await loop.run_in_executor(None, youtube.download, url, my_hook)
        file_path = await jmthon.tgcalls.convert(x)
    else:
        if len(message.command) < 2:
            return await lel.edit(
                "**⌔∮ لم بتم العثور على العنوان يرجى التاكد من عنوان صحيح \nمثال  ◂  !تشغيل In The End\n\nالتحديثات : @jmthon**"
            )
        await lel.edit("** تم العثور على المطلوب 🔎 **")
        query = message.text.split(None, 1)[1]
        # print(query)
        await lel.edit("**يتم التعرف غلى الصوت 🎵 **")
        try:
            results = YoutubeSearch(query, max_results=5).to_dict()
            url = f"https://youtube.com{results[0]['url_suffix']}"
            # print results
            title = results[0]["title"]
            thumbnail = results[0]["thumbnails"][0]
            thumb_name = f"thumb{title}.jpg"
            thumb = requests.get(thumbnail, allow_redirects=True)
            open(thumb_name, "wb").write(thumb.content)
            duration = results[0]["duration"]
            url_suffix = results[0]["url_suffix"]
            views = results[0]["views"]
            durl = url
            durl = durl.replace("youtube", "youtubepp")

            secmul, dur, dur_arr = 1, 0, duration.split(":")
            for i in range(len(dur_arr) - 1, -1, -1):
                dur += int(dur_arr[i]) * secmul
                secmul *= 60

        except Exception as e:
            await lel.edit(
                "⪼ لم يتم العثور على المطلوب\n\nحاول بعنوان ثاني او استخدم امر `!تشغيل [رابط يوتيوب]`."
            )
            print(str(e))
            return

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🚨 الدعم", url=f"t.me/jmthon_support"),
                    InlineKeyboardButton("📡 التحديثات", url=f"t.me/jmthon "),
                ],
                [InlineKeyboardButton(text="🗑 اغلاق", callback_data="cls")],
            ]
        )

        if (dur / 60) > DURATION_LIMIT:
            await lel.edit(
                f"⪼ يبدو ان الفيديو اكبر من {DURATION_LIMIT} دقيقة لا يمكنك تشغيله هنا"
            )
            return
        requested_by = message.from_user.first_name
        await generate_cover(requested_by, title, views, duration, thumbnail)

        def my_hook(d):
            if d["status"] == "downloading":
                percentage = d["_percent_str"]
                per = (str(percentage)).replace(".", "", 1).replace("%", "", 1)
                per = int(per)
                eta = d["eta"]
                speed = d["_speed_str"]
                size = d["_total_bytes_str"]
                bytesx = d["total_bytes"]
                if str(bytesx) in flex:
                    pass
                else:
                    flex[str(bytesx)] = 1
                if flex[str(bytesx)] == 1:
                    flex[str(bytesx)] += 1
                    try:
                        if eta > 2:
                            lel.edit(
                                f"جار تحميل {title[:50]}\n\n**حجم الملف:** {size}\n**نسبه التنزيل:** {percentage}\n**السرعة:** {speed}\n**الوقت المستغرق:** {eta} ثانية"
                            )
                    except Exception as e:
                        pass
                if per > 250:
                    if flex[str(bytesx)] == 2:
                        flex[str(bytesx)] += 1
                        if eta > 2:
                            lel.edit(
                                f"**جار تحميل** {title[:50]}..\n\n**حجم الملف:** {size}\n**نسبه التنزيل:** {percentage}\n**السرعة:** {speed}\n**الوقت المستغرق:** {eta} ثانية"
                            )
                        print(
                            f"[{url_suffix}] نسبه التنزيل {percentage} at a speed of {speed} | ETA: {eta} "
                        )
                if per > 500:
                    if flex[str(bytesx)] == 3:
                        flex[str(bytesx)] += 1
                        if eta > 2:
                            lel.edit(
                                f"**جار تحميل** {title[:50]}...\n\n**حجم الملف:** {size}\n**نسبه التنزيل:** {percentage}\n**السرعة:** {speed}\n**الوقت المستغرق:** {eta} ثانية"
                            )
                        print(
                            f"[{url_suffix}] نسبه التنزيل {percentage} at a speed of {speed} | ETA: {eta} ثانيةonds"
                        )
                if per > 800:
                    if flex[str(bytesx)] == 4:
                        flex[str(bytesx)] += 1
                        if eta > 2:
                            lel.edit(
                                f"**Downloading** {title[:50]}....\n\n**حجم الملف:** {size}\n**نسبه التنزيل:** {percentage}\n**السرعة:** {speed}\n**الوقت المستغرق:** {eta} ثانية"
                            )
                        print(
                            f"[{url_suffix}] نسبه التنزيل {percentage} at a speed of {speed} | ETA: {eta} ثانيةonds"
                        )
            if d["status"] == "finished":
                try:
                    taken = d["_elapsed_str"]
                except Exception as e:
                    taken = "00:00"
                size = d["_total_bytes_str"]
                lel.edit(
                    f"**تن التنزيل** {title[:50]}.....\n\n**حجم الملف:** {size}\n**الوقت المستغرق:** {taken} ثانية"
                )
                print(f"[{url_suffix}] تم تنزيله | انتهى: {taken} ثواني")

        loop = asyncio.get_event_loop()
        x = await loop.run_in_executor(None, youtube.download, url, my_hook)
        file_path = await jmthon.tgcalls.convert(x)

    if await is_active_chat(message.chat.id):
        position = await queues.put(message.chat.id, file=file_path)
        await message.reply_photo(
            photo="final.png",
            caption="**🎵 العنوان:** [{}]({})\n**🕒 المدة:** {} دقيقه\n**👤 تن الاضافه بواسطه :** {}\n\n**#⃣ قائمة الانتظار:** {}".format(
                title,
                url,
                duration,
                message.from_user.mention(),
                position,
            ),
            reply_markup=keyboard,
        )
    else:
        try:
            await calls.pytgcalls.join_group_call(
                message.chat.id,
                InputStream(
                    InputAudioStream(
                        file_path,
                    ),
                ),
                stream_type=StreamType().local_stream,
            )
        except Exception:
            return await lel.edit(
                "⌔∮ لا يمكنني الدخول للمكالمه الصوتية تأكد من ان المكالمه شغالة هنا"
            )

        await music_on(message.chat.id)
        await add_active_chat(message.chat.id)
        await message.reply_photo(
            photo="final.png",
            reply_markup=keyboard,
            caption="**🎵 العنوان:** [{}]({})\n**🕒 المدة:** {} دقيقي\n**👤 تم الاضافه بواسطه:** {}\n\n**▶️ الشغال الان هو `{}`...**".format(
                title, url, duration, message.from_user.mention(), message.chat.title
            ),
        )

    os.remove("final.png")
    return await lel.delete()
