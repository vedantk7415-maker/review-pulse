"""Review Pulse — multi-page Streamlit app.

Shell only: styling + navigation. All logic lives in analysis.py and views/.
Run with:  streamlit run app.py
"""

import streamlit as st

import styles

st.set_page_config(
    page_title="Review Pulse",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

styles.inject_css()

home = st.Page("views/home.py", title="Home", icon="🏠", default=True)
insights = st.Page("views/insights.py", title="Insights", icon="📈")
pulse = st.Page("views/pulse.py", title="Weekly Pulse", icon="📰")
explainer = st.Page("views/explainer.py", title="Fee Explainer", icon="💰")
approve = st.Page("views/approve.py", title="Approve & Publish", icon="✅")
history = st.Page("views/history.py", title="History", icon="🕘")
checks = st.Page("views/checks.py", title="Checks", icon="🛠")

nav = st.navigation([home, insights, pulse, explainer, approve, history, checks])

with st.sidebar:
    st.markdown(
        '<div class="rp-brand">Review Pulse'
        '<small>Groww reviews · weekly product pulse</small></div>',
        unsafe_allow_html=True,
    )

nav.run()
