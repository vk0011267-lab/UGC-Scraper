from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
import httpx
import re
from datetime import datetime

app = FastAPI()


@app.get("/", response_class=HTMLResponse)
async def home():
    return FileResponse("templates/index.html")


def convert_to_mobile(url):
    if "vkvideo" in url:
        url = url.replace("vkvideo.ru", "vk.com").replace("vkvideo.com", "vk.com")

    if "vk.com" in url:
        return url.replace("vk.com", "m.vk.com")

    return url


def extract_data(html, original_url):

    def find(pattern):
        match = re.search(pattern, html)
        return match.group(1) if match else "N/A"

    title = find(r'"md_title":"(.*?)"')
    views = find(r'"views":(\d+)')
    duration = find(r'"duration":(\d+)')
    uploader = find(r'"md_author":"(.*?)"')

    timestamp = find(r'"date":(\d+)')
    date = datetime.fromtimestamp(int(timestamp)).strftime('%d:%m:%Y') if timestamp != "N/A" else "N/A"

    if duration != "N/A":
        duration = str(datetime.utcfromtimestamp(int(duration)).strftime('%H:%M:%S'))

    owner = find(r'"owner_id":(-?\d+)')
    profile = f"https://vk.com/id{owner}" if owner != "N/A" else "N/A"

    return {
        "url": original_url,
        "duration": duration,
        "title": title,
        "views": views,
        "date": date,
        "profile": profile,
        "uploader": uploader
    }


@app.post("/api/scrape")
async def scrape(request: Request):
    data = await request.json()
    url = data.get("url")

    mobile_url = convert_to_mobile(url)

    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X)",
        "Accept-Language": "en-US,en;q=0.9"
    }

    async with httpx.AsyncClient() as client:
        res = await client.get(mobile_url, headers=headers, timeout=15)
        html = res.text

    return extract_data(html, url)
