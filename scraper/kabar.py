import requests
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime, timedelta, date
from concurrent.futures import ThreadPoolExecutor
import re


BASE_URL = "https://kabartrenggalek.com"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/139.0.0.0 Safari/537.36"
    )
}


# ============================================================
# KONVERSI BULAN INDONESIA
# ============================================================

BULAN = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "Mei": 5,
    "Jun": 6,
    "Jul": 7,
    "Agu": 8,
    "Sep": 9,
    "Okt": 10,
    "Nov": 11,
    "Des": 12
}


# ============================================================
# PARSE TANGGAL ARTIKEL
# ============================================================

def parse_date(text):

    if not text:
        return None

    text = text.strip()
    now = datetime.now()

    # -----------------------------------------
    # Format: "23 jam lalu"
    # -----------------------------------------
    match = re.search(
        r"(\d+)\s+jam lalu",
        text,
        re.IGNORECASE
    )

    if match:
        return now - timedelta(
            hours=int(match.group(1))
        )

    # -----------------------------------------
    # Format: "2 hari lalu"
    # -----------------------------------------
    match = re.search(
        r"(\d+)\s+hari lalu",
        text,
        re.IGNORECASE
    )

    if match:
        return now - timedelta(
            days=int(match.group(1))
        )

    # -----------------------------------------
    # Format tanggal: DD-MM-YYYY
    # Contoh: 30-08-2026
    # -----------------------------------------
    for fmt in (
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%d.%m.%Y"
    ):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass

    # -----------------------------------------
    # Format: "12 Agu 2026"
    # -----------------------------------------
    parts = text.split()

    if len(parts) == 3:
        try:
            hari = int(parts[0])
            bulan = BULAN.get(parts[1].capitalize())
            tahun = int(parts[2])

            if bulan:
                return datetime(
                    tahun,
                    bulan,
                    hari
                )

        except (ValueError, TypeError):
            pass

    return None

# ============================================================
# KONVERSI INPUT TANGGAL
# ============================================================

def convert_input_date(value):

    if value is None:
        return None

    if isinstance(value, datetime):
        return value

    if isinstance(value, date):
        return datetime.combine(
            value,
            datetime.min.time()
        )

    if isinstance(value, str):
        try:
            return datetime.strptime(
                value,
                "%Y-%m-%d"
            )
        except ValueError:
            return None

    return None


# ============================================================
# SCRAPE DETAIL ARTIKEL
# ============================================================

def scrape_article(url):

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=10
        )

        if response.status_code != 200:
            print(
                "Gagal membuka:",
                url,
                "Status:",
                response.status_code
            )
            # Tetap kembalikan record kosong.
            # Data dari CARD sudah valid dan tetap harus masuk tabel.
            return {
                "Tanggal": None,
                "Judul": "",
                "Penulis": "",
                "Isi": "",
                "Link": url,
                "Kategori": ""
            }

        soup = BeautifulSoup(
            response.text,
            "lxml"
        )

    except requests.RequestException as e:
        print(
            "Gagal request artikel:",
            e
        )
        # Jangan buang artikel hanya karena halaman detail gagal.
        return {
            "Tanggal": None,
            "Judul": "",
            "Penulis": "",
            "Isi": "",
            "Link": url,
            "Kategori": ""
        }

    except Exception as e:
        print(
            "Error artikel:",
            e
        )
        return {
            "Tanggal": None,
            "Judul": "",
            "Penulis": "",
            "Isi": "",
            "Link": url,
            "Kategori": ""
        }

    # ========================================================
    # JUDUL
    # ========================================================

    title = ""

    title_tag = soup.select_one(
        "article.article-detail h1"
    )

    # fallback jika struktur detail sedikit berubah
    if not title_tag:
        title_tag = soup.select_one("h1")

    if title_tag:
        title = title_tag.get_text(
            " ",
            strip=True
        )

    # ========================================================
    # PENULIS
    # ========================================================

    author = ""

    author_tag = soup.select_one(
        ".article-detail-byline "
        "a[href^='/penulis/']"
    )

    # fallback
    if not author_tag:
        author_tag = soup.select_one(
            "a[href^='/penulis/']"
        )

    if author_tag:
        author = author_tag.get_text(
            " ",
            strip=True
        )

    # ========================================================
    # ISI ARTIKEL
    # ========================================================

    isi = ""

    content = soup.select_one(
        "div.article-detail-content"
    )

    if content:

        paragraphs = []

        for p in content.find_all("p"):

            text = p.get_text(
                " ",
                strip=True
            )

            if (
                text
                and text != "Advertisement"
            ):
                paragraphs.append(text)

        isi = "\n".join(
            paragraphs
        )

    # ========================================================
    # TANGGAL ARTIKEL
    # ========================================================

    tanggal = None

    date_tag = soup.select_one(
        "span.article-detail-time"
    )

    if date_tag:
        tanggal = parse_date(
            date_tag.get_text(
                " ",
                strip=True
            )
        )

    return {
        "Tanggal": tanggal,
        "Judul": title,
        "Penulis": author,
        "Isi": isi,
        "Link": url,
        "Kategori": ""
    }


# ============================================================
# AMBIL DETAIL ARTIKEL (UNTUK THREAD)
# ============================================================

def _scrape_detail_item(item):
    """Ambil detail artikel tanpa mengubah struktur hasil scraper."""
    link, title_card, tanggal, kategori = item

    article = scrape_article(link)

    # Tetap masukkan data dari halaman pencarian jika detail gagal.
    article["Tanggal"] = tanggal.date()

    if not article["Judul"]:
        article["Judul"] = title_card

    article["Kategori"] = kategori

    return article


