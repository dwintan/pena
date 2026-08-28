import pandas as pd

from scraper.kabar import scrape_search as kabar
from scraper.njenggelek import scrape_search as njeng
from scraper.suara import scrape_search as suara


def collect(keyword, portals, start=None, end=None):

    hasil = []

    # ========================================================
    # KABAR TRENGGALEK
    # ========================================================

    if "Kabar Trenggalek" in portals:

        df = kabar(
            keyword,
            start,
            end
        )

        if df is not None and not df.empty:

            df["Sumber"] = "Kabar Trenggalek"

            hasil.append(df)

    # ========================================================
    # TRENGGALEK NJENGGELEK
    # ========================================================

    if "Trenggalek Njenggelek" in portals:

        df = njeng(
            keyword,
            start,
            end
        )

        if df is not None and not df.empty:

            df["Sumber"] = "Trenggalek Njenggelek"

            hasil.append(df)

    # ========================================================
    # SUARA TRENGGALEK
    # ========================================================

    if "Suara Trenggalek" in portals:

        df = suara(
            keyword,
            start,
            end
        )

        if df is not None and not df.empty:

            df["Sumber"] = "Suara Trenggalek"

            hasil.append(df)

    # ========================================================
    # TIDAK ADA HASIL
    # ========================================================

    if not hasil:

        return pd.DataFrame(
            columns=[
                "Tanggal",
                "Judul",
                "Penulis",
                "Isi",
                "Link",
                "Kategori",
                "Sumber"
            ]
        )

    # ========================================================
    # GABUNG DATA
    # ========================================================

    df = pd.concat(
        hasil,
        ignore_index=True
    )

    # ========================================================
    # PASTIKAN TANGGAL SERAGAM
    # ========================================================

    if "Tanggal" in df.columns:

        df["Tanggal"] = pd.to_datetime(
            df["Tanggal"],
            errors="coerce"
        )

    # ========================================================
    # HAPUS DUPLIKAT
    # ========================================================

    if "Link" in df.columns:

        df = df.drop_duplicates(
            subset=["Link"],
            keep="first"
        )

    # ========================================================
    # SORTING
    # ========================================================

    if "Tanggal" in df.columns:

        df = df.sort_values(
            by="Tanggal",
            ascending=False,
            na_position="last"
        )

    # ========================================================
    # RESET INDEX
    # ========================================================

    df = df.reset_index(
        drop=True
    )

    return df