from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from playwright.async_api import async_playwright
import re
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


# 🤖 Fetch with browser (IMPORTANT)
async def fetch_html(url):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.goto(url, timeout=60000)
        await page.wait_for_timeout(3000)

        content = await page.content()
        await browser.close()

        return content


# 🔍 Extract data (VIEW SOURCE LIKE)
def extract_data(html, original_url):

    def find(pattern):
        match = re.search(pattern, html)
        return match.group(1) if match else "N/A"

    title = find(r'"md_title":"(.*?)"')
    views = find(r'"views":(\d+)')
    duration = find(r'"duration":(\d+)')
    uploader = find(r'"md_author":"(.*?)"')

    timestamp = find(r'"date":(\d+)')
    if timestamp != "N/A":
        date = datetime.fromtimestamp(int(timestamp)).strftime('%d:%m:%Y')
    else:
        date = "N/A"

    if duration != "N/A":
        sec = int(duration)
        duration = str(datetime.utcfromtimestamp(sec).strftime('%H:%M:%S'))

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


# 🚀 API
@app.post("/api/scrape")
async def scrape(request: Request):
    data = await request.json()
    url = data.get("url")

    mobile_url = convert_to_mobile(url)

    html = await fetch_html(mobile_url)

    return extract_data(html, url)
