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

