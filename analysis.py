"""Review Pulse - data + computation layer.

Every number shown in the app is computed here from the two real data files:
  - "Reviews CSV sample.csv"  (Play Store reviews: date, rating, review_text)
  - "output.json"             (the analysis output from the review study)
plus the two markdown deliverables (weekly_pulse.md, fee_explainer.md).
Nothing is hardcoded except theme keyword rules, which are shown on the Checks page.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import streamlit as st
from datetime import datetime, timedelta

CSV_PATH = "Reviews CSV sample.csv"
OUTPUT_JSON = "output.json"
PULSE_MD = "weekly_pulse.md"
EXPLAINER_MD = "fee_explainer.md"
HISTORY_JSON = "history.json"

# ---------------------------------------------------------------------------
# Theme classification (deterministic keyword scoring, computed from the CSV).
# Tie-break priority is the order below. Same theme names as output.json.
# ---------------------------------------------------------------------------

THEME_KEYWORDS = {
    "fees": [
        "brokerage", "charge", "fee", "dp charge", "gst", "tax", "deduct",
        "deduction", "expensive", "costly", "pricing", "cost", "rupee", "rs.",
    ],
    "support": [
        "support", "withdraw", "kyc", "customer care", "refund", "payment",
        "upi", "deposit", "money back", "response", "revert", "help",
    ],
    "execution": [
        "stop loss", "target", "order", "execut", "crash", "hang", "slow",
        "bug", "glitch", "freeze", "not working", "loading", "failed", "lag",
    ],
    "praise": [
        "good", "nice", "best", "easy", "love", "awesome", "superb", "great",
        "amazing", "simple", "helpful", "excellent", "perfect", "smooth",
    ],
}

THEME_ORDER = ["fees", "support", "execution", "praise", "other"]

THEME_DISPLAY = {
    "fees": "Fees, brokerage & unexpected charges",
    "support": "Support, withdrawals, payments & KYC",
    "execution": "App performance & order execution",
    "praise": "Appreciation & ease of use",
    "other": "Other / unclassified",
}

FEE_CONFUSED_KEYWORDS = [
    "unclear", "unexpect", "without clear", "without proper", "without information",
    "hidden", "not informed", "beforehand", "no information", "surprise",
    "unknown", "deducted without", "without notif",
]
FEE_HIGH_KEYWORDS = [
    "too much", "high", "expens", "costly", "loot", "robber", "significant",
    "heavy", "increas", "worst",
]


# ---------------------------------------------------------------------------
# Loading + masking
# ---------------------------------------------------------------------------

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE = re.compile(r"(?<!\d)\+?\d[\d\s\-]{8,12}\d(?!\d)")
_HANDLE = re.compile(r"(?<!\w)@\w+")
_TITLE_NAME = re.compile(r"\b(?:Mr|Mrs|Ms|Shri|Smt|Dr)\.?\s+[A-Z][a-zA-Z]+")


def mask_text(text: str) -> str:
    """Best-effort PII masking for display: emails, phone-like numbers,
    social handles, title-prefixed names (Mr/Mrs/Ms/Shri/Smt/Dr)."""
    text = _EMAIL.sub("[email]", text)
    text = _PHONE.sub("[phone]", text)
    text = _HANDLE.sub("[handle]", text)
    text = _TITLE_NAME.sub("[name]", text)
    return text


def classify(text: str, rating: int) -> str:
    tl = text.lower()
    best, best_score = "other", 0
    for theme in THEME_ORDER:
        if theme == "other":
            continue
        if theme == "praise" and rating < 4:
            continue
        score = sum(tl.count(kw) for kw in THEME_KEYWORDS[theme])
        if score > best_score:
            best, best_score = theme, score
    return best


@st.cache_data(show_spinner=False)
def _parse_reviews(source_text: str) -> list[dict]:
    reader = csv.DictReader(io.StringIO(source_text))
    required = ("date", "rating", "review_text")
    missing = [c for c in required if c not in (reader.fieldnames or [])]
    if missing:
        raise ValueError("missing column(s): " + ", ".join(missing))
    rows = []
    for i, r in enumerate(reader, start=2):
        try:
            rating = int(r["rating"])
            when = datetime.strptime(r["date"], "%Y-%m-%d %H:%M:%S")
        except ValueError as e:
            raise ValueError(f"row {i}: {e}") from e
        text = r["review_text"]
        rows.append({
            "date": when,
            "rating": rating,
            "text": text,
            "masked": mask_text(text),
            "theme": classify(text, rating),
        })
    if not rows:
        raise ValueError("the file has headers but no review rows")
    return rows


def uploaded_csv_text() -> str | None:
    """CSV text currently uploaded in the session, if any."""
    try:
        data = st.session_state.get("uploaded_csv")
    except Exception:
        return None
    if data is None:
        return None
    if isinstance(data, bytes):
        return data.decode("utf-8-sig", errors="replace")
    return str(data)


def clear_upload() -> None:
    """Drop any uploaded CSV and fall back to the bundled sample."""
    st.session_state.pop("uploaded_csv", None)
    st.session_state.pop("uploaded_csv_name", None)


def set_uploaded_csv(data: bytes, name: str = "uploaded CSV") -> str | None:
    """Store an uploaded reviews CSV in the session.

    Returns None on success, or an error message if the CSV cannot be read
    (in which case nothing is stored and the previous data source stays active).
    """
    text = data.decode("utf-8-sig", errors="replace") if isinstance(data, bytes) else str(data)
    try:
        _parse_reviews(text)
    except Exception as e:
        return (f"Could not read `{name}` — {e}. "
                "Required columns: `date` (YYYY-MM-DD HH:MM:SS), `rating`, `review_text`.")
    st.session_state["uploaded_csv"] = data
    st.session_state["uploaded_csv_name"] = name
    return None


def active_csv_label() -> tuple[str, str]:
    """Return (source_kind, label) for the CSV currently being analysed."""
    if st.session_state.get("uploaded_csv") is not None:
        name = st.session_state.get("uploaded_csv_name", "uploaded CSV")
        return "uploaded", name
    return "bundled sample", os.path.basename(CSV_PATH)


def load_reviews() -> list[dict]:
    """Reviews from the uploaded CSV if one is loaded, else the bundled sample."""
    text = uploaded_csv_text()
    if text is not None:
        return _parse_reviews(text)
    with open(CSV_PATH, encoding="utf-8-sig") as f:
        return _parse_reviews(f.read())


@st.cache_data(show_spinner=False)
def load_output() -> dict:
    with open(OUTPUT_JSON, encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(show_spinner=False)
def load_pulse_md() -> str:
    with open(PULSE_MD, encoding="utf-8") as f:
        return f.read().replace("\\*", "*")


@st.cache_data(show_spinner=False)
def load_explainer_md() -> str:
    with open(EXPLAINER_MD, encoding="utf-8") as f:
        return f.read().replace("\\*", "*").replace("\\.", ".")


# ---------------------------------------------------------------------------
# Aggregations
# ---------------------------------------------------------------------------

def dataset_stats() -> dict:
    rows = load_reviews()
    dates = [r["date"] for r in rows]
    avg = sum(r["rating"] for r in rows) / len(rows)
    return {
        "count": len(rows),
        "start": min(dates).strftime("%d %b %Y"),
        "end": max(dates).strftime("%d %b %Y"),
        "max_date": max(dates),
        "avg_rating": round(avg, 2),
    }


def theme_stats() -> list[dict]:
    rows = load_reviews()
    total = len(rows)
    out = []
    for theme in THEME_ORDER:
        sub = [r for r in rows if r["theme"] == theme]
        if not sub:
            continue
        low = [r for r in sub if r["rating"] <= 2]
        out.append({
            "key": theme,
            "name": THEME_DISPLAY[theme],
            "reviews": len(sub),
            "share": round(100 * len(sub) / total, 1),
            "avg_rating": round(sum(r["rating"] for r in sub) / len(sub), 2),
            "low_stars": len(low),
            "problem_rate": round(100 * len(low) / len(sub), 1),
        })
    out.sort(key=lambda d: d["low_stars"], reverse=True)
    return out


def low_star_trend() -> dict:
    """1-2 star volume: last 28 days vs the 28 days before that."""
    rows = load_reviews()
    end = dataset_stats()["max_date"]
    recent = [r for r in rows if r["date"] > end - timedelta(days=28)]
    prior = [r for r in rows if end - timedelta(days=56) < r["date"] <= end - timedelta(days=28)]
    rec = sum(1 for r in recent if r["rating"] <= 2)
    pri = sum(1 for r in prior if r["rating"] <= 2)
    pct = round(100 * (rec - pri) / pri, 1) if pri else 0.0
    if pct > 2:
        arrow, verdict = "▲", "worsening"
    elif pct < -2:
        arrow, verdict = "▼", "improving"
    else:
        arrow, verdict = "▬", "steady"
    return {"recent": rec, "prior": pri, "pct": pct, "arrow": arrow, "verdict": verdict}


def weekly_series(theme_key: str | None = None) -> list[dict]:
    rows = load_reviews()
    weeks: dict[str, int] = {}
    for r in rows:
        if theme_key and r["theme"] != theme_key:
            continue
        wk = r["date"].strftime("%G-W%V")
        weeks[wk] = weeks.get(wk, 0) + 1
    return [{"week": w, "reviews": c} for w, c in sorted(weeks.items())]


def representative_quote(theme_key: str) -> str:
    """Deterministic pick straight from the CSV (never rewritten):
    first 1-2 star review of the theme, 40-220 chars; else first of any
    rating in that length band; else the first non-empty review."""
    rows = [r for r in load_reviews() if r["theme"] == theme_key]
    band = lambda r: 40 <= len(r["text"]) <= 220  # noqa: E731
    for cond in (lambda r: r["rating"] <= 2 and band(r), band):
        for r in rows:
            if cond(r):
                return r["text"]
    for r in rows:
        if r["text"].strip():
            return r["text"]
    return ""


def fee_panel() -> dict:
    rows = load_reviews()
    fee_rows = [r for r in rows if any(kw in r["text"].lower() for kw in THEME_KEYWORDS["fees"])]
    confused = [r for r in fee_rows if any(kw in r["text"].lower() for kw in FEE_CONFUSED_KEYWORDS)]
    high = [r for r in fee_rows if any(kw in r["text"].lower() for kw in FEE_HIGH_KEYWORDS)]
    top_confusion = ""
    for r in confused:
        if 40 <= len(r["text"]) <= 220:
            top_confusion = r["text"]
            break
    if not top_confusion and confused:
        top_confusion = confused[0]["text"]
    return {
        "fee_mentions": len(fee_rows),
        "confused": len(confused),
        "high": len(high),
        "top_confusion": top_confusion,
    }


def explore(theme_key: str, search: str, star_filter: list[int], sort: str,
            page: int, per_page: int = 20) -> tuple[list[dict], int]:
    rows = [r for r in load_reviews() if r["theme"] == theme_key]
    if star_filter:
        rows = [r for r in rows if r["rating"] in star_filter]
    if search.strip():
        rows = [r for r in rows if search.lower() in r["text"].lower()]
    if sort == "Newest":
        rows.sort(key=lambda r: r["date"], reverse=True)
    elif sort == "Oldest":
        rows.sort(key=lambda r: r["date"])
    elif sort == "Highest rating":
        rows.sort(key=lambda r: r["rating"], reverse=True)
    else:
        rows.sort(key=lambda r: r["rating"])
    pages = max(1, -(-len(rows) // per_page))
    page = min(page, pages)
    return rows[(page - 1) * per_page: page * per_page], pages


# ---------------------------------------------------------------------------
# Publish payload (identical format to the original working flow)
# ---------------------------------------------------------------------------

def build_doc_entry(output: dict) -> str:
    parts = [
        "Date: " + str(output.get("date", "")),
        "Top themes: " + ", ".join(output.get("top_themes", [])),
        "",
        "Weekly pulse:",
        str(output.get("weekly_pulse", "")),
        "",
        "Identified fee issue:",
        str(output.get("identified_fee_issue", "")),
        "",
        "Fee explanation:",
    ]
    parts += ["- " + str(b) for b in output.get("explanation_bullets", [])]
    parts += ["", "Sources:"] + ["- " + str(u) for u in output.get("source_links", [])]
    return "\n".join(parts)


def build_payload() -> tuple[dict, str]:
    output = load_output()
    payload = dict(output)
    doc_entry = build_doc_entry(output)
    payload["doc_entry"] = doc_entry
    return payload, doc_entry


def fingerprint(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def get_webhook_url() -> tuple[str, str]:
    try:
        url = str(st.secrets["N8N_WEBHOOK_URL"]).strip()
        if url:
            return url, "st.secrets"
    except Exception:
        pass
    url = os.environ.get("N8N_WEBHOOK", "").strip()
    return url, ("environment variable N8N_WEBHOOK" if url else "not configured")


# Default MCP endpoint for the "Review Pulse (MCP tools)" workflow (an n8n MCP
# Server Trigger). Kept OUT of source so no private instance hostname is
# committed — supply it via st.secrets["N8N_MCP_URL"] or env N8N_MCP_URL.
# If neither is set, publishing simply falls back to the webhook path.
DEFAULT_MCP_URL = ""


def get_mcp_url() -> tuple[str, str]:
    try:
        url = str(st.secrets["N8N_MCP_URL"]).strip()
        if url:
            return url, "st.secrets"
    except Exception:
        pass
    url = os.environ.get("N8N_MCP_URL", "").strip()
    if url:
        return url, "environment variable N8N_MCP_URL"
    return DEFAULT_MCP_URL, ("built-in default" if DEFAULT_MCP_URL else "not configured")


def build_email_html(output: dict) -> str:
    """Branded HTML email for the create_email_draft MCP tool.
    Same layout the webhook workflow's 'Format Email as HTML' node produces."""

    def esc(s) -> str:
        return (str(s if s is not None else "")
                .replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;").replace('"', "&quot;"))

    def br(s) -> str:
        return esc(s).replace("\n", "<br>")

    theme_items = "".join(
        f'<li style="margin:4px 0;font-size:14px">{esc(t)}</li>'
        for t in output.get("top_themes", []))
    bullet_items = "".join(
        f'<li style="margin:6px 0;font-size:14px">{esc(b)}</li>'
        for b in output.get("explanation_bullets", []))
    source_links = "<br>".join(
        f'<a href="{esc(u)}" style="color:#0066cc;text-decoration:none">{esc(u)}</a>'
        for u in output.get("source_links", []))

    return (
        '<div style="max-width:600px;margin:0 auto;font-family:Arial,Helvetica,sans-serif;color:#1f1f1f;line-height:1.5">'
        '<div style="background:#00b386;padding:18px 22px;border-radius:8px 8px 0 0">'
        '<h1 style="margin:0;color:#ffffff;font-size:18px">Weekly Product Pulse</h1>'
        f'<p style="margin:6px 0 0;color:#e3f7f0;font-size:13px">{esc(output.get("date", ""))}</p>'
        '</div>'
        '<div style="border:1px solid #e0e0e0;border-top:none;padding:22px;border-radius:0 0 8px 8px">'
        '<h2 style="font-size:15px;margin:0 0 8px;color:#00664f">Top themes</h2>'
        f'<ul style="margin:0 0 18px;padding-left:18px">{theme_items}</ul>'
        '<h2 style="font-size:15px;margin:0 0 8px;color:#00664f">Pulse summary</h2>'
        f'<p style="margin:0 0 18px;font-size:14px">{br(output.get("weekly_pulse", ""))}</p>'
        '<h2 style="font-size:15px;margin:0 0 8px;color:#00664f">Fee clarification for support</h2>'
        f'<ul style="margin:0 0 18px;padding-left:18px">{bullet_items}</ul>'
        '<h2 style="font-size:15px;margin:0 0 8px;color:#00664f">Sources</h2>'
        f'<p style="margin:0;font-size:13px">{source_links}</p>'
        '</div>'
        '<p style="text-align:center;color:#999;font-size:12px;margin-top:14px">'
        'Approval-gated delivery via n8n - draft only, not sent automatically.</p>'
        '</div>')


# ---------------------------------------------------------------------------
# History (local JSON file)
# ---------------------------------------------------------------------------

def read_history() -> list[dict]:
    try:
        with open(HISTORY_JSON, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return []


def append_history(action: str, fp: str, result: str) -> None:
    hist = read_history()
    hist.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "action": action,
        "fingerprint": fp,
        "result": result,
    })
    with open(HISTORY_JSON, "w", encoding="utf-8") as f:
        json.dump(hist, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Automated checks (all computed from the real files)
# ---------------------------------------------------------------------------

FORBIDDEN_SEND_TOKENS = ["smtplib", "mail.gmail.com/v1/users/me/messages/send", "sendmail"]


def run_checks() -> list[dict]:
    output = load_output()
    rows = load_reviews()
    texts = [r["text"] for r in rows]
    pulse = output.get("weekly_pulse", "")
    bullets = output.get("explanation_bullets", [])
    links = output.get("source_links", [])
    subject = output.get("email_subject", "")
    explainer = load_explainer_md()
    themes = output.get("top_themes", [])

    quotes = re.findall(r'"([^"]{10,400})"', pulse)
    quotes_found = [q for q in quotes if any(q in t for t in texts)]

    fee_issue = output.get("identified_fee_issue", "").lower()
    explainer_text = " ".join(bullets).lower() + explainer.lower()
    topic_token = "brokerage" if "brokerage" in fee_issue else (fee_issue.split()[0] if fee_issue else "")
    topic_match = bool(topic_token) and topic_token in explainer_text

    try:
        here = os.path.abspath(__file__)
        approve_src = ""
        views_src = ""
        approve_path = os.path.join(os.path.dirname(here), "views", "approve.py")
        if os.path.exists(approve_path):
            with open(approve_path, encoding="utf-8") as f:
                approve_src = f.read()
        mcp_src = ""
        mcp_path = os.path.join(os.path.dirname(here), "mcp_client.py")
        if os.path.exists(mcp_path):
            with open(mcp_path, encoding="utf-8") as f:
                mcp_src = f.read()
        with open(here, encoding="utf-8") as f:
            # Drop the lines that define the forbidden-token list itself,
            # otherwise this file would always match its own patterns.
            views_src = "".join(
                ln for ln in f if "FORBIDDEN_SEND_TOKENS" not in ln
            )
        src = approve_src + views_src + mcp_src
        no_send = not any(tok in src for tok in FORBIDDEN_SEND_TOKENS)
    except OSError:
        no_send = False

    return [
        {"name": "Themes ≤ 5", "passed": len(themes) <= 5, "detail": f"{len(themes)} themes in output.json"},
        {"name": "Top 3 themes identified", "passed": len(themes) >= 3, "detail": "top_themes has " + str(len(themes))},
        {"name": "3 quotes verbatim in CSV", "passed": len(quotes_found) >= 3 and len(quotes) >= 3,
         "detail": f"{len(quotes_found)}/{len(quotes)} pulse quotes found verbatim in the CSV"},
        {"name": "Weekly pulse ≤ 250 words", "passed": len(pulse.split()) <= 250, "detail": f"{len(pulse.split())} words"},
        {"name": "Fee bullets ≤ 6", "passed": len(bullets) <= 6, "detail": f"{len(bullets)} bullets"},
        {"name": "Exactly 2 source links", "passed": len(links) == 2, "detail": f"{len(links)} links"},
        {"name": '"Last checked" present', "passed": "last checked" in explainer.lower(), "detail": "in fee_explainer.md"},
        {"name": "Explainer matches fee issue", "passed": topic_match, "detail": f"token '{topic_token}' matched in explainer"},
        {"name": "Email subject format", "passed": bool(re.match(r"^Weekly Product Pulse \+ Customer Clarification \u2014 \d{4}-\d{2}-\d{2}$", subject)),
         "detail": subject or "missing"},
        {"name": "No auto-send (draft only)", "passed": no_send, "detail": "app source contains no email-send call"},
    ]
