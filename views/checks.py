import streamlit as st

import analysis
import styles

checks = analysis.run_checks()
passed = sum(1 for c in checks if c["passed"])

styles.page_header("Checks", "Automated validation of the deliverables — every check computed in code.")

st.markdown(styles.card(
    f'<div class="rp-kpi-label">Result</div>'
    f'<div class="rp-kpi-value" style="color:{"#00785C" if passed == len(checks) else "#B42318"}">{passed}/{len(checks)} passed</div>'
), unsafe_allow_html=True)

for c in checks:
    icon = "✅" if c["passed"] else "❌"
    tag = '<span class="rp-tag rp-tag-ok">PASS</span>' if c["passed"] else '<span class="rp-tag rp-tag-bad">FAIL</span>'
    st.markdown(
        f'<div class="rp-card" style="padding:12px 16px;margin:4px 0">'
        f'{icon} <b>{c["name"]}</b> {tag}'
        f'<div class="rp-sub" style="margin-top:4px">{c["detail"]}</div></div>',
        unsafe_allow_html=True,
    )

st.caption("Theme keyword rules and masking patterns live in analysis.py (THEME_KEYWORDS / mask_text).")
