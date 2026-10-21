import streamlit as st

import analysis
import styles

out = analysis.load_output()
pulse = out.get("weekly_pulse", "")
words = len(pulse.split())

styles.page_header("Weekly Pulse", "Internal weekly summary (from output.json) — max 250 words.")

w1, w2 = st.columns([1, 5])
with w1:
    ok = words <= 250
    st.markdown(styles.card(
        f'<div class="rp-kpi-label">Word count</div>'
        f'<div class="rp-kpi-value" style="color:{"#00785C" if ok else "#B42318"}">{words}</div>'
        f'<div class="rp-sub">limit 250 · {"✅ within limit" if ok else "❌ over limit"}</div>'
    ), unsafe_allow_html=True)
with w2:
    st.download_button("Download weekly_pulse.md", data=analysis.load_pulse_md(),
                       file_name="weekly_pulse.md", mime="text/markdown")

st.markdown(styles.card(analysis.load_pulse_md()), unsafe_allow_html=True)
