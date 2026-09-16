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

        if r.status_code != 200:
            return "", ""

        soup = BeautifulSoup(r.text, "html.parser")

        # =========================
        # AMBIL KATEGORI
        # =========================

        kategori = ""

        category_tag = soup.select_one(
            "header.entry-header-single .cat-links-content a"
        )

        if category_tag:
            kategori = category_tag.get_text(
                strip=True
            )

        # =========================
        # AMBIL ISI BERITA
        # =========================

        content = soup.find(
            "div",
            class_="entry-content"
        )

        if not content:
            return "", kategori

        paragraphs = content.find_all("p")

        isi = "\n".join(
            p.get_text(" ", strip=True)
            for p in paragraphs
        )

        return isi, kategori

    except Exception:
        return "", ""


def scrape_search(keyword, start_date=None, end_date=None):

    if start_date:
        start_date = datetime.strptime(
            start_date,
            "%Y-%m-%d"
        ).date()

    if end_date:
        end_date = datetime.strptime(
            end_date,
            "%Y-%m-%d"
        ).date()

    data = []
    page = 1

    while True:

        if page == 1:
            url = (
                f"{BASE_URL}/"
                f"?s={quote(keyword)}"
                f"&post_type[]=post"
            )
        else:
            url = (
                f"{BASE_URL}/page/{page}/"
                f"?s={quote(keyword)}"
                f"&post_type[]=post"
            )

        try:

            r = requests.get(
                url,
                headers=HEADERS,
                timeout=20
            )

        except requests.RequestException:
            break

        if r.status_code != 200:
            break

        soup = BeautifulSoup(
            r.text,
            "html.parser"
        )

        articles = soup.find_all("article")

        if not articles:
            break

        stop = False

        for article in articles:

            try:

                # =========================
                # JUDUL
                # =========================

                title_tag = article.find(
                    "h2",
                    class_="entry-title"
                )

                if not title_tag:
                    continue

                title = title_tag.get_text(
                    strip=True
                )

                # =========================
                # LINK
                # =========================

                link_tag = title_tag.find("a")

                if not link_tag:
                    continue

                link = link_tag.get("href")

                # =========================
                # TANGGAL
                # =========================

                date_tag = article.find(
                    "time",
                    class_="entry-date"
                )

                if not date_tag:
                    continue

                tanggal = datetime.fromisoformat(
                    date_tag["datetime"]
                ).date()

                # =========================
                # FILTER TANGGAL
                # =========================

                if start_date and tanggal < start_date:
                    stop = True
                    break

                if end_date and tanggal > end_date:
                    continue

                # =========================
                # PENULIS
                # =========================

                author = ""

                posted = article.find(
                    "div",
                    class_="posted-by"
                )

                if posted:

                    a = posted.find("a")

                    if a:
                        author = a.get_text(
                            strip=True
                        )

                # =========================
                # AMBIL ISI + KATEGORI
                # DARI HALAMAN ARTIKEL
                # =========================

                isi, kategori = get_article(link)

                # =========================
                # SIMPAN DATA
                # =========================

                data.append({
                    "Tanggal": tanggal,
                    "Judul": title,
                    "Penulis": author,
                    "Isi": isi,
                    "Link": link,
                    "Kategori": kategori
                })

            except Exception:
                continue

        if stop:
            break

        # =========================
        # CEK HALAMAN BERIKUTNYA
        # =========================

        if not soup.find(
            "a",
            class_="next"
        ):
            break

        page += 1

        time.sleep(0.3)

    return pd.DataFrame(data)