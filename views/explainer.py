import re

import streamlit as st

import analysis
import styles

out = analysis.load_output()
explainer_raw = analysis.load_explainer_md()
bullets = out.get("explanation_bullets", [])
links = out.get("source_links", [])

styles.page_header("Fee Explainer", "Customer-facing clarification of the fee issue found in the reviews "
                                   "(brokerage + extra per-order charges).")

m = re.search(r"Last checked:.*", explainer_raw)
last_checked = m.group(0).strip() if m else "Last checked: —"

st.markdown(styles.card(
    '<div class="rp-kpi-label">The misunderstanding (from the reviews)</div>'
    f'<div style="color:#344054;font-size:.92rem;margin-top:6px">{out.get("identified_fee_issue", "")}</div>'
), unsafe_allow_html=True)

st.markdown("#### Explainer")
for b in bullets:
    st.markdown(f'<div class="rp-quote" style="margin:6px 0">• {b}</div>', unsafe_allow_html=True)

st.markdown("#### Sources")
for u in links:
    st.markdown(f"- [{u}]({u})")

st.caption(last_checked)
st.download_button("Download fee_explainer.md", data=analysis.load_explainer_md(),
                   file_name="fee_explainer.md", mime="text/markdown")
