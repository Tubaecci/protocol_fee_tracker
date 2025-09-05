import streamlit as st
import pandas as pd
import plotly.express as px
import joblib
import os

# Page config
st.set_page_config(
    page_title="Plume DeFi Fees Revenue Tracker",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for colorful KPI cards
st.markdown("""
<style>
    .metric-card, .metric-card-orange, .metric-card-orange1, .metric-card-orange2, .metric-card-orange3 {
        padding: 1rem;
        border-radius: 10px;
        border: 2px solid #d53f8c;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .metric-card-orange  {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    }
    .metric-card-orange1 {
        background: linear-gradient(135deg, #ffb347 0%, #ffcc33 100%);
    }
    .metric-card-orange2 {
        background: linear-gradient(135deg, #ff9966 0%, #ff5e62 100%);
    }
    .metric-card-orange3 {
        background: linear-gradient(135deg, #f7971e 0%, #ffd200 100%);
    }
    .metric-title {
        font-size: 0.9rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0;
    }
</style>
""", unsafe_allow_html=True)

def format_currency(amount):
    if amount is None or pd.isna(amount) or amount == 0:
        return "$0"
    if amount >= 1_000_000_000:
        return f"${amount/1_000_000_000:.2f}B"
    elif amount >= 1_000_000:
        return f"${amount/1_000_000:.2f}M"
    elif amount >= 1_000:
        return f"${amount/1_000:.2f}K"
    else:
        return f"${amount:.2f}"

def create_metric_card(title, value, card_type="orange"):
    card_class = f"metric-card-{card_type}" if card_type != "default" else "metric-card-orange"
    return f"""
    <div class="{card_class}">
        <div class="metric-title">{title}</div>
        <div class="metric-value">{value}</div>
    </div>
    """

# Load data
df_protocols_tvl = joblib.load('database/df_protocols_tvl.joblib')
df_protocols_revenue = joblib.load('database/df_protocols_revenue.joblib')
df_protocols_fees = joblib.load('database/df_protocols_fees.joblib')
df_protocols_market_data = joblib.load('database/df_protocols_market_data.joblib')

st.title("🪶 Plume DeFi Fees & Revenue Tracker")

# Sidebar filters
st.sidebar.header("🔍 Filters & Controls")
protocols = sorted(df_protocols_tvl['Protocol'].unique())
selected_protocols = st.sidebar.multiselect("Select Protocol(s)", protocols, default=protocols[:5] if len(protocols) > 5 else protocols)
 
categories = []
if 'Category' in df_protocols_tvl.columns:
    categories = sorted(df_protocols_tvl['Category'].dropna().unique())
selected_categories = st.sidebar.multiselect("Filter by Category", categories, default=categories)

# Filter data
filtered_tvl = df_protocols_tvl[df_protocols_tvl['Protocol'].isin(selected_protocols)]
if selected_categories:
    filtered_tvl = filtered_tvl[filtered_tvl['Category'].isin(selected_categories)]

filtered_fees = df_protocols_fees[df_protocols_fees['Protocol'].isin(filtered_tvl['Protocol'])]
filtered_revenue = df_protocols_revenue[df_protocols_revenue['Protocol'].isin(filtered_tvl['Protocol'])]
filtered_market = df_protocols_market_data[df_protocols_market_data['Protocol'].isin(filtered_tvl['Protocol'])]

# KPIs
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(create_metric_card(
        "Total Protocols",
        str(len(filtered_tvl)),
        "orange1"
    ), unsafe_allow_html=True)
with col2:
    st.markdown(create_metric_card(
        "Total TVL",
        format_currency(filtered_tvl['TVL (USD)'].sum()),
        "orange2"
    ), unsafe_allow_html=True)
with col3:
    st.markdown(create_metric_card(
        "Total Market Cap",
        format_currency(filtered_market['Market Cap (USD)'].sum() if 'Market Cap (USD)' in filtered_market.columns else 0),
        "orange3"
    ), unsafe_allow_html=True)

# Overview Table
st.header("📋 Protocol Overview")
overview_cols = [col for col in ['Protocol', 'Category', 'TVL (USD)'] if col in filtered_tvl.columns]
if 'Market Cap (USD)' in filtered_market.columns:
    overview_cols.append('Market Cap (USD)')
if 'Current Price (USD)' in filtered_market.columns:
    overview_cols.append('Current Price (USD)')

overview_df = pd.merge(filtered_tvl, filtered_market, on='Protocol', how='left')

# Format TVL (USD) column with $ sign
format_dict = {}
if 'TVL (USD)' in overview_cols:
    format_dict['TVL (USD)'] = lambda x: format_currency(x)

st.dataframe(
    overview_df[overview_cols].reset_index(drop=True).style.format(format_dict),
    use_container_width=True
)

# Top Protocols by TVL
st.subheader("🏆 Top Protocols by TVL")
top_tvl = filtered_tvl.nlargest(10, 'TVL (USD)')
fig = px.bar(top_tvl, x='Protocol', y='TVL (USD)', color='Category', title="Top Protocols by TVL")
fig.update_layout(xaxis_tickangle=45, showlegend=True)
st.plotly_chart(fig, use_container_width=True)

# Revenue & Fees Section
st.header("💰 Revenue & Fees")
col1, col2 = st.columns(2)

with col1:
    st.subheader("Top Revenue Earners")
    if not filtered_revenue.empty:
        top_revenue = filtered_revenue.nlargest(10, '24h Revenue (USD)')
        st.dataframe(top_revenue[['Protocol', '24h Revenue (USD)', '7d Revenue (USD)', '30d Revenue (USD)', 'Total Revenue (USD)']].reset_index(drop=True), use_container_width=True)
        fig_rev = px.bar(top_revenue, x='Protocol', y='24h Revenue (USD)', title="24h Revenue", color_discrete_sequence=['#11998e'])
        fig_rev.update_layout(xaxis_tickangle=45)
        st.plotly_chart(fig_rev, use_container_width=True)

with col2:
    st.subheader("Top Fee Generators")
    if not filtered_fees.empty:
        top_fees = filtered_fees.nlargest(10, '24h Fees (USD)')
        st.dataframe(top_fees[['Protocol', '24h Fees (USD)', '7d Fees (USD)', '30d Fees (USD)', 'Total Fees (USD)']].reset_index(drop=True), use_container_width=True)
        fig_fees = px.bar(top_fees, x='Protocol', y='24h Fees (USD)', title="24h Fees", color_discrete_sequence=['#f5576c'])
        fig_fees.update_layout(xaxis_tickangle=45)
        st.plotly_chart(fig_fees, use_container_width=True)

# Market Data Table
st.header("📈 Market Data")
if not filtered_market.empty:
    st.dataframe(filtered_market.reset_index(drop=True), use_container_width=True)

# Footer
st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    st.markdown("**📊 Data Sources:**")
    st.markdown("- DefiLlama API")
    st.markdown("- CoinGecko API")
with col2:
    st.markdown("**🔄 Refresh Schedule:**")
    st.markdown("- Manual refresh: Update data notebooks and rerun app")