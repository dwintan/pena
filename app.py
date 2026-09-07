import os
from datetime import date

import pandas as pd
import streamlit as st
import plotly.express as px

from scraper.manager import collect
from utils.export import to_excel


# ============================================================
# CONFIG
# ============================================================

st.set_page_config(
    page_title="PENA | BPS Kabupaten Trenggalek",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# LOAD CSS
# ============================================================

css_path = os.path.join("assets", "style.css")

if os.path.exists(css_path):
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(
            f"<style>{f.read()}</style>",
            unsafe_allow_html=True
        )


# ============================================================
# SESSION STATE
# ============================================================

if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame()


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.markdown(
        """
        <div class="sidebar-brand">
            <div class="sidebar-title">PENA</div>
            <div class="sidebar-subtitle">
                Sistem Pengumpulan Fenomena Pendukung Analisis Statistik
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # --------------------------------------------------------
    # KATA KUNCI
    # --------------------------------------------------------

    st.markdown(
        """
        <div class="sidebar-section-title">
            <span class="sidebar-icon">
                <svg viewBox="0 0 24 24">
                    <circle cx="10.8" cy="10.8" r="6.5"></circle>
                    <path d="M16 16l5 5"></path>
                </svg>
            </span>
            <span>Kata Kunci</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    keyword = st.text_input(
        "Kata Kunci",
        placeholder="Contoh: stunting",
        label_visibility="collapsed"
    )

    # --------------------------------------------------------
    # PORTAL BERITA
    # --------------------------------------------------------

    st.markdown(
        """
        <div class="sidebar-section-title portal-title">
            <span class="sidebar-icon">
                <svg viewBox="0 0 24 24">
                    <rect x="4" y="3" width="16" height="18" rx="2"></rect>
                    <path d="M8 7h8"></path>
                    <path d="M8 11h8"></path>
                    <path d="M8 15h5"></path>
                </svg>
            </span>
            <span>Portal Berita</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    portal = []

    portal_options = {
        "Kabar Trenggalek": "Kabar Trenggalek",
        "Trenggalek Njenggelek": "Trenggalek Njenggelek",
        "Suara Trenggalek": "Suara Trenggalek"
    }

    for key, label in portal_options.items():

        checked = st.checkbox(
            label,
            value=True,
            key=f"portal_{key}"
        )

        if checked:
            portal.append(key)

    # --------------------------------------------------------
    # PERIODE
    # --------------------------------------------------------

    st.markdown(
        """
        <div class="sidebar-section-title periode-title">
            <span class="sidebar-icon">
                <svg viewBox="0 0 24 24">
                    <rect x="3" y="5" width="18" height="16" rx="2"></rect>
                    <path d="M7 3v4"></path>
                    <path d="M17 3v4"></path>
                    <path d="M3 9h18"></path>
                </svg>
            </span>
            <span>Rentang Tanggal</span>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Card periode
    # st.markdown(
    #     '<div class="date-card">',
    #     unsafe_allow_html=True
    # )

    with st.container(border=True):

        col_start, col_end = st.columns(2, gap="small")

        with col_start:

            st.markdown(
                '<div class="date-caption">Mulai</div>',
                unsafe_allow_html=True
            )

            tanggal_awal = st.date_input(
                "Tanggal mulai",
                value=pd.Timestamp("2026-01-01").date(),
                format="DD/MM/YYYY",
                label_visibility="collapsed",
                key="tanggal_awal"
            )

        with col_end:

            st.markdown(
                '<div class="date-caption">Sampai</div>',
                unsafe_allow_html=True
            )

            tanggal_akhir = st.date_input(
                "Tanggal sampai",
                value=pd.Timestamp.today().date(),
                format="DD/MM/YYYY",
                label_visibility="collapsed",
                key="tanggal_akhir"
            )

            # st.markdown(
            #     '</div>',
            #     unsafe_allow_html=True
            # )

    # --------------------------------------------------------
    # TOMBOL
    # --------------------------------------------------------

    st.markdown("<div class='sidebar-button-space'></div>", unsafe_allow_html=True)

    cari = st.button(
        "Cari Fenomena",
        use_container_width=True
    )

# ============================================================
# CARI FENOMENA
# ============================================================

if cari:

    if not keyword.strip():

        st.warning(
            "Silakan masukkan kata kunci terlebih dahulu."
        )

    elif not portal:

        st.warning(
            "Pilih minimal satu portal berita."
        )

    elif tanggal_awal > tanggal_akhir:

        st.warning(
            "Tanggal awal tidak boleh lebih besar "
            "daripada tanggal akhir."
        )

    else:

        start = tanggal_awal.strftime(
            "%Y-%m-%d"
        )

        end = tanggal_akhir.strftime(
            "%Y-%m-%d"
        )

        with st.spinner(
            "Sedang mengumpulkan fenomena..."
        ):

            try:

                hasil = collect(
                    keyword=keyword.strip(),
                    portals=portal,
                    start=start,
                    end=end
                )

                if hasil is None:
                    hasil = pd.DataFrame()

                st.session_state.data = hasil

            except Exception as e:

                st.error(
                    "Terjadi kesalahan saat proses scraping."
                )

                st.exception(e)


# ============================================================
# DATA
# ============================================================

df = st.session_state.data.copy()


# Pastikan kolom selalu tersedia
required_columns = [
    "Tanggal",
    "Judul",
    "Penulis",
    "Isi",
    "Link",
    "Kategori",
    "Sumber"
]

for col in required_columns:

    if col not in df.columns:
        df[col] = ""


# Normalisasi tanggal
if not df.empty:

    df["Tanggal"] = pd.to_datetime(
        df["Tanggal"],
        errors="coerce"
    )


# ============================================================
# HERO
# ============================================================

st.html(
    """
    <div class="hero">

        <div class="hero-brand">
            <span class="hero-icon">📰</span>
            <span class="hero-title">PENA</span>
        </div>

        <div class="hero-description">
            Pengumpulan Fenomena Pendukung Analisis Statistik
        </div>

        <div class="hero-location">
            BPS Kabupaten Trenggalek
        </div>

    </div>
    """
)


# ============================================================
# KPI
# ============================================================

artikel = len(df)
jumlah_portal = len(portal)

if not df.empty:

    jumlah_penulis = (
        df["Penulis"]
        .replace("", pd.NA)
        .dropna()
        .nunique()
    )

    jumlah_kategori = (
        df["Kategori"]
        .replace("", pd.NA)
        .dropna()
        .nunique()
    )

else:

    jumlah_penulis = 0
    jumlah_kategori = 0


k1, k2, k3, k4 = st.columns(4)


with k1:
    st.html(
        f"""
        <div class="kpi">
            <div class="kpi-label">Artikel</div>
            <div class="kpi-value">{artikel}</div>
        </div>
        """
    )


with k2:
    st.html(
        f"""
        <div class="kpi">
            <div class="kpi-label">Portal</div>
            <div class="kpi-value">{jumlah_portal}</div>
        </div>
        """
    )


with k3:
    st.html(
        f"""
        <div class="kpi">
            <div class="kpi-label">Penulis</div>
            <div class="kpi-value">{jumlah_penulis}</div>
        </div>
        """
    )


with k4:
    st.html(
        f"""
        <div class="kpi">
            <div class="kpi-label">Kategori</div>
            <div class="kpi-value">{jumlah_kategori}</div>
        </div>
        """
    )


# ============================================================
# BELUM ADA DATA
# ============================================================

if df.empty:

    st.html(
        """
        <div class="empty-state">

            <div class="empty-icon">
                ⌕
            </div>

            <div class="empty-title">
                Belum ada fenomena
            </div>

            <div class="empty-description">
                Masukkan kata kunci, pilih portal berita,
                tentukan rentang tanggal, kemudian klik
                <b>Cari Fenomena</b>.
            </div>

        </div>
        """
    )


    # PORTAL
    st.html(
        """
        <div class="section-title">
            Portal yang Didukung
        </div>

        <div class="section-description">
            PENA mendukung pengumpulan fenomena dari
            portal berita lokal Kabupaten Trenggalek.
        </div>
        """
    )


    p1, p2, p3 = st.columns(3)


    with p1:

        st.html(
            """
            <div class="portal-card">
                <div class="portal-code">KT</div>
                <div>
                    <div class="portal-name">
                        Kabar Trenggalek
                    </div>
                    <div class="portal-desc">
                        Portal berita lokal
                    </div>
                </div>
            </div>
            """
        )


    with p2:

        st.html(
            """
            <div class="portal-card">
                <div class="portal-code">TN</div>
                <div>
                    <div class="portal-name">
                        Trenggalek Njenggelek
                    </div>
                    <div class="portal-desc">
                        Portal berita lokal
                    </div>
                </div>
            </div>
            """
        )


    with p3:

        st.html(
            """
            <div class="portal-card">
                <div class="portal-code">ST</div>
                <div>
                    <div class="portal-name">
                        Suara Trenggalek
                    </div>
                    <div class="portal-desc">
                        Portal berita lokal
                    </div>
                </div>
            </div>
            """
        )


    # FOOTER
    st.html(
        """
        <footer class="main-footer">

            <div class="footer-line"></div>

            <div class="footer-content">

                <span>
                    <b>PENA</b>
                    · Pengumpulan Fenomena Pendukung
                    Analisis Statistik
                </span>

                <span>
                    Tim Neraca Wilayah dan Analisis Statistik
                    · BPS Kabupaten Trenggalek
                </span>

            </div>

        </footer>
        """
    )

    st.stop()


# ============================================================
# HASIL FENOMENA
# ============================================================

st.html(
    """
    <div class="section-title">
        Hasil Fenomena
    </div>

    <div class="section-description">
        Artikel yang ditemukan berdasarkan kriteria pencarian.
    </div>
    """
)


# ============================================================
# EXPORT
# ============================================================

try:

    excel = to_excel(df)

    st.download_button(
        "Download Excel",
        data=excel,
        file_name=(
            f"PENA_"
            f"{keyword.strip() if keyword.strip() else 'fenomena'}"
            f".xlsx"
        ),
        mime=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        width="content"
    )

except Exception as e:

    st.error(
        "File Excel tidak dapat dibuat."
    )

    st.exception(e)


# ============================================================
# TABEL
# ============================================================

tampil = df[
    [
        "Tanggal",
        "Judul",
        "Penulis",
        "Sumber"
    ]
].copy()


tampil["Tanggal"] = tampil[
    "Tanggal"
].dt.strftime(
    "%d/%m/%Y"
)


st.dataframe(
    tampil,
    use_container_width=True,
    hide_index=True,
    column_config={

        "Tanggal": st.column_config.TextColumn(
            "Tanggal",
            width="small"
        ),

        "Judul": st.column_config.TextColumn(
            "Judul",
            width="large"
        ),

        "Penulis": st.column_config.TextColumn(
            "Penulis",
            width="medium"
        ),

        "Sumber": st.column_config.TextColumn(
            "Portal",
            width="medium"
        )
    }
)


# ============================================================
# ANALISIS
# ============================================================

st.html(
    """
    <div class="analysis-heading">
        Grafik Fenomena
    </div>
    """
)


left, right = st.columns(2)


# ============================================================
# TREN
# ============================================================

with left:

    trend_data = df.dropna(
        subset=["Tanggal"]
    )

    if not trend_data.empty:

        trend = (
            trend_data
            .groupby(
                trend_data["Tanggal"].dt.date
            )
            .size()
            .reset_index(
                name="Jumlah"
            )
        )

        fig = px.area(
            trend,
            x="Tanggal",
            y="Jumlah",
            markers=True
        )

        fig.update_layout(
            title="Tren Artikel",
            height=330,
            margin=dict(
                l=10,
                r=10,
                t=45,
                b=10
            ),
            plot_bgcolor="white",
            paper_bgcolor="white",
            showlegend=False
        )

        st.plotly_chart(
            fig,
            use_container_width=True
        )


# ============================================================
# PORTAL
# ============================================================

with right:

    sumber = (
        df["Sumber"]
        .value_counts()
        .reset_index()
    )

    sumber.columns = [
        "Sumber",
        "Jumlah"
    ]

    fig2 = px.bar(
        sumber,
        x="Jumlah",
        y="Sumber",
        orientation="h"
    )

    fig2.update_layout(
        title="Artikel berdasarkan Portal",
        height=330,
        margin=dict(
            l=10,
            r=10,
            t=45,
            b=10
        ),
        plot_bgcolor="white",
        paper_bgcolor="white",
        showlegend=False
    )

    st.plotly_chart(
        fig2,
        use_container_width=True
    )


# ============================================================
# PREVIEW ARTIKEL
# ============================================================

st.html(
    """
    <div class="analysis-heading">
        Preview Artikel
    </div>
    """
)


pilih = st.selectbox(
    "Pilih artikel",
    df.index,
    format_func=lambda x: df.loc[x, "Judul"],
    label_visibility="collapsed"
)


tanggal_artikel = df.loc[
    pilih,
    "Tanggal"
]


if pd.notna(tanggal_artikel):

    tanggal_text = tanggal_artikel.strftime(
        "%d/%m/%Y"
    )

else:

    tanggal_text = "-"


judul = str(
    df.loc[pilih, "Judul"]
)

sumber = str(
    df.loc[pilih, "Sumber"]
)

penulis = str(
    df.loc[pilih, "Penulis"]
)

isi = str(
    df.loc[pilih, "Isi"]
)


st.html(
    f"""
    <article class="article-card">

        <div class="article-source">
            {sumber}
        </div>

        <div class="article-title">
            {judul}
        </div>

        <div class="article-meta">
            {tanggal_text}
            &nbsp; · &nbsp;
            {penulis}
        </div>

        <div class="article-content">
            {isi}
        </div>

    </article>
    """
)


link = str(
    df.loc[pilih, "Link"]
)


if link.startswith("http"):

    st.link_button(
        "Buka Artikel Asli",
        link,
        width="content"
    )


# ============================================================
# FOOTER
# ============================================================

st.html(
    """
    <footer class="main-footer">

        <div class="footer-line"></div>

        <div class="footer-content">

            <span>
                <b>PENA</b>
                · Pengumpulan Fenomena Pendukung
                Analisis Statistik
            </span>

            <span>
                Tim Neraca Wilayah dan Analisis Statistik
                · BPS Kabupaten Trenggalek
            </span>

        </div>

    </footer>
    """
)