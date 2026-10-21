import streamlit as st

import analysis
import styles

hist = analysis.read_history()

styles.page_header("History", "Every approve/reject from this app (stored in local history.json).")

if not hist:
    st.info("No actions yet — approve or reject something on the Approve & Publish page.")
else:
    rows = [{
        "Timestamp": h["timestamp"],
        "Action": h["action"].title(),
        "Fingerprint": h["fingerprint"][:16] + "…",
        "Result": h["result"],
    } for h in reversed(hist)]
    st.table(rows)
    st.caption(f"{len(hist)} action(s) recorded locally in history.json.")
