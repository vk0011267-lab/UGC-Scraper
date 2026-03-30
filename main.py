from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import httpx
import re
from datetime import datetime

app = FastAPI()
templates = Jinja2Templates(directory="templates")


# 🔁 Convert URL to m.vk.com
def convert_to_mobile(url):
    if "vkvideo.com" in url:
        url = url.replace("vkvideo.com", "vk.com")

    if "vk.com" in url:
        return url.replace("vk.com", "m.vk.com")

    return url


# 🔍 Extract data
def extract_data(html, original_url):
    def find(pattern):
        match = re.search(pattern, html)
        return match.group(1) if match else "N/A"

    title = find(r'"md_title":"(.*?)"')
    if title == "N/A":
        title = find(r'<title>(.*?)</title>')

    views = find(r'"views":(\d+)')
    duration = find(r'"duration":(\d+)')
    uploader = find(r'"md_author":"(.*?)"')

    timestamp = find(r'"date":(\d+)')
    if timestamp != "N/A":
        date = datetime.fromtimestamp(int(timestamp)).strftime('%d:%m:%Y')
    else:
        date = "N/A"

    # ⏱ duration convert
    if duration != "N/A":
        sec = int(duration)
        duration = str(datetime.utcfromtimestamp(sec).strftime('%H:%M:%S'))

    # 👤 profile
    owner = find(r'"owner_id":(-?\d+)')
    profile_url = f"https://vk.com/id{owner}" if owner != "N/A" else "N/A"

    return {
        "url": original_url,
        "duration": duration,
        "title": title,
        "views": views,
        "date": date,
        "profile": profile_url,
        "uploader": uploader
    }


# 🌐 Home Page
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# 🚀 Scrape API (ONE BY ONE)
@app.post("/api/scrape")
async def scrape(request: Request):
    data = await request.json()
    url = data.get("url")

    mobile_url = convert_to_mobile(url)

    html = ""

    try:
        async with httpx.AsyncClient(headers={
            "User-Agent": "Mozilla/5.0"
        }) as client:
            res = await client.get(mobile_url, timeout=10)
            html = res.text

            # 🤖 human check fallback
            if "I'm human" in html or "captcha" in html:
                html = res.text  # fallback simple (Render me playwright heavy hota h)

    except:
        html = ""

    result = extract_data(html, url)
    return result
