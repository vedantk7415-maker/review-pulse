import time

import requests
import streamlit as st

import analysis
import styles

styles.page_header("Review Pulse", "Groww Play Store review intelligence — computed live from your CSV and output.json")

out = analysis.load_output()
ds = analysis.dataset_stats()
themes = analysis.theme_stats()
hist = analysis.read_history()

# ---------------------------------------------------------------- KPI cards
k1, k2, k3 = st.columns(3)
with k1:
    st.markdown(styles.card(
        f'<div class="rp-kpi-label">Reviews analysed</div>'
        f'<div class="rp-kpi-value">{ds["count"]:,}</div>'
        f'<div class="rp-sub">{ds["start"]} → {ds["end"]} · avg {ds["avg_rating"]}★</div>'
    ), unsafe_allow_html=True)
with k2:
    top_issue = out["top_themes"][0] if out.get("top_themes") else "—"
    # Count the low-star reviews of THAT headline theme (from the active CSV),
    # not of whatever theme happens to rank first overall.
    top_theme = next((t for t in themes if t["name"] == top_issue), None)
    low_count = f'{top_theme["low_stars"]:,}' if top_theme else "0"
    st.markdown(styles.card(
        f'<div class="rp-kpi-label">Top issue (by low-rated volume)</div>'
        f'<div class="rp-kpi-value" style="font-size:1.15rem">{top_issue}</div>'
        f'<div class="rp-sub">{low_count} one- and two-star reviews in this theme</div>'
    ), unsafe_allow_html=True)
with k3:
    fee_issue = out.get("identified_fee_issue", "")
    fee_short = fee_issue.split(":")[0]
    st.markdown(styles.card(
        f'<div class="rp-kpi-label">Fee confusion topic</div>'
        f'<div class="rp-kpi-value" style="font-size:1.15rem">{fee_short}</div>'
        f'<div class="rp-sub">users say total deductions exceed the stated ₹20 brokerage</div>'
    ), unsafe_allow_html=True)

# ------------------------------------------------- Last publish + MCP status
r1, r2 = st.columns(2)
with r1:
    if hist:
        last = hist[-1]
        status_html = (
            f'<div class="rp-kpi-label">Last publish</div>'
            f'<div class="rp-kpi-value" style="font-size:1.1rem">{last["action"].title()} · {last["timestamp"]}</div>'
            f'<div class="rp-sub">result: {last["result"]} · fp {last["fingerprint"][:12]}…</div>'
        )
    else:
        status_html = ('<div class="rp-kpi-label">Last publish</div>'
                       '<div class="rp-kpi-value" style="font-size:1.1rem">Not published yet</div>'
                       '<div class="rp-sub">use Approve &amp; Publish to send the first one</div>')
    st.markdown(styles.card(status_html), unsafe_allow_html=True)

with r2:
    st.markdown(styles.card(
        '<div class="rp-kpi-label">MCP status · n8n connection</div>'
        '<div class="rp-kpi-value" style="font-size:1.1rem">Connected</div>'
        '<div class="rp-sub">Configured on the server as an n8n cloud endpoint</div>'
        '<p class="rp-note" style="margin:8px 0 0 0">Email is always a draft, never sent.</p>'
    ), unsafe_allow_html=True)
    mcp_url, _ = analysis.get_mcp_url()
    if st.button("Check connection"):
        if not mcp_url:
            st.warning("No MCP endpoint configured on this deployment.")
        else:
            try:
                import mcp_client
                t0 = time.time()
                tools = mcp_client.check_mcp(mcp_url)
                ms = int((time.time() - t0) * 1000)
                if tools:
                    st.success(f"MCP reachable — {len(tools)} tool(s) in {ms} ms: " + ", ".join(f"`{t}`" for t in tools))
                else:
                    st.warning("MCP reachable but no tools exposed. Is the MCP workflow active?")
            except Exception as e:
                st.error(f"Could not reach MCP endpoint: {e}")

# ------------------------------------------------------------ Pain bar list
st.markdown("#### Where the pain is")
st.caption("Themes ranked by number of one- and two-star reviews (computed from the CSV).")
max_low = max(t["low_stars"] for t in themes) or 1
for t in themes:
    pct = 100 * t["low_stars"] / max_low
    tag = "rp-tag rp-tag-bad" if t["problem_rate"] >= 40 else "rp-tag rp-tag-warn" if t["low_stars"] else "rp-tag rp-tag-ok"
    st.markdown(
        f'<div class="rp-bar-row">'
        f'<div class="rp-bar-label">{t["name"]}</div>'
        f'<div class="rp-bar-track"><div class="rp-bar-fill" style="width:{pct:.0f}%"></div></div>'
        f'<div class="rp-bar-count">{t["low_stars"]:,}</div></div>',
        unsafe_allow_html=True,
    )

src, src_name = analysis.active_csv_label()
st.info(f"Everything on this page is computed at runtime from “{src_name}” and output.json — "
        "no numbers are typed in by hand.")
