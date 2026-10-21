"""Review Pulse - all app styling lives here (single CSS injection)."""

ACCENT = "#00B386"

CSS = """
<style>
:root { --accent: #00B386; }

/* Light, airy page */
.stApp { background: #F6F8F9; }

/* Dark sidebar with brand */
[data-testid="stSidebar"] {
    background: #0E1621;
}
[data-testid="stSidebar"] * { color: #E6EDF3; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: #9FB0BD; }

.rp-brand {
    font-size: 1.35rem; font-weight: 700; color: #FFFFFF !important;
    padding: 4px 0 0 2px; letter-spacing: .3px;
}
.rp-brand small {
    display:block; font-size: .7rem; font-weight: 400; color: #7D8FA0 !important;
    letter-spacing: .6px; text-transform: uppercase;
}

/* Rounded white cards */
.rp-card {
    background: #FFFFFF;
    border: 1px solid #E4E9ED;
    border-radius: 16px;
    padding: 20px 22px;
    margin: 6px 0 14px 0;
    box-shadow: 0 1px 3px rgba(16,24,40,.05);
}
.rp-card h3, .rp-card h4 { margin: 0 0 8px 0; color: #101828; }
.rp-kpi-value { font-size: 1.7rem; font-weight: 700; color: #101828; line-height: 1.1; }
.rp-kpi-label { font-size: .78rem; color: #667085; text-transform: uppercase; letter-spacing: .6px; }
.rp-sub { color: #667085; font-size: .85rem; }

.rp-tag {
    display: inline-block; background: #E6F7F2; color: #00785C;
    border-radius: 999px; padding: 2px 12px; font-size: .78rem; font-weight: 600;
    margin: 2px 4px 2px 0;
}
.rp-tag-warn { background: #FFF4E5; color: #B54708; }
.rp-tag-bad  { background: #FEECEC; color: #B42318; }
.rp-tag-ok   { background: #E6F7F2; color: #00785C; }

.rp-quote {
    border-left: 3px solid var(--accent);
    background: #FAFBFC;
    border-radius: 0 10px 10px 0;
    padding: 10px 14px; color: #344054; font-size: .92rem;
}

.rp-note { font-size: .82rem; color: #667085; }

/* Bar rows ("Where the pain is") */
.rp-bar-row { display: flex; align-items: center; gap: 10px; margin: 6px 0; }
.rp-bar-label { width: 260px; font-size: .85rem; color: #344054; }
.rp-bar-track { flex: 1; background: #EDF1F3; border-radius: 999px; height: 14px; }
.rp-bar-fill { background: var(--accent); border-radius: 999px; height: 14px; }
.rp-bar-count { width: 64px; text-align: right; font-size: .85rem; color: #101828; font-weight: 600; }

/* Tables */
[data-testid="stTable"] table { border-radius: 12px; overflow: hidden; }

/* Buttons */
.stButton > button[kind="primary"], .stDownloadButton > button {
    border-radius: 10px; background: var(--accent); border: none; color: white; font-weight: 600;
}
.stButton > button[kind="secondary"] { border-radius: 10px; }

.rp-h1 { font-size: 1.5rem; font-weight: 700; color: #101828; margin: 0 0 2px 0; }
.rp-h1sub { color: #667085; font-size: .9rem; margin: 0 0 18px 0; }
</style>
"""


def inject_css() -> None:
    import streamlit as st
    st.markdown(CSS, unsafe_allow_html=True)


def card(inner: str = "") -> str:
    """Wrap html content in a card div."""
    return f'<div class="rp-card">{inner}</div>'


def page_header(title: str, subtitle: str = "") -> None:
    import streamlit as st
    sub = f'<p class="rp-h1sub">{subtitle}</p>' if subtitle else ""
    st.markdown(f'<div class="rp-h1">{title}</div>{sub}', unsafe_allow_html=True)
