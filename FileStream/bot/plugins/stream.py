
import asyncio
from FileStream.bot import FileStream, multi_clients
from FileStream.utils.bot_utils import is_user_banned, is_user_exist, is_user_joined, gen_link, is_channel_banned, is_channel_exist, is_user_authorized
from FileStream.utils.database import Database
from FileStream.utils.file_properties import get_file_ids, get_file_info
from FileStream.config import Telegram
from pyrogram import filters, Client
from pyrogram.errors import FloodWait
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.enums.parse_mode import ParseMode
db = Database(Telegram.DATABASE_URL, Telegram.SESSION_NAME)


import base64
import logging
import math
import requests

import xml.etree.ElementTree as ET
import random
from struct import pack
import re

from pymongo import MongoClient
from pyrogram.errors import MessageNotModified
from umongo import Instance, Document, fields


from pyrogram.file_id import FileId

from info import officialchatid, bot_username, updatechannel, logDataChannel, DB01_MB, botid, DB02_MB, MUVI_Bots, \
    Muvi_requested_Files


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Initialize the app with a service account, granting admin privileges
# MongoDB information
DATABASE_URI = "mongodb+srv://test:test05@cluster0.g05zxpa.mongodb.net/?retryWrites=true&w=majority"
DATABASE_NAME = "Cluster0"
COLLECTION_NAME = 'MovieBoxDATA'

client = MongoClient(DATABASE_URI)
dbss = client[DATABASE_NAME]
instance = Instance.from_db(dbss)
BUTTONS = {}
ss = ""
botno= f"https://t.me/"

# url=f"http://t.me/{temp.U_NAME}?startgroup=true"
# url=f"https://t.me/movieboxtv_bot?start=sendfile_{msgid}_{chatid}_{user_id}_{group_id}_no"
@instance.register
class Media(Document):
    file_id = fields.StrField(attribute='_id')
    file_ref = fields.StrField(allow_none=True)
    file_name = fields.StrField(required=True)
    file_size = fields.IntField(required=True)
    file_msg_id = fields.IntField(allow_none=True)
    file_channel_id = fields.IntField(allow_none=True)
    caption = fields.StrField(allow_none=True)

    class Meta:
        collection_name = COLLECTION_NAME


@instance.register
class GMedia(Document):
    _id = fields.IntField(attribute='_id')
    group_id = fields.StrField(allow_none=True)
    group_name = fields.StrField(allow_none=True)
    group_members = fields.IntField(allow_none=True)
    groupusername = fields.StrField(allow_none=True)
    group_owner_id = fields.IntField(allow_none=True)
    group_owner_name = fields.StrField(allow_none=True)
    group_owner_earn = fields.IntField(allow_none=True)

    class Meta:
        collection_name = "newGroups_2in1"

async def get_search_results(query, file_type=None, max_results=(10), offset=0, filter=False):
    query = query.strip()
    if not query:
        raw_pattern = '.'
    elif ' ' not in query:
        raw_pattern = r'(\b|[\.\+\-_])' + query + r'(\b|[\.\+\-_])'
    else:
        raw_pattern = query.replace(' ', r'.*[\s\.\+\-_]')
    try:
        regex = re.compile(raw_pattern, flags=re.IGNORECASE)
    except:
        return [], '', 0
    filter = {'file_name': regex}
    if file_type: filter['file_type'] = file_type

    total_results = Media.count_documents(filter)
    logging.info(total_results)
    next_offset = offset + max_results
    if next_offset > total_results: next_offset = ''

    cursor = Media.find(filter)
    # Sort by recent
    cursor.sort('$natural', -1)
    # Slice files according to offset and max results
    cursor.skip(offset).limit(max_results)
    # Get list of files
    # files = cursor.to_list(length=max_results)
    # return files, next_offset, total_results
    # Get list of files
    files = list(cursor)  # Convert the cursor to a list
    return files, next_offset, total_results


async def get_file_details(query):
    filter = {'file_id': query}
    cursor = Media.find(filter)
    # filedetails = cursor.to_list(length=1)
    filedetails = list(cursor)  # Convert the cursor to a list
    return filedetails


async def get_size(size):
    """Get size in readable format"""

    units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units):
        i += 1
        size /= 1024.0

    return "%.0f %s" % (size, units[i])


