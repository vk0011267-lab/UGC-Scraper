from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
import httpx
import re
import json
from datetime import datetime

app = FastAPI()


# 🌐 Home Page
@app.get("/", response_class=HTMLResponse)
async def home():
    return FileResponse("templates/index.html")


# 🔁 Convert URL
def convert_to_mobile(url):
    if "vkvideo" in url:
        url = url.replace("vkvideo.ru", "vk.com").replace("vkvideo.com", "vk.com")

    if "vk.com" in url:
        return url.replace("vk.com", "m.vk.com")

    return url


# 🔍 Extract using JSON (IMPORTANT FIX)
def extract_data(html, original_url):

    title = "N/A"
    views = "N/A"
    duration = "N/A"
    uploader = "N/A"
    date = "N/A"
    profile_url = "N/A"

    try:
        # 🔥 Extract JSON block
        json_match = re.search(r'playerParams\s*=\s*(\{.*?\});', html)

        if json_match:
            data = json.loads(json_match.group(1))

            video = data.get("params", [{}])[0]

            title = video.get("md_title", "N/A")
            views = video.get("views", "N/A")

            # duration
            dur = video.get("duration")
            if dur:
                duration = str(datetime.utcfromtimestamp(int(dur)).strftime('%H:%M:%S'))

            # uploader
            uploader = video.get("md_author", "N/A")

            # date
            timestamp = video.get("date")
            if timestamp:
                date = datetime.fromtimestamp(int(timestamp)).strftime('%d:%m:%Y')

            # profile
            owner = video.get("owner_id")
            if owner:
                profile_url = f"https://vk.com/id{owner}"

    except:
        pass

    # 🔁 fallback (title only)
    if title == "N/A":
        match = re.search(r'<title>(.*?)</title>', html)
        if match:
            title = match.group(1)

    return {
        "url": original_url,
        "duration": duration,
        "title": title,
        "views": views,
        "date": date,
        "profile": profile_url,
        "uploader": uploader
    }


# 🚀 API
@app.post("/api/scrape")
async def scrape(request: Request):
    try:
        data = await request.json()
        url = data.get("url")

        mobile_url = convert_to_mobile(url)

        async with httpx.AsyncClient(headers={
            "User-Agent": "Mozilla/5.0"
        }) as client:
            res = await client.get(mobile_url, timeout=10)
            html = res.text

        return extract_data(html, url)

    except Exception as e:
        return {"error": str(e)}
