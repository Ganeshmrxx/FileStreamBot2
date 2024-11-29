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
db = Database(Telegram.DATABASE_URL, Telegram.SESSION_NAME)
botno= "q"
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

#---------------------[ START CMD ]---------------------#
@FileStream.on_callback_query()
async def cb_data(bot, update: CallbackQuery):
    usr_cmd = update.data.split("_")
    logging.info("callback")
    logging.info(usr_cmd)
    print("calback")
    print(usr_cmd)
   
    # Handle pagination logic when the callback starts with "next_"
    if usr_cmd[0] == "next_":
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
        if not search:
            await update.answer("You are using an outdated message. Please send your request again.", show_alert=True)
            return

        # Fetch the search results for the next page
        files, n_offset, total = get_search_results(ss, offset=offset, filter=True)
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
                    text=f"[{get_size(file.file_size)}]💠{modify_filename(file.file_name)}",
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

   
    elif usr_cmd[0] == "home":
        await update.message.edit_text(
            text=LANG.START_TEXT.format(update.from_user.mention, FileStream.username),
            disable_web_page_preview=True,
            reply_markup=BUTTON.START_BUTTONS
        )
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