async def encode_file_id(s: bytes) -> str:
    r = b""
    n = 0

    for i in s + bytes([22]) + bytes([4]):
        if i == 0:
            n += 1
        else:
            if n:
                r += b"\x00" + bytes([n])
                n = 0

            r += bytes([i])

    return base64.urlsafe_b64encode(r).decode().rstrip("=")


async def encode_file_ref(file_ref: bytes) -> str:
    return base64.urlsafe_b64encode(file_ref).decode().rstrip("=")


async def unpack_new_file_id(new_file_id):
    """Return file_id, file_ref"""
    decoded = FileId.decode(new_file_id)
    file_id = encode_file_id(
        pack(
            "<iiqq",
            int(decoded.file_type),
            decoded.dc_id,
            decoded.media_id,
            decoded.access_hash
        )
    )
    file_ref = encode_file_ref(decoded.file_reference)
    return file_id, file_ref


async def modify_filename(filename):
    # Perform your modifications to the filename here
    # For example, let's add a prefix "Modified_" to the filename
    name = filename
    clean_text = re.sub(r'^\[.*?\]|@\w+\b', '', name).strip()
    words = clean_text.split()
    if len(words) <= 5:
        clean_text = name.replace("@", "")
        clean_text = re.sub(r'^\[.*?\]', '', clean_text).strip()
    clean_text = re.sub(r"(_|\-|\.|\+)", " ", clean_text)
    file_name = re.sub(r'\s+', ' ', clean_text).strip()

    collection = dbss["replaceword"]
    all_documents = collection.find({})

    for document in all_documents:
        x = document["_id"]
        if x in file_name:
            clean_text = file_name.replace(x, "")
        if clean_text == "":
            file_name = file_name
        else:
            file_name = clean_text

    # query = re.sub(r'\s+', ' ', clean_text).strip()
    # print(query)
    return file_name


async def convert_to_embed_url(original_url):
    # Check if it's a valid Terabox URL
    if "tera" in original_url:
        # Extract the unique identifier (surl) part
        surl = original_url.split("/s/")[1]

        # Remove leading "1" along with any connected special characters (e.g., _, -, etc.)
        cleaned_surl = re.sub(r"^1[\W_]*", "", surl)

        # Construct the embed URL
        embed_url = f"https://www.1024terabox.com/sharing/embed?surl={cleaned_surl}"
        return cleaned_surl
    else:
        return "Invalid Terabox URL"


# Example original URL
async def get_first_tera_url(text):
    # Regular expression to find URLs with "tera" in them
    url_pattern = r"https?://\S*tera\S*"

    # Find all matches in the text
    matches = re.findall(url_pattern, text)

    # Return the first match if found, otherwise return None
    return matches[0] if matches else None

@FileStream.on_message(filters.text & filters.incoming)
async def search(client, message):
    global ss
    ss = message.text
    chat_id = message.chat.id
    user_id = message.from_user.id
    username = f"@{message.from_user.username}" if message.from_user.username else "notFound"
    group_id = message.chat.id

    logging.info(f"Received query: {ss}")

    # Handling "tera" in the query
    if "tera" in ss:
        print("tera here")
    # Handling general search queries
    else:
        m = await message.reply_text(
            text=f"Searching.. {ss}\nPlease Wait.. {username}\n\nSend me Terabox Link and Direct Play Here, No Ads"
        )
        files, offset, total_results = await get_search_results(ss)

        if not files:
            print("not found any file")
            return


        btn = [
            [
                InlineKeyboardButton(
                    text=f"[{await get_size(file.file_size)}]💠{await modify_filename(file.file_name)}",
                    url=f'{botno}sendfile_{file.file_msg_id}_{file.file_channel_id}_{user_id}_{group_id}'
                )
            ]
            for file in files
        ]

        if offset:
            key = f"{message.chat.id}-{message.id}"
            BUTTONS[key] = search
            btn.append([
                InlineKeyboardButton(text=f"🗓 1/{math.ceil(int(total_results) / 10)}", callback_data="pages"),
                InlineKeyboardButton(text="Next ›››", callback_data=f"next_{user_id}_{key}_{offset}_{user_id}_{group_id}")
            ])
        else:
            btn.append([InlineKeyboardButton(text="🗓 No More Results", callback_data="pages")])

        reply_markup = InlineKeyboardMarkup(btn)
     
        await message.reply_text(
            f"We Found Your Query 🎞️ <b>{ss}</b>\n\nTotal Files: {total_results}\n\n©️ <a href='https://t.me/{client.me.username}'>{client.me.first_name}</a>",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML
        )
       
    
