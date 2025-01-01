
import asyncio
from FileStream.bot import FileStream, multi_clients
from FileStream.utils.bot_utils import is_user_banned, is_user_exist, is_user_joined, gen_link, is_channel_banned, is_channel_exist, is_user_authorized
from FileStream.utils.database import Database
from FileStream.utils.file_properties import get_file_ids, get_file_info
from FileStream.config import Telegram
from pyrogram import filters, Client
from pyrogram.errors import FloodWait
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
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
import datetime
import math
from FileStream import __version__
from FileStream.bot import FileStream
from FileStream.config import Telegram, Server
from FileStream.utils.translation import LANG, BUTTON
from FileStream.utils.bot_utils import gen_link
from FileStream.utils.database import Database
from FileStream.utils.human_readable import humanbytes
from FileStream.server.exceptions import FIleNotFound
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram.file_id import FileId, FileType, PHOTO_TYPES
from pyrogram.enums.parse_mode import ParseMode
import logging
from database import Media, get_file_details, get_search_results

db = Database(Telegram.DATABASE_URL, Telegram.SESSION_NAME)
botno= f"https://t.me/"
BUTTONS = {}
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

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

#---------------------[ START CMD ]---------------------#



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


@FileStream.on_message(filters.command('start') & filters.private)
async def start(bot: Client, message: Message):
    logging.error("h here")
    
    usr_cmd = message.text.split("_")[-1]

    if usr_cmd == "/start":
        if Telegram.START_PIC:
            await message.reply_photo(
                photo=Telegram.START_PIC,
                caption=LANG.START_TEXT.format(message.from_user.mention, FileStream.username),
                parse_mode=ParseMode.HTML,
                reply_markup=BUTTON.START_BUTTONS
            )
        else:
            await message.reply_text(
                text=LANG.START_TEXT.format(message.from_user.mention, FileStream.username),
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
                reply_markup=BUTTON.START_BUTTONS
            )
    else:
        
        if "stream_" in message.text:
            try:
                file_check = await db.get_file(usr_cmd)
                file_id = str(file_check['_id'])
                if file_id == usr_cmd:
                    reply_markup, stream_text = await gen_linkx(m=message, _id=file_id,
                                                                name=[FileStream.username, FileStream.fname])
                    await message.reply_text(
                        text=stream_text,
                        parse_mode=ParseMode.HTML,
                        disable_web_page_preview=True,
                        reply_markup=reply_markup,
                        quote=True
                    )

            except FIleNotFound as e:
                await message.reply_text("File Not Found")
            except Exception as e:
                await message.reply_text("Something Went Wrong")
                logging.error(e)

        elif "streamnew_" in message.text:
            try:
                logging.error("streamnew here")
                print("hello")
                usr_cmd = message.text.split("_")
                req, mid, cid, user_id, group_id = usr_cmd
                logging.error(f"mid: {mid}, cid: {cid}")
                try:
                    i = await bot.get_messages(cid,mid)
                    logging.error("yhan aaya here")
                    logging.error(i)
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
                    logging.error(f"get file error: {e}")
                    await message.reply_text(
                        text={e}
                    )


            except Exception as e:
               logging.error(f"Outer error: {e}")
               await message.reply_text(f"An unexpected error occurred: {str(e)}")


        elif "file_" in message.text:
            try:
                file_check = await db.get_file(usr_cmd)
                db_id = str(file_check['_id'])
                file_id = file_check['file_id']
                file_name = file_check['file_name']
                if db_id == usr_cmd:
                    filex = await message.reply_cached_media(file_id=file_id, caption=f'**{file_name}**')
                    await asyncio.sleep(3600)
                    try:
                        await filex.delete()
                        await message.delete()
                    except Exception:
                        pass

            except FIleNotFound as e:
                await message.reply_text("**File Not Found**")
            except Exception as e:
                await message.reply_text("Something Went Wrong")
                logging.error(e)

        else:
            await message.reply_text(f"**Invalid Command**")

@FileStream.on_message(filters.private & filters.command(["about"]))
async def start(bot, message):
    if not await verify_user(bot, message):
        return
    if Telegram.START_PIC:
        await message.reply_photo(
            photo=Telegram.START_PIC,
            caption=LANG.ABOUT_TEXT.format(FileStream.fname, __version__),
            parse_mode=ParseMode.HTML,
            reply_markup=BUTTON.ABOUT_BUTTONS
        )
    else:
        await message.reply_text(
            text=LANG.ABOUT_TEXT.format(FileStream.fname, __version__),
            disable_web_page_preview=True,
            reply_markup=BUTTON.ABOUT_BUTTONS
        )

