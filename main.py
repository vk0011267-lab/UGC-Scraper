from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import httpx
import re
from datetime import datetime
import os

app = FastAPI()

# ✅ FIX: absolute path for templates (Render issue solve)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


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

    title = find(r'"md_title":"(.*?)"')
    if title == "N/A":
        title = find(r'<title>(.*?)</title>')

    views = find(r'"views":(\d+)')
    duration = find(r'"duration":(\d+)')
    uploader = find(r'"md_author":"(.*?)"')

    timestamp = find(r'"date":(\d+)')
    if timestamp != "N/A":
        try:
            date = datetime.fromtimestamp(int(timestamp)).strftime('%d:%m:%Y')
        except:
            date = "N/A"
    else:
        date = "N/A"

    # ⏱ duration convert
    if duration != "N/A":
        try:
            sec = int(duration)
            duration = str(datetime.utcfromtimestamp(sec).strftime('%H:%M:%S'))
        except:
            duration = "N/A"

    # 👤 profile
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


# 🌐 Home Page
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    try:
        return templates.TemplateResponse("index.html", {"request": request})
    except Exception as e:
        return HTMLResponse(content=f"Template Error: {str(e)}", status_code=500)


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
