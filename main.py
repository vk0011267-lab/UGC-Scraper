from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
import httpx
import re
from datetime import datetime

app = FastAPI()


# 🌐 Home Page (NO JINJA - DIRECT HTML SERVE)
@app.get("/", response_class=HTMLResponse)
async def home():
    return FileResponse("templates/index.html")


# 🔁 Convert URL to m.vk.com
def convert_to_mobile(url):
    if "vkvideo.com" in url:
        url = url.replace("vkvideo.com", "vk.com")

    if "vk.com" in url:
        return url.replace("vk.com", "m.vk.com")

    return url


# 🔍 Extract data safely
def extract_data(html, original_url):
    def find(pattern):
        try:
            match = re.search(pattern, html)
            return match.group(1) if match else "N/A"
        except:
            return "N/A"

    # 📌 Title
    title = find(r'"md_title":"(.*?)"')
    if title == "N/A":
        title = find(r'<title>(.*?)</title>')

    # 👁 Views
    views = find(r'"views":(\d+)')

    # ⏱ Duration
    duration = find(r'"duration":(\d+)')
    if duration != "N/A":
        try:
            sec = int(duration)
            duration = str(datetime.utcfromtimestamp(sec).strftime('%H:%M:%S'))
        except:
            duration = "N/A"

    # 👤 Uploader
    uploader = find(r'"md_author":"(.*?)"')

    # 📅 Date
    timestamp = find(r'"date":(\d+)')
    if timestamp != "N/A":
        try:
            date = datetime.fromtimestamp(int(timestamp)).strftime('%d:%m:%Y')
        except:
            date = "N/A"
    else:
        date = "N/A"

    # 🔗 Profile URL
    owner = find(r'"owner_id":(-?\d+)')
    if owner != "N/A":
        profile_url = f"https://vk.com/id{owner}"
    else:
        profile_url = "N/A"

    return {
        "url": original_url,
        "duration": duration,
        "title": title,
        "views": views,
        "date": date,
        "profile": profile_url,
        "uploader": uploader
    }


# 🚀 Scrape API (one-by-one)
@app.post("/api/scrape")
async def scrape(request: Request):
    try:
        data = await request.json()
        url = data.get("url")

        if not url:
            return {"error": "No URL provided"}

        mobile_url = convert_to_mobile(url)

        html = ""

        try:
            async with httpx.AsyncClient(headers={
                "User-Agent": "Mozilla/5.0"
            }) as client:
                res = await client.get(mobile_url, timeout=10)
                html = res.text
        except:
            html = ""

        result = extract_data(html, url)
        return result

    except Exception as e:
        return {"error": str(e)}