@FileStream.on_message((filters.command('help')) & filters.private)
async def help_handler(bot, message):
    if not await verify_user(bot, message):
        return
    if Telegram.START_PIC:
        await message.reply_photo(
            photo=Telegram.START_PIC,
            caption=LANG.HELP_TEXT.format(Telegram.OWNER_ID),
            parse_mode=ParseMode.HTML,
            reply_markup=BUTTON.HELP_BUTTONS
        )
    else:
        await message.reply_text(
            text=LANG.HELP_TEXT.format(Telegram.OWNER_ID),
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=BUTTON.HELP_BUTTONS
        )

# ---------------------------------------------------------------------------------------------------

@FileStream.on_message(filters.command('files') & filters.private)
async def my_files(bot: Client, message: Message):
    if not await verify_user(bot, message):
        return
    user_files, total_files = await db.find_files(message.from_user.id, [1, 10])

    file_list = []
    async for x in user_files:
        file_list.append([InlineKeyboardButton(x["file_name"], callback_data=f"myfile_{x['_id']}_{1}")])
    if total_files > 10:
        file_list.append(
            [
                InlineKeyboardButton("◄", callback_data="N/A"),
                InlineKeyboardButton(f"1/{math.ceil(total_files / 10)}", callback_data="N/A"),
                InlineKeyboardButton("►", callback_data="userfiles_2")
            ],
        )
    if not file_list:
        file_list.append(
            [InlineKeyboardButton("ᴇᴍᴘᴛʏ", callback_data="N/A")],
        )
    file_list.append([InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")])
    await message.reply_photo(photo=Telegram.FILE_PIC,
                              caption="Total files: {}".format(total_files),
                              reply_markup=InlineKeyboardMarkup(file_list))




@FileStream.on_message(filters.text & filters.incoming )
async def search(client, message):
    if message.text.startswith("/"):
        logging.error(message)
        return  # Ignore commands
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
                    url=f"https://t.me/{FileStream.username}?start=streamnew_{file.file_msg_id}_{file.file_channel_id}_{user_id}_{group_id}"
                   
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


@FileStream.on_callback_query()
async def cb_data(bot, update: CallbackQuery):
    usr_cmd = update.data.split("_")
    logging.info("caback")
    logging.info(usr_cmd)
    print("calback")
    print(usr_cmd)
   
    # Handle pagination logic when the callback starts with "next_"
    if usr_cmd[0] == "next":
        if len(usr_cmd) < 6:
            await update.answer("Invalid callback data.", show_alert=True)
            return

        # Extract callback data
        ident, req, key, offset, user_id, group_id = usr_cmd

        if int(req) not in [update.from_user.id, 0]:
            await update.answer(f"This is not your result. Please search your own.\n{req}", show_alert=True)
            return

        try:
            offset = int(offset)
        except ValueError:
            offset = 0

        # Retrieve search function or data
        search = BUTTONS.get(key)
    
        # Fetch the search results for the next page
        files, n_offset, total = await get_search_results(ss, offset=offset, filter=True)
        try:
            n_offset = int(n_offset)
        except ValueError:
            n_offset = 0

        if not files:
            await update.answer("No more files found.")
            return

        # Generate buttons for the search results
        btn = [
            [
                InlineKeyboardButton(
                    text=f"[{await get_size(file.file_size)}]💠{await modify_filename(file.file_name)}",
                    url=f'{botno}sendfile_{file.file_msg_id}_{file.file_channel_id}_{user_id}_{group_id}'
                )
            ]
            for file in files
        ]

        # Pagination buttons
        if 0 < offset <= 10:
            prev_offset = 0
        elif offset == 0:
            prev_offset = None
        else:
            prev_offset = offset - 10

        if n_offset == 0:
            btn.append([
                InlineKeyboardButton("ᴘᴀɢᴇs", callback_data="pages"),
                InlineKeyboardButton(f"{round(offset / 10) + 1} / {round(total / 10)}", callback_data="pages"),
                InlineKeyboardButton("‹ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{prev_offset}_{user_id}_{group_id}")
            ])
        elif prev_offset is None:
            btn.append([
                InlineKeyboardButton("ᴘᴀɢᴇs", callback_data="pages"),
                InlineKeyboardButton(f"{round(offset / 10) + 1} / {round(total / 10)}", callback_data="pages"),
                InlineKeyboardButton("ɴᴇxᴛ ›", callback_data=f"next_{req}_{key}_{n_offset}_{user_id}_{group_id}")
            ])
        else:
            btn.append([
                InlineKeyboardButton("‹ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{prev_offset}_{user_id}_{group_id}"),
                InlineKeyboardButton(f"{round(offset / 10) + 1} / {round(total / 10)}", callback_data="pages"),
                InlineKeyboardButton("ɴᴇxᴛ ›", callback_data=f"next_{req}_{key}_{n_offset}_{user_id}_{group_id}")
            ])

        reply_markup = InlineKeyboardMarkup(btn)

        # Update the message with new pagination buttons
        try:
            await update.message.edit_reply_markup(
                reply_markup=reply_markup
            )
        except MessageNotModified:
            await update.answer("Nothing changed in this message.")

   
    # Handle pagination logic when the callback starts with "next_"
    elif usr_cmd[0] == "help":
        await update.message.edit_text(
            text=LANG.HELP_TEXT.format(Telegram.OWNER_ID),
            disable_web_page_preview=True,
            reply_markup=BUTTON.HELP_BUTTONS
        )
    elif usr_cmd[0] == "about":
        await update.message.edit_text(
            text=LANG.ABOUT_TEXT.format(FileStream.fname, __version__),
            disable_web_page_preview=True,
            reply_markup=BUTTON.ABOUT_BUTTONS
        )

    #---------------------[ MY FILES CMD ]---------------------#

    elif usr_cmd[0] == "N/A":
        await update.answer("N/A", True)
    elif usr_cmd[0] == "close":
        await update.message.delete()
    elif usr_cmd[0] == "msgdelete":
        await update.message.edit_caption(
        caption= "**Cᴏɴғɪʀᴍ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴅᴇʟᴇᴛᴇ ᴛʜᴇ Fɪʟᴇ**\n\n",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ʏᴇs", callback_data=f"msgdelyes_{usr_cmd[1]}_{usr_cmd[2]}"), InlineKeyboardButton("ɴᴏ", callback_data=f"myfile_{usr_cmd[1]}_{usr_cmd[2]}")]])
    )
    elif usr_cmd[0] == "msgdelyes":
        await delete_user_file(usr_cmd[1], int(usr_cmd[2]), update)
        return
    elif usr_cmd[0] == "msgdelpvt":
        await update.message.edit_caption(
        caption= "**Cᴏɴғɪʀᴍ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴅᴇʟᴇᴛᴇ ᴛʜᴇ Fɪʟᴇ**\n\n",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ʏᴇs", callback_data=f"msgdelpvtyes_{usr_cmd[1]}"), InlineKeyboardButton("ɴᴏ", callback_data=f"mainstream_{usr_cmd[1]}")]])
    )
    elif usr_cmd[0] == "msgdelpvtyes":
        await delete_user_filex(usr_cmd[1], update)
        return

    elif usr_cmd[0] == "mainstream":
        _id = usr_cmd[1]
        reply_markup, stream_text = await gen_link(_id=_id)
        await update.message.edit_text(
            text=stream_text,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
        )

    elif usr_cmd[0] == "userfiles":
        file_list, total_files = await gen_file_list_button(int(usr_cmd[1]), update.from_user.id)
        await update.message.edit_caption(
            caption="Total files: {}".format(total_files),
            reply_markup=InlineKeyboardMarkup(file_list)
            )
    elif usr_cmd[0] == "myfile":
        await gen_file_menu(usr_cmd[1], usr_cmd[2], update)
        return
    elif usr_cmd[0] == "sendfile":
        myfile = await db.get_file(usr_cmd[1])
        file_name = myfile['file_name']
        await update.answer(f"Sending File {file_name}")
        await update.message.reply_cached_media(myfile['file_id'], caption=f'**{file_name}**')
    else:
        await update.message.delete()



    #---------------------[ MY FILES FUNC ]---------------------#

async def gen_file_list_button(file_list_no: int, user_id: int):

    file_range=[file_list_no*10-10+1, file_list_no*10]
    user_files, total_files=await db.find_files(user_id, file_range)

    file_list=[]
    async for x in user_files:
        file_list.append([InlineKeyboardButton(x["file_name"], callback_data=f"myfile_{x['_id']}_{file_list_no}")])
    if total_files > 10:
        file_list.append(
                [InlineKeyboardButton("◄", callback_data="{}".format("userfiles_"+str(file_list_no-1) if file_list_no > 1 else 'N/A')),
                 InlineKeyboardButton(f"{file_list_no}/{math.ceil(total_files/10)}", callback_data="N/A"),
                 InlineKeyboardButton("►", callback_data="{}".format("userfiles_"+str(file_list_no+1) if total_files > file_list_no*10 else 'N/A'))]
        )
    if not file_list:
        file_list.append(
                [InlineKeyboardButton("ᴇᴍᴘᴛʏ", callback_data="N/A")])
    file_list.append([InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")])
    return file_list, total_files

async def gen_file_menu(_id, file_list_no, update: CallbackQuery):
    try:
        myfile_info=await db.get_file(_id)
    except FIleNotFound:
        await update.answer("File Not Found")
        return

    file_id=FileId.decode(myfile_info['file_id'])

    if file_id.file_type in PHOTO_TYPES:
        file_type = "Image"
    elif file_id.file_type == FileType.VOICE:
        file_type = "Voice"
    elif file_id.file_type in (FileType.VIDEO, FileType.ANIMATION, FileType.VIDEO_NOTE):
        file_type = "Video"
    elif file_id.file_type == FileType.DOCUMENT:
        file_type = "Document"
    elif file_id.file_type == FileType.STICKER:
        file_type = "Sticker"
    elif file_id.file_type == FileType.AUDIO:
        file_type = "Audio"
    else:
        file_type = "Unknown"

    page_link = f"{Server.URL}watch/{myfile_info['_id']}"
    stream_link = f"{Server.URL}dl/{myfile_info['_id']}"
    if "video" in file_type.lower():
        MYFILES_BUTTONS = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("sᴛʀᴇᴀᴍ", url=page_link), InlineKeyboardButton("ᴅᴏᴡɴʟᴏᴀᴅ", url=stream_link)],
                [InlineKeyboardButton("ɢᴇᴛ ғɪʟᴇ", callback_data=f"sendfile_{myfile_info['_id']}"),
                 InlineKeyboardButton("ʀᴇᴠᴏᴋᴇ ғɪʟᴇ", callback_data=f"msgdelete_{myfile_info['_id']}_{file_list_no}")],
                [InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="userfiles_{}".format(file_list_no))]
            ]
        )
    else:
        MYFILES_BUTTONS = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("ᴅᴏᴡɴʟᴏᴀᴅ", url=stream_link)],
                [InlineKeyboardButton("ɢᴇᴛ ғɪʟᴇ", callback_data=f"sendfile_{myfile_info['_id']}"),
                 InlineKeyboardButton("ʀᴇᴠᴏᴋᴇ ғɪʟᴇ", callback_data=f"msgdelete_{myfile_info['_id']}_{file_list_no}")],
                [InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="userfiles_{}".format(file_list_no))]
            ]
        )

    TiMe = myfile_info['time']
    if type(TiMe) == float:
        date = datetime.datetime.fromtimestamp(TiMe)
    await update.edit_message_caption(
        caption="**File Name :** `{}`\n**File Size :** `{}`\n**File Type :** `{}`\n**Created On :** `{}`".format(myfile_info['file_name'],
                                                                                                                    humanbytes(int(myfile_info['file_size'])),
                                                                                                                    file_type,
                                                                                                                    TiMe if isinstance(TiMe,str) else date.date()),
                                                                                                                    reply_markup=MYFILES_BUTTONS )


async def delete_user_file(_id, file_list_no: int, update:CallbackQuery):

    try:
        myfile_info=await db.get_file(_id)
    except FIleNotFound:
        await update.answer("File Already Deleted")
        return

    await db.delete_one_file(myfile_info['_id'])
    await db.count_links(update.from_user.id, "-")
    await update.message.edit_caption(
            caption= "**Fɪʟᴇ Dᴇʟᴇᴛᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ !**" + update.message.caption.replace("Cᴏɴғɪʀᴍ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴅᴇʟᴇᴛᴇ ᴛʜᴇ Fɪʟᴇ", ""),
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ʙᴀᴄᴋ", callback_data=f"userfiles_1")]])
        )

async def delete_user_filex(_id, update:CallbackQuery):

    try:
        myfile_info=await db.get_file(_id)
    except FIleNotFound:
        await update.answer("File Already Deleted")
        return

    await db.delete_one_file(myfile_info['_id'])
    await db.count_links(update.from_user.id, "-")
    await update.message.edit_caption(
            caption= "**Fɪʟᴇ Dᴇʟᴇᴛᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ !**\n\n",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data=f"close")]])
        )


    

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
        """
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
"""
        
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
"""
