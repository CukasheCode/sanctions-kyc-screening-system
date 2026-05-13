# ============================================================
# SANCTIONS SCREENING COMPLIANCE DASHBOARD — BEAUTIFUL VERSION
# ============================================================
# What this file does:
#   - Connects to your S3 bucket
#   - Reads your CSV files (alert_queue, whitelist, kyc_customers)
#   - Shows a professional compliance dashboard with colors
#   - Allows the officer to confirm alerts or mark false positives
#
# How to run it:
#   streamlit run sanctions_dashboard_beautiful.py
# ============================================================

# --- IMPORTS ---
import streamlit as st
import boto3
import pandas as pd
import io
import requests
from datetime import datetime

# ============================================================
# STEP 1: CONFIGURATION
# Change BUCKET_NAME to your actual S3 bucket name
# ============================================================
BUCKET_NAME = "sanctions-screening-mismail"
AWS_REGION  = "us-east-1"
API_URL     = "https://7m2zj4bfpk.execute-api.us-east-1.amazonaws.com/default/sanctions-real-time"

# ============================================================
# STEP 2: CONNECT TO AWS S3
# boto3 uses your "aws configure" credentials automatically
# ============================================================
s3 = boto3.client(

    "s3",

    region_name=AWS_REGION,

    aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],

    aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"]

)

# ============================================================
# STEP 3: FUNCTION TO READ CSV FILES FROM S3
# Downloads the file from S3 and reads it as a pandas table
# ============================================================
def read_csv(key):
    try:
        response = s3.get_object(Bucket=BUCKET_NAME, Key=key)
        return pd.read_csv(io.StringIO(response["Body"].read().decode("utf-8")))
    except Exception as e:
        st.warning(f"Could not load {key}: {e}")
        return pd.DataFrame()

# ============================================================
# STEP 4: FUNCTION TO SAVE CSV FILES BACK TO S3
# Used when the officer takes action on an alert
# ============================================================
def save_csv(df, key):
    try:
        buf = io.StringIO()
        df.to_csv(buf, index=False)
        s3.put_object(Bucket=BUCKET_NAME, Key=key, Body=buf.getvalue())
        return True
    except Exception as e:
        st.error(f"Save failed: {e}")
        return False

# ============================================================
# STEP 5: PAGE SETTINGS AND CUSTOM STYLING
# This makes the dashboard look professional with colors
# ============================================================
st.set_page_config(
    page_title="Sanctions Screening Dashboard",
    page_icon="🛡️",
    layout="wide"
)

# Custom CSS — this adds colors and styling to the dashboard
# Think of this as the "paint" for the dashboard
st.markdown("""
<style>
    /* Main background */
    .main { background-color: #0F1117; }

    /* Top header bar */
    .header-bar {
        background: linear-gradient(90deg, #1a1f2e, #162032);
        padding: 20px 30px;
        border-radius: 12px;
        border-left: 4px solid #FF4B4B;
        margin-bottom: 24px;
    }

    /* Metric cards */
    [data-testid="metric-container"] {
        background: #1a1f2e;
        border: 1px solid #2d3748;
        border-radius: 12px;
        padding: 16px;
    }

    /* Alert table rows */
    .alert-row {
        background: #1e2a3a;
        border-left: 4px solid #FF4B4B;
        padding: 12px 16px;
        border-radius: 8px;
        margin-bottom: 8px;
    }

    /* Pass badge */
    .badge-pass {
        background: #1a4731;
        color: #2ecc71;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 600;
    }

    /* Flag badge */
    .badge-flag {
        background: #4a1a1a;
        color: #FF4B4B;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 600;
    }

    /* Pending badge */
    .badge-pending {
        background: #3a3a1a;
        color: #f1c40f;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 13px;
        font-weight: 600;
    }

    /* Section headers */
    .section-header {
        color: #a0aec0;
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        margin-bottom: 12px;
    }

    /* Divider */
    hr { border-color: #2d3748; }

    /* Dataframe styling */
    [data-testid="stDataFrame"] {
        border-radius: 8px;
        overflow: hidden;
    }

    /* Button styling */
    .stButton button {
        border-radius: 8px;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# STEP 6: HEADER
# ============================================================
st.markdown("""
<div class="header-bar">
    <h1 style="color: white; margin: 0; font-size: 24px;">
        🛡️ Sanctions Screening Compliance Dashboard
    </h1>
    <p style="color: #a0aec0; margin: 4px 0 0 0; font-size: 14px;">
        Real-time and batch screening · OFAC · CASL · OFSI · UN · FATF
    </p>
</div>
""", unsafe_allow_html=True)

# Show last loaded time
col_time, col_status = st.columns([3, 1])
with col_time:
    st.caption(f"Last loaded: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC")
with col_status:
    st.markdown('<span style="color: #2ecc71; font-size: 13px;">● System operational</span>', unsafe_allow_html=True)

st.divider()

# ============================================================
# STEP 7: LOAD ALL DATA FROM S3
# We load all files once at the top
# ============================================================
with st.spinner("Loading data from AWS S3..."):
    alert_df     = read_csv("alert_queue.csv")
    whitelist_df = read_csv("whitelist.csv")
    kyc_df       = read_csv("kyc_customers.csv")

# ============================================================
# STEP 8: TOP METRICS ROW
# Four numbers across the top of the dashboard
# ============================================================
col1, col2, col3, col4 = st.columns(4)

# Count pending alerts
pending = len(alert_df[alert_df["status"] == "pending"]) if "status" in alert_df.columns else len(alert_df)

with col1:
    st.metric(
        label="🚨 Total Alerts",
        value=len(alert_df),
        delta="requires review" if len(alert_df) > 0 else "all clear"
    )
with col2:
    st.metric(
        label="⏳ Pending Review",
        value=pending,
        delta=f"{pending} outstanding" if pending > 0 else "none"
    )
with col3:
    st.metric(
        label="✅ Whitelisted",
        value=len(whitelist_df),
        delta="cleared customers"
    )
with col4:
    st.metric(
        label="🗃️ Sanctions Database",
        value="82,408",
        delta="5 global sources"
    )

st.divider()

# ============================================================
# STEP 9: PANEL 1 — ALERT QUEUE
# The most important panel — compliance officer reviews here
# ============================================================
st.markdown('<p class="section-header">Panel 1 — Alert Queue</p>', unsafe_allow_html=True)
st.markdown("**Every customer that matched a sanctions entry. Review each alert and take action.**")

if alert_df.empty:
    # Green success message when no alerts
    st.success("✅ No pending alerts. All customers have been screened and cleared.")

else:
    # Show each alert as a colored card
    for _, row in alert_df.iterrows():
        with st.container():
            st.markdown(f"""
            <div class="alert-row">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <span style="color: white; font-weight: 600; font-size: 15px;">
                            {row.get('customer_name', 'Unknown')}
                        </span>
                        <span style="color: #a0aec0; font-size: 13px; margin-left: 12px;">
                            Matched: {row.get('match', 'Unknown')}
                        </span>
                    </div>
                    <div>
                        <span style="color: #FF4B4B; font-weight: 600; font-size: 13px; margin-right: 16px;">
                            Source: {row.get('source', 'Unknown')} list
                        </span>
                        <span style="color: #f1c40f; font-weight: 600; font-size: 13px;">
                            Score: {row.get('match_score', 0)}%
                        </span>
                    </div>
                </div>
                <div style="margin-top: 6px; color: #718096; font-size: 12px;">
                    Detected: {row.get('timestamp', 'Unknown')} &nbsp;|&nbsp;
                    Status: <span class="badge-pending">{row.get('status', 'pending')}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Also show as a table for easy reading
    st.markdown("**Full alert details:**")
    st.dataframe(alert_df, use_container_width=True, height=200)

    # Action section
    st.markdown("---")
    st.markdown("**Take action on an alert:**")

    col_a, col_b = st.columns(2)
    with col_a:
        name = st.text_input(
            "Customer name to action",
            placeholder="e.g. Banco Nacional de Cuba"
        )
    with col_b:
        action = st.selectbox(
            "Choose action",
            ["-- select --", "Add to Whitelist", "Mark False Positive", "Confirm Match"]
        )

    if st.button("Submit Action", type="primary"):
        if not name:
            st.warning("Please enter a customer name.")
        elif action == "-- select --":
            st.warning("Please select an action.")

        elif action == "Add to Whitelist":
            # Add to whitelist and remove from alerts
            new_entry = pd.DataFrame([{
                "customer_id":  "",
                "name":         name,
                "cleared_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "cleared_by":   "compliance_officer"
            }])
            updated_whitelist = pd.concat([whitelist_df, new_entry], ignore_index=True)
            updated_alerts    = alert_df[alert_df["customer_name"] != name].copy()
            if save_csv(updated_whitelist, "whitelist.csv") and save_csv(updated_alerts, "alert_queue.csv"):
                st.success(f"✅ {name} added to whitelist. Future alerts will be suppressed.")
                st.rerun()

        elif action == "Confirm Match":
            # Real sanctions hit — must file SAR with FINTRAC
            st.error(f"""
            🚨 CONFIRMED SANCTIONS MATCH
            Customer: {name}
            Action required: File a Suspicious Activity Report (SAR) with FINTRAC immediately.
            Do NOT inform the customer — tipping off is a criminal offence in Canada.
            """)

        elif action == "Mark False Positive":
            # Update status in alert queue
            updated_alerts = alert_df.copy()
            updated_alerts.loc[updated_alerts["customer_name"] == name, "status"] = "false_positive"
            if save_csv(updated_alerts, "alert_queue.csv"):
                st.info(f"ℹ️ {name} marked as false positive. Alert dismissed.")
                st.rerun()

st.divider()

# ============================================================
# STEP 10: PANEL 2 — REAL-TIME SCREENING TEST
# Type any name and screen it against all 5 lists instantly
# ============================================================
st.markdown('<p class="section-header">Panel 2 — Real-Time Screening</p>', unsafe_allow_html=True)
st.markdown("**Screen any customer name against all 82,408 sanctions entries instantly.**")

col_input, col_btn = st.columns([4, 1])
with col_input:
    test_name = st.text_input(
        "Name to screen",
        placeholder="e.g. North Korea Trading Corp",
        label_visibility="collapsed"
    )
with col_btn:
    screen_btn = st.button("Screen Now 🔍", type="primary", use_container_width=True)

if screen_btn:
    if not test_name:
        st.warning("Please enter a name to screen.")
    else:
        with st.spinner(f"Screening {test_name} against 82,408 sanctions entries..."):
            try:
                resp   = requests.post(API_URL, json={"name": test_name}, timeout=10)
                result = resp.json()

                if result.get("status") == "FLAG":
                    # Red alert for a match
                    st.markdown(f"""
                    <div style="background: #4a1a1a; border: 1px solid #FF4B4B; border-radius: 12px; padding: 20px; margin: 12px 0;">
                        <h3 style="color: #FF4B4B; margin: 0 0 8px 0;">🚨 FLAGGED — Sanctions Match Found</h3>
                        <p style="color: white; margin: 4px 0;"><strong>Customer screened:</strong> {test_name}</p>
                        <p style="color: white; margin: 4px 0;"><strong>Matched entry:</strong> {result.get('match', 'Unknown')}</p>
                        <p style="color: white; margin: 4px 0;"><strong>Source list:</strong> {result.get('source', 'Unknown')}</p>
                        <p style="color: #a0aec0; margin: 12px 0 0 0; font-size: 13px;">
                            This customer must not be onboarded. File a SAR with FINTRAC if account exists.
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # Green pass for clean result
                    st.markdown(f"""
                    <div style="background: #1a4731; border: 1px solid #2ecc71; border-radius: 12px; padding: 20px; margin: 12px 0;">
                        <h3 style="color: #2ecc71; margin: 0 0 8px 0;">✅ PASS — No Sanctions Match</h3>
                        <p style="color: white; margin: 4px 0;"><strong>Customer screened:</strong> {test_name}</p>
                        <p style="color: #a0aec0; margin: 4px 0; font-size: 13px;">
                            Not found on any of the 5 sanctions lists. Customer may proceed.
                        </p>
                    </div>
                    """, unsafe_allow_html=True)

                # Show raw API response
                with st.expander("View raw API response"):
                    st.json(result)

            except Exception as e:
                st.warning(f"API connection error: {e}")

st.divider()

# ============================================================
# STEP 11: PANEL 3 — KYC CUSTOMERS
# All customers in the system
# ============================================================
st.markdown('<p class="section-header">Panel 3 — KYC Customer Database</p>', unsafe_allow_html=True)
st.markdown(f"**{len(kyc_df)} customers registered in the system.**")

if kyc_df.empty:
    st.info("No KYC customers loaded.")
else:
    # Color code rows by risk country
    high_risk_countries = ["Cuba", "CUBA", "North Korea", "Iran", "Syria", "Russia"]

    st.dataframe(
        kyc_df,
        use_container_width=True,
        height=250,
        column_config={
            "customer_id": st.column_config.NumberColumn("ID", width="small"),
            "name":        st.column_config.TextColumn("Customer Name", width="large"),
            "country":     st.column_config.TextColumn("Country", width="medium"),
        }
    )

    # Show risk summary
    high_risk = kyc_df[kyc_df["country"].isin(high_risk_countries)]
    if not high_risk.empty:
        st.warning(f"⚠️ {len(high_risk)} customer(s) from high-risk jurisdictions: {', '.join(high_risk['name'].tolist())}")

st.divider()

# ============================================================
# STEP 12: PANEL 4 — WHITELIST
# Customers cleared by compliance officers
# ============================================================
st.markdown('<p class="section-header">Panel 4 — Whitelist</p>', unsafe_allow_html=True)
st.markdown("**Customers cleared by compliance officers. Will not generate future alerts.**")

if whitelist_df.empty:
    st.info("Whitelist is empty. No customers have been cleared yet.")
else:
    st.dataframe(
        whitelist_df,
        use_container_width=True,
        height=200,
        column_config={
            "name":         st.column_config.TextColumn("Customer Name", width="large"),
            "cleared_date": st.column_config.TextColumn("Cleared Date", width="medium"),
            "cleared_by":   st.column_config.TextColumn("Cleared By", width="medium"),
        }
    )

st.divider()

# ============================================================
# STEP 13: SANCTIONS DATABASE SUMMARY
# Shows how many entries came from each source
# ============================================================
st.markdown('<p class="section-header">Sanctions Database Coverage</p>', unsafe_allow_html=True)

col_db1, col_db2, col_db3, col_db4, col_db5 = st.columns(5)
with col_db1:
    st.markdown("""
    <div style="background:#1a1f2e; border:1px solid #2d3748; border-radius:10px; padding:16px; text-align:center;">
        <div style="color:#FF4B4B; font-size:11px; font-weight:600; letter-spacing:1px;">OFAC</div>
        <div style="color:white; font-size:18px; font-weight:600; margin-top:4px;">US</div>
        <div style="color:#718096; font-size:11px;">Daily update</div>
    </div>""", unsafe_allow_html=True)
with col_db2:
    st.markdown("""
    <div style="background:#1a1f2e; border:1px solid #2d3748; border-radius:10px; padding:16px; text-align:center;">
        <div style="color:#3498db; font-size:11px; font-weight:600; letter-spacing:1px;">CASL</div>
        <div style="color:white; font-size:18px; font-weight:600; margin-top:4px;">Canada</div>
        <div style="color:#718096; font-size:11px;">Weekly update</div>
    </div>""", unsafe_allow_html=True)
with col_db3:
    st.markdown("""
    <div style="background:#1a1f2e; border:1px solid #2d3748; border-radius:10px; padding:16px; text-align:center;">
        <div style="color:#9b59b6; font-size:11px; font-weight:600; letter-spacing:1px;">OFSI</div>
        <div style="color:white; font-size:18px; font-weight:600; margin-top:4px;">UK</div>
        <div style="color:#718096; font-size:11px;">Weekly update</div>
    </div>""", unsafe_allow_html=True)
with col_db4:
    st.markdown("""
    <div style="background:#1a1f2e; border:1px solid #2d3748; border-radius:10px; padding:16px; text-align:center;">
        <div style="color:#1abc9c; font-size:11px; font-weight:600; letter-spacing:1px;">UN SC</div>
        <div style="color:white; font-size:18px; font-weight:600; margin-top:4px;">Global</div>
        <div style="color:#718096; font-size:11px;">Monthly update</div>
    </div>""", unsafe_allow_html=True)
with col_db5:
    st.markdown("""
    <div style="background:#1a1f2e; border:1px solid #2d3748; border-radius:10px; padding:16px; text-align:center;">
        <div style="color:#f39c12; font-size:11px; font-weight:600; letter-spacing:1px;">FATF</div>
        <div style="color:white; font-size:18px; font-weight:600; margin-top:4px;">AML</div>
        <div style="color:#718096; font-size:11px;">Quarterly update</div>
    </div>""", unsafe_allow_html=True)

# ============================================================
# FOOTER
# ============================================================
st.divider()
col_f1, col_f2 = st.columns([2, 1])
with col_f1:
    st.caption("Sanctions Screening Platform · Built on AWS S3 + Lambda + API Gateway · Canada-based compliance")
with col_f2:
    st.caption(f"82,408 sanctions entries · 5 sources · {datetime.now().strftime('%Y-%m-%d')}")