# ============================================================
# SCRAPE SEARCH
# ============================================================

def scrape_search(
    keyword,
    start_date=None,
    end_date=None
):

    # ========================================================
    # NORMALISASI TANGGAL
    # ========================================================

    start_date = convert_input_date(start_date)
    end_date = convert_input_date(end_date)

    # Tanggal akhir mencakup satu hari penuh
    if end_date:
        end_date = end_date.replace(
            hour=23,
            minute=59,
            second=59,
            microsecond=999999
        )

    results = []
    page = 1
    stop_scraping = False

    # ========================================================
    # THREAD DETAIL ARTIKEL
    # ========================================================
    # Halaman pencarian tetap diambil berurutan, tetapi halaman
    # detail beberapa artikel diambil bersamaan. Ini bagian yang
    # paling banyak memakan waktu pada scraper lama.
    MAX_WORKERS = 10

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:

        # ========================================================
        # SCRAPE SEMUA HALAMAN
        # ========================================================

        while not stop_scraping:

            print(f"\\nScraping Kabar Trenggalek halaman {page}")

            url = f"{BASE_URL}/cari"
            params = {
                "q": keyword,
                "page": page
            }

            try:
                response = requests.get(
                    url,
                    params=params,
                    headers=HEADERS,
                    timeout=20
                )
            except requests.RequestException as e:
                print("Gagal request halaman:", e)
                break

            if response.status_code != 200:
                print("Status:", response.status_code)
                break

            soup = BeautifulSoup(response.text, "lxml")

            # ====================================================
            # CARD ARTIKEL UI BARU
            # ====================================================

            cards = soup.select("article.article-card--list")

            print(f"Ditemukan {len(cards)} artikel")

            if not cards:
                break

            # Menampung artikel yang lolos filter tanggal.
            # Detailnya nanti di-request secara paralel.
            detail_items = []

            # ====================================================
            # BACA CARD ARTIKEL
            # ====================================================

            for card in cards:
                try:
                    # --------------------------------------------
                    # LINK
                    # --------------------------------------------
                    link_tag = card.select_one("h3 a")

                    if not link_tag:
                        continue

                    href = link_tag.get("href")

                    if not href:
                        continue

                    link = urljoin(BASE_URL, href)

                    # --------------------------------------------
                    # JUDUL DARI CARD
                    # --------------------------------------------
                    title_card = link_tag.get_text(" ", strip=True)

                    # --------------------------------------------
                    # TANGGAL
                    # --------------------------------------------
                    tanggal_tag = card.select_one(
                        "span.article-card-time"
                    )

                    if not tanggal_tag:
                        continue

                    tanggal_text = tanggal_tag.get_text(
                        " ",
                        strip=True
                    )

                    tanggal = parse_date(tanggal_text)

                    if tanggal is None:
                        print(
                            "Tanggal tidak dikenali:",
                            tanggal_text
                        )
                        continue

                    # --------------------------------------------
                    # FILTER TANGGAL
                    # --------------------------------------------
                    if end_date and tanggal > end_date:
                        continue

                    # Karena hasil Kabar Trenggalek diurutkan dari
                    # terbaru ke terlama, begitu melewati start_date
                    # kita tidak perlu memproses halaman berikutnya.
                    if start_date and tanggal < start_date:
                        stop_scraping = True
                        break

                    # --------------------------------------------
                    # KATEGORI
                    # --------------------------------------------
                    kategori = ""

                    kategori_tag = card.select_one(
                        "a.article-card-kicker"
                    )

                    if kategori_tag:
                        kategori = kategori_tag.get_text(
                            " ",
                            strip=True
                        )

                    detail_items.append(
                        (link, title_card, tanggal, kategori)
                    )

                except Exception as e:
                    print(f"Gagal membaca card artikel: {e}")
                    continue

            # ====================================================
            # SCRAPE DETAIL SECARA PARALEL
            # ====================================================

            if detail_items:
                futures = [
                    executor.submit(_scrape_detail_item, item)
                    for item in detail_items
                ]

                # executor.map menjaga urutan artikel sesuai card.
                # Jika satu artikel error, artikel lain tetap diproses.
                for item, future in zip(detail_items, futures):
                    try:
                        article = future.result()
                        results.append(article)

                        tanggal = item[2]
                        print(
                            f"{tanggal.strftime('%Y-%m-%d')} | "
                            f"{article['Judul']}"
                        )

                    except Exception as e:
                        print(f"Gagal mengambil artikel: {e}")

            if stop_scraping:
                break

            # ====================================================
            # PAGINATION
            # ====================================================

            next_exists = False

            for a in soup.select("nav.site-pagination a"):
                href = a.get("href", "")
                text = a.get_text(" ", strip=True)

                if (
                    f"page={page + 1}" in href
                    or text == "Berikutnya →"
                ):
                    next_exists = True
                    break

            if not next_exists:
                break

            page += 1

    # ========================================================
    # DATAFRAME
    # ========================================================

    df = pd.DataFrame(
        results,
        columns=[
            "Tanggal",
            "Judul",
            "Penulis",
            "Isi",
            "Link",
            "Kategori"
        ]
    )

    # ========================================================
    # HAPUS DUPLIKAT + SORTING
    # ========================================================

    if not df.empty:
        df = df.drop_duplicates(
            subset="Link",
            keep="first"
        )

        df = df.sort_values(
            "Tanggal",
            ascending=False
        )

        df = df.reset_index(drop=True)

    return df
