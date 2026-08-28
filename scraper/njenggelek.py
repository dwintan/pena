import requests
import pandas as pd
import json
import html
from bs4 import BeautifulSoup
from datetime import datetime
import time

BASE_URL = "https://trenggaleknjenggelek.jawapos.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

session = requests.Session()


def scrape_article(url):

    try:
        response = session.get(
            url,
            headers=HEADERS,
            timeout=20
        )

        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, "lxml")

        app = soup.find("div", id="app")

        if app is None:
            return None

        data = json.loads(
            html.unescape(app["data-page"])
        )

        article = data["props"]["article"]

    except Exception:
        return None

    title = article.get("title", "")

    date_string = article.get("date", "")

    category = ""

    if article.get("category"):
        category = article["category"].get("name", "")

    author = ""

    if article.get("authors"):
        author = ", ".join(
            x.get("name", "")
            for x in article["authors"]
        )

    html_content = article.get("content", "")

    soup_content = BeautifulSoup(
        html_content,
        "lxml"
    )

    # Hapus Baca Juga
    for tag in soup_content.select("strong.readmore"):
        tag.decompose()

    # Hapus script dan style
    for tag in soup_content(["script", "style"]):
        tag.decompose()

    paragraphs = []

    for p in soup_content.find_all("p"):

        text = p.get_text(" ", strip=True)

        if not text:
            continue

        if text.startswith("Baca Juga"):
            continue

        paragraphs.append(text)

    isi = "\n".join(paragraphs)

    # ==========================
    # SAMAKAN FORMAT TANGGAL
    # ==========================

    try:
        tanggal = datetime.strptime(
            date_string[:10],
            "%Y-%m-%d"
        ).date()
    except Exception:
        tanggal = None

    return {
        "Tanggal": tanggal,
        "Judul": title,
        "Penulis": author,
        "Isi": isi,
        "Link": url,
        "Kategori": category
    }


def scrape_search(
    keyword,
    start_date=None,
    end_date=None
):

    # ==========================
    # SAMAKAN FILTER KE datetime.date
    # ==========================

    if start_date:
        if isinstance(start_date, str):
            start_date = datetime.strptime(
                start_date,
                "%Y-%m-%d"
            ).date()
        elif isinstance(start_date, datetime):
            start_date = start_date.date()

    if end_date:
        if isinstance(end_date, str):
            end_date = datetime.strptime(
                end_date,
                "%Y-%m-%d"
            ).date()
        elif isinstance(end_date, datetime):
            end_date = end_date.date()

    results = []

    page = 1

    while True:

        print(f"Scraping Njenggelek halaman {page}")

        url = (
            f"{BASE_URL}/search"
            f"?q={keyword}&page={page}"
        )

        try:

            response = session.get(
                url,
                headers=HEADERS,
                timeout=20
            )

        except Exception:
            break

        if response.status_code != 200:
            break

        soup = BeautifulSoup(
            response.text,
            "lxml"
        )

        app = soup.find(
            "div",
            id="app"
        )

        if app is None:
            break

        try:

            data = json.loads(
                html.unescape(
                    app["data-page"]
                )
            )

            news = data["props"]["news"]["data"]

        except Exception:
            break

        if len(news) == 0:
            break

        for item in news:

            try:

                article_url = (
                    BASE_URL
                    + "/"
                    + item["category"]["slug"]
                    + "/"
                    + item["article_id"]
                    + "/"
                    + item["slug"]
                )

                article = scrape_article(
                    article_url
                )

                if article is None:
                    continue

                dt = article["Tanggal"]

                if dt is None:
                    continue

                # ==========================
                # FILTER TANGGAL
                # ==========================

                if start_date and dt < start_date:
                    continue

                if end_date and dt > end_date:
                    continue

                results.append(article)

                time.sleep(0.2)

            except Exception as e:

                print(
                    f"Gagal mengambil artikel: {e}"
                )

        # ==========================
        # CEK HALAMAN SELANJUTNYA
        # ==========================

        try:

            has_more = data[
                "props"
            ][
                "news"
            ][
                "paginatorInfo"
            ][
                "hasMorePages"
            ]

        except Exception:

            has_more = False

        if not has_more:
            break

        page += 1

    # ==========================
    # DATAFRAME
    # ==========================

    df = pd.DataFrame(results)

    if not df.empty:

        df = df.drop_duplicates(
            subset="Link"
        )

        df = df.sort_values(
            "Tanggal",
            ascending=False
        )

        df = df.reset_index(
            drop=True
        )

    return df