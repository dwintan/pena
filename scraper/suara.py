import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import quote
import time

BASE_URL = "https://suaratrenggalek.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}


def get_article(url):

    try:

        r = requests.get(url, headers=HEADERS, timeout=20)

        soup = BeautifulSoup(r.text, "html.parser")

        content = soup.find("div", class_="entry-content")

        if not content:
            return ""

        paragraphs = content.find_all("p")

        return "\n".join(
            p.get_text(" ", strip=True)
            for p in paragraphs
        )

    except:
        return ""


def scrape_search(keyword, start_date=None, end_date=None):

    if start_date:
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()

    if end_date:
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

    data = []
    page = 1

    while True:

        if page == 1:
            url = f"{BASE_URL}/?s={quote(keyword)}&post_type[]=post"
        else:
            url = f"{BASE_URL}/page/{page}/?s={quote(keyword)}&post_type[]=post"

        r = requests.get(url, headers=HEADERS, timeout=20)

        if r.status_code != 200:
            break

        soup = BeautifulSoup(r.text, "html.parser")

        articles = soup.find_all("article")

        if not articles:
            break

        stop = False

        for article in articles:

            try:

                title = article.find(
                    "h2",
                    class_="entry-title"
                ).get_text(strip=True)

                link = article.find(
                    "h2",
                    class_="entry-title"
                ).find("a")["href"]

                tanggal = datetime.fromisoformat(
                    article.find(
                        "time",
                        class_="entry-date"
                    )["datetime"]
                ).date()

                if start_date and tanggal < start_date:
                    stop = True
                    break

                if end_date and tanggal > end_date:
                    continue

                author = ""

                posted = article.find("div", class_="posted-by")

                if posted:
                    a = posted.find("a")
                    if a:
                        author = a.get_text(strip=True)

                isi = get_article(link)

                data.append({
                    "Tanggal": tanggal,
                    "Judul": title,
                    "Penulis": author,
                    "Isi": isi,
                    "Link": link,
                    "Kategori": ""
                })

            except:
                pass

        if stop:
            break

        if not soup.find("a", class_="next"):
            break

        page += 1
        time.sleep(0.3)

    return pd.DataFrame(data)