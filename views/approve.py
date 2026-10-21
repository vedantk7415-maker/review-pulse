import requests
import streamlit as st

import analysis
import styles

styles.page_header("Approve & Publish",
                   "Nothing leaves this app until you type APPROVE. The email is a Gmail draft — never auto-sent.")

# ------------------------------------------------------------- Data source
# One control, applied immediately: pick a CSV and it is analysed right away.
# Remove the file (click its X) to go back to the bundled sample.
st.markdown("#### Data source")
up = st.file_uploader(
    "Upload reviews CSV",
    type=["csv"],
    key="approve_csv",
    help="Optional. Columns: date (YYYY-MM-DD HH:MM:SS), rating, review_text. "
         "Leave empty to analyse the bundled Reviews CSV sample.csv.",
)
if up is None:
    if st.session_state.get("uploaded_csv") is not None:
        analysis.clear_upload()
else:
    data = up.getvalue()
    if st.session_state.get("uploaded_csv") != data:
        err = analysis.set_uploaded_csv(data, up.name)
        if err:
            st.error(err)

src, src_name = analysis.active_csv_label()
try:
    n_reviews = len(analysis.load_reviews())
except Exception as e:
    n_reviews = None
    st.error(f"Could not read `{src_name}` — {e}")
suffix = "your upload" if src == "uploaded" else "bundled sample"
st.caption(f"Analysing {n_reviews if n_reviews is not None else '?'} reviews "
           f"from {src_name} ({suffix}).")
st.divider()

payload, doc_entry = analysis.build_payload()
checks = analysis.run_checks()
passed = sum(1 for c in checks if c["passed"])
total = len(checks)

left, right = st.columns([3, 2], gap="large")

# ------------------------------------------------------------------ Preview
with left:
    st.markdown("#### Preview — appended to the Google Doc")
    st.text_area("doc_entry", value=doc_entry, height=380, label_visibility="collapsed")

    st.markdown("#### Preview — email")
    st.markdown('<span class="rp-tag rp-tag-warn">Gmail draft, not sent</span>', unsafe_allow_html=True)
    st.markdown(f'**Subject:** {payload["email_subject"]}')
    st.text_area("email_body", value=payload["email_body"], height=300, label_visibility="collapsed")

# ------------------------------------------------------------- Approval gate
with right:
    # Plain-language status card. The SHA-256 fingerprint still guards against
    # publishing content that changed after this page loaded, but it's now
    # tucked into an expander instead of shouting a hex string at the reader.
    st.markdown(styles.card(
        '<div class="rp-kpi-label">Ready to publish</div>'
        f'<p class="rp-sub" style="margin:8px 0 0 0">The preview on the left is exactly what '
        'will be published. Nothing is sent until you approve it below.</p>'
        f'<div style="margin-top:12px" class="rp-tag {"rp-tag-ok" if passed == total else "rp-tag-warn"}">'
        f'Checks: {passed}/{total} passed</div>'
        f'<div class="rp-tag rp-tag-warn">Email stays a draft</div>'
    ), unsafe_allow_html=True)

    typed = st.text_input(
        "Type APPROVE to enable publishing",
        key="approve_word",
        placeholder="APPROVE",
        help="Deliberate human gate: the publish button stays disabled until you type the word "
             "approve. This is the one place a person signs off before anything leaves the app.",
    )
    st.caption("This is the human sign-off. The button below unlocks once you type APPROVE.")

    mcp_url, mcp_source = analysis.get_mcp_url()
    webhook_url, webhook_source = analysis.get_webhook_url()
    use_mcp = bool(mcp_url)
    channel = "n8n (MCP tools)" if use_mcp else "n8n (webhook)"
    fp_now = analysis.fingerprint(payload)

    can_approve = typed.strip().upper() == "APPROVE" and bool(use_mcp or webhook_url)
    if st.button("Approve & publish", type="primary", disabled=not can_approve):
        payload_now, _ = analysis.build_payload()
        try:
            if use_mcp:
                import mcp_client
                steps = mcp_client.publish_via_mcp(mcp_url, payload_now)
                result = "Published — " + "; ".join(steps)
                analysis.append_history("approve", fp_now, result)
                st.success(result + " Check the Google Doc and Gmail Drafts.")
            else:
                resp = requests.post(webhook_url, json=payload_now, timeout=30)
                if 200 <= resp.status_code < 300:
                    result = "Published via webhook"
                    analysis.append_history("approve", fp_now, result)
                    st.success(result + " Check the Google Doc and Gmail Drafts.")
                else:
                    result = f"Error HTTP {resp.status_code}: {resp.text[:300]}"
                    analysis.append_history("approve", fp_now, result)
                    st.error("Publish failed with status " + str(resp.status_code))
                    st.code(resp.text)
        except Exception as e:
            result = f"Publish failed: {e}"
            analysis.append_history("approve", fp_now, result)
            st.error(f"Publish failed: {e}")

    if st.button("Reject"):
        analysis.append_history("reject", fp_now, "Rejected — nothing sent")
        st.info("Rejected — nothing was published and the email stays a draft.")

    # Technical detail is available but out of the way.
    with st.expander("Technical details"):
        st.markdown(
            f"**Channel:** {channel} ({mcp_source if use_mcp else webhook_source})\n\n"
            "The publish step calls the n8n MCP tools `append_to_doc` then "
            "`create_email_draft`. The email is always created as a Gmail draft, never sent."
        )
        if use_mcp:
            st.markdown(f"**Endpoint:** `{mcp_url}`")
        if not webhook_url:
            st.caption("Webhook fallback: not configured")
