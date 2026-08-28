import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime
import time

BASE_URL = "https://kabartrenggalek.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def scrape_article(url):
    response = requests.get(url, headers=HEADERS, timeout=20)
    soup = BeautifulSoup(response.text, "lxml")

    title = ""
    author = ""
    isi = ""

    if soup.select_one("h1"):
        title = soup.select_one("h1").get_text(strip=True)

    if soup.select_one("a[href^='/penulis/']"):
        author = soup.select_one("a[href^='/penulis/']").get_text(strip=True)

    content = soup.select_one(
        "div.prose.prose-lg.max-w-none.mb-8.text-gray-700.leading-relaxed"
    )

    if content:
        paragraphs = []
        for p in content.find_all("p"):
            text = p.get_text(" ", strip=True)
            if text and text != "Advertisement":
                paragraphs.append(text)
        isi = "\n".join(paragraphs)

    return title, author, isi


def scrape_search(keyword, start_date=None, end_date=None):

    if start_date:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")

    if end_date:
        end_date = datetime.strptime(end_date, "%Y-%m-%d")

    results = []
    page = 1
    stop = False

    while not stop:

        url = f"{BASE_URL}/latest?q={keyword}&page={page}"

        r = requests.get(url, headers=HEADERS, timeout=20)

        if r.status_code != 200:
            break

        soup = BeautifulSoup(r.text, "lxml")
        cards = soup.select("a.news-card")

        if not cards:
            break

        for card in cards:

            href = card.get("href")
            if not href:
                continue

            tanggal = datetime.strptime(
                card.select_one("span.text-gray-500").get_text(strip=True),
                "%d %b %Y"
            )

            if start_date and tanggal < start_date:
                stop = True
                break

            if end_date and tanggal > end_date:
                continue

            kategori = ""
            k = card.select_one("span.text-blue-700")
            if k:
                kategori = k.get_text(strip=True)

            link = urljoin(BASE_URL, href)
            judul, penulis, isi = scrape_article(link)

            results.append({
                "Tanggal": tanggal.date(),
                "Judul": judul,
                "Penulis": penulis,
                "Isi": isi,
                "Link": link,
                "Kategori": kategori
            })

            time.sleep(0.2)

        if stop:
            break

        if soup.find("a", rel="next") is None:
            break

        page += 1

    return pd.DataFrame(results)