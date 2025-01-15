import aiohttp
import jinja2
import urllib.parse
from FileStream.config import Telegram, Server
from FileStream.utils.database import Database
from FileStream.utils.human_readable import humanbytes
db = Database(Telegram.DATABASE_URL, Telegram.SESSION_NAME)


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
    # query = re.sub(r'\s+', ' ', clean_text).strip()
    # print(query)
    return file_name

async def render_page(db_id):
    file_data=await db.get_file(db_id)
    src = urllib.parse.urljoin(Server.URL, f'dl/{file_data["_id"]}')
    file_size = humanbytes(file_data['file_size'])
    file_names = file_data['file_name'].replace("_", " ")
    file_name = await modify_filename(file_names)

    if str((file_data['mime_type']).split('/')[0].strip()) == 'video':
        template_file = "FileStream/template/play.html"
    else:
        template_file = "FileStream/template/dl.html"
        async with aiohttp.ClientSession() as s:
            async with s.get(src) as u:
                file_size = humanbytes(int(u.headers.get('Content-Length')))

    with open(template_file) as f:
        template = jinja2.Template(f.read())

    return template.render(
        file_name=file_name,
        file_url=src,
        file_size=file_size
    )
