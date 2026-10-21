import pandas as pd
import streamlit as st

import analysis
import styles

out = analysis.load_output()
themes = analysis.theme_stats()
trend = analysis.low_star_trend()

styles.page_header("Insights", "Every figure below is computed in code from the reviews CSV.")

st.caption("**Ranking rule:** themes are ranked by volume of 1–2★ reviews (problem rate = share of a theme's "
           "reviews that are 1–2★). Top 3 match the study's identified themes.")

# --------------------------------------------------------------- Theme table
top3 = set(out.get("top_themes", []))
rows = []
for i, t in enumerate(themes, 1):
    rows.append({
        "#": i,
        "Theme": ("🏆 " if t["name"] in top3 else "") + t["name"],
        "Reviews": f'{t["reviews"]:,}',
        "Share": f'{t["share"]}%',
        "Avg ★": f'{t["avg_rating"]}',
        "1–2★": f'{t["low_stars"]:,}',
        "Problem rate": f'{t["problem_rate"]}%',
    })
st.table(rows)

t1, t2, t3 = st.columns(3)
with t1:
    st.markdown(styles.card(
        f'<div class="rp-kpi-label">1–2★ last 4 weeks</div>'
        f'<div class="rp-kpi-value">{trend["recent"]}</div>'
        f'<div class="rp-sub">vs {trend["prior"]} in previous 4 weeks</div>'
    ), unsafe_allow_html=True)
with t2:
    color = "#B42318" if trend["verdict"] == "worsening" else "#00785C" if trend["verdict"] == "improving" else "#667085"
    st.markdown(styles.card(
        f'<div class="rp-kpi-label">Trend</div>'
        f'<div class="rp-kpi-value" style="color:{color}">{trend["arrow"]} {abs(trend["pct"])}%</div>'
        f'<div class="rp-sub">{trend["verdict"]} (last 4 weeks vs previous 4)</div>'
    ), unsafe_allow_html=True)
with t3:
    fp = analysis.fee_panel()
    st.markdown(styles.card(
        f'<div class="rp-kpi-label">Reviews mentioning fees</div>'
        f'<div class="rp-kpi-value">{fp["fee_mentions"]:,}</div>'
        f'<div class="rp-sub">of {analysis.dataset_stats()["count"]:,} total</div>'
    ), unsafe_allow_html=True)

# -------------------------------------------------- Representative quotes
st.markdown("#### Representative quote per theme")
st.caption("Picked deterministically by code straight from the CSV (first 1–2★ review of 40–220 characters; "
           "never rewritten). Emails, phone numbers and handles are masked.")
for t in themes:
    q = analysis.representative_quote(t["key"])
    st.markdown(
        f'<div class="rp-card"><h4 style="margin:0 0 6px 0;font-size:.95rem">{t["name"]}</h4>'
        f'<div class="rp-quote">“{analysis.mask_text(q)}”</div></div>',
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------- Fee issue panel
st.markdown("#### Fee issue panel")
f1, f2, f3 = st.columns(3)
with f1:
    st.markdown(styles.card(
        f'<div class="rp-kpi-label">Mention a fee/charge</div>'
        f'<div class="rp-kpi-value">{fp["fee_mentions"]:,}</div>'
        f'<div class="rp-sub">keyword match on fee/brokerage/charge/tax/deduct</div>'
    ), unsafe_allow_html=True)
with f2:
    st.markdown(styles.card(
        f'<div class="rp-kpi-label">“Charges are high”</div>'
        f'<div class="rp-kpi-value">{fp["high"]:,}</div>'
        f'<div class="rp-sub">reviews saying charges are too high/expensive</div>'
    ), unsafe_allow_html=True)
with f3:
    st.markdown(styles.card(
        f'<div class="rp-kpi-label">Confused about a charge</div>'
        f'<div class="rp-kpi-value">{fp["confused"]:,}</div>'
        f'<div class="rp-sub">unclear / unexpected / “deducted without information”</div>'
    ), unsafe_allow_html=True)

fee_issue = out.get("identified_fee_issue", "")
st.markdown(styles.card(
    f'<div class="rp-kpi-label">Top confusion (from output.json)</div>'
    f'<div style="color:#344054;font-size:.92rem;margin:6px 0 10px 0">{fee_issue}</div>'
    f'<div class="rp-quote">“{analysis.mask_text(fp["top_confusion"])}”</div>'
), unsafe_allow_html=True)

# --------------------------------------------------------- Review explorer
st.markdown("#### Read the reviews")
theme_keys = [t["key"] for t in themes]
labels = {t["name"]: t["key"] for t in themes}
tabs = st.tabs([f'{t["name"]} ({t["reviews"]:,})' for t in themes])

for tab, t in zip(tabs, themes):
    with tab:
        c1, c2, c3 = st.columns([3, 2, 2])
        with c1:
            search = st.text_input("Text search", key=f"search_{t['key']}")
        with c2:
            star = st.radio("Stars", ["All", "1–2★", "3★", "4–5★"], horizontal=True, key=f"star_{t['key']}")
        with c3:
            sort = st.selectbox("Sort", ["Newest", "Oldest", "Highest rating", "Lowest rating"], key=f"sort_{t['key']}")
        star_map = {"All": [], "1–2★": [1, 2], "3★": [3], "4–5★": [4, 5]}
        if "page" not in st.session_state:
            st.session_state.page = {}
        page = st.session_state.page.get(t["key"], 1)
        items, pages = analysis.explore(t["key"], search, star_map[star], sort, page)
        st.caption(f"Page {min(page, pages)} of {pages} · {len(items)} shown")
        for r in items:
            st.markdown(
                f'<div class="rp-card" style="padding:12px 16px;margin:4px 0">'
                f'<span class="rp-tag">{"★" * r["rating"]}{"☆" * (5 - r["rating"])}</span>'
                f'<span class="rp-sub">{r["date"].strftime("%d %b %Y")}</span>'
                f'<div style="color:#344054;font-size:.9rem;margin-top:6px">{r["masked"]}</div></div>',
                unsafe_allow_html=True,
            )
        pc1, pc2 = st.columns([1, 1])
        with pc1:
            if st.button("← Previous", key=f"prev_{t['key']}", disabled=page <= 1):
                st.session_state.page[t["key"]] = max(1, page - 1)
                st.rerun()
        with pc2:
            if st.button("Next →", key=f"next_{t['key']}", disabled=page >= pages):
                st.session_state.page[t["key"]] = page + 1
                st.rerun()

        series = analysis.weekly_series(t["key"])
        if series:
            df = pd.DataFrame(series)
            st.caption("Reviews per week for this theme")
            st.bar_chart(df.set_index("week"), height=200)