"""
@FileStream.on_message(
    filters.private
    & (
            filters.document
            | filters.video
            | filters.video_note
            | filters.audio
            | filters.voice
            | filters.animation
            | filters.photo
    ),
    group=4,
)
async def private_receive_handler(bot: Client, message: Message):
    if not await is_user_authorized(message):
        return
    if await is_user_banned(message):
        return

    await is_user_exist(bot, message)
    if Telegram.FORCE_SUB:
        if not await is_user_joined(bot, message):
            return
    try:

        try:
            
           i = await bot.get_messages(chat_id=-1002059529731, message_ids=33554)
           inserted_id = await db.add_file(get_file_info(i))
           await get_file_ids(False, inserted_id, multi_clients, message)
           reply_markup, stream_text = await gen_link(_id=inserted_id)
           await message.reply_text(
            text=stream_text,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            quote=True
           )
        except Exception as e:
            await message.reply_text(
                 text={e}
            )
            print("error getting message {e}")
        
        inserted_id = await db.add_file(get_file_info(message))
        await get_file_ids(False, inserted_id, multi_clients, message)
        reply_markup, stream_text = await gen_link(_id=inserted_id)
        await message.reply_text(
            text=stream_text,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            quote=True
        )
        
    except FloodWait as e:
        print(f"Sleeping for {str(e.value)}s")
        await asyncio.sleep(e.value)
        await bot.send_message(chat_id=Telegram.ULOG_CHANNEL,
                               text=f"Gᴏᴛ FʟᴏᴏᴅWᴀɪᴛ ᴏғ {str(e.value)}s ғʀᴏᴍ [{message.from_user.first_name}](tg://user?id={message.from_user.id})\n\n**ᴜsᴇʀ ɪᴅ :** `{str(message.from_user.id)}`",
                               disable_web_page_preview=True, parse_mode=ParseMode.MARKDOWN)

"""

@FileStream.on_message(
    filters.channel
    & ~filters.forwarded
    & ~filters.media_group
    & (
            filters.document
            | filters.video
            | filters.video_note
            | filters.audio
            | filters.voice
            | filters.photo
    )
)
async def channel_receive_handler(bot: Client, message: Message):
    if await is_channel_banned(bot, message):
        return
    await is_channel_exist(bot, message)

    try:
        inserted_id = await db.add_file(get_file_info(message))
        await get_file_ids(False, inserted_id, multi_clients, message)
        reply_markup, stream_link = await gen_link(_id=inserted_id)
        await bot.edit_message_reply_markup(
            chat_id=message.chat.id,
            message_id=message.id,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Dᴏᴡɴʟᴏᴀᴅ ʟɪɴᴋ 📥",
                                       url=f"https://t.me/{FileStream.username}?start=stream_{str(inserted_id)}")]])
        )

    except FloodWait as w:
        print(f"Sleeping for {str(w.x)}s")
        await asyncio.sleep(w.x)
        await bot.send_message(chat_id=Telegram.ULOG_CHANNEL,
                               text=f"ɢᴏᴛ ғʟᴏᴏᴅᴡᴀɪᴛ ᴏғ {str(w.x)}s ғʀᴏᴍ {message.chat.title}\n\n**ᴄʜᴀɴɴᴇʟ ɪᴅ :** `{str(message.chat.id)}`",
                               disable_web_page_preview=True)
    except Exception as e:
        await bot.send_message(chat_id=Telegram.ULOG_CHANNEL, text=f"**#EʀʀᴏʀTʀᴀᴄᴋᴇʙᴀᴄᴋ:** `{e}`",
                               disable_web_page_preview=True)
        print(f"Cᴀɴ'ᴛ Eᴅɪᴛ Bʀᴏᴀᴅᴄᴀsᴛ Mᴇssᴀɢᴇ!\nEʀʀᴏʀ:  **Gɪᴠᴇ ᴍᴇ ᴇᴅɪᴛ ᴘᴇʀᴍɪssɪᴏɴ ɪɴ ᴜᴘᴅᴀᴛᴇs ᴀɴᴅ ʙɪɴ Cʜᴀɴɴᴇʟ!{e}**")

