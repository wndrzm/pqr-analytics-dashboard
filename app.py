import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ─── PAGE CONFIG ───────────────────────────────────────────
st.set_page_config(page_title="PQR Analytics Dashboard", layout="wide")

st.title("📊 Clinical PQR Analytics Dashboard")
st.caption("Product Quality Review — Pharmaceutical Manufacturing 2024")

st.info("""
👩‍⚕️ **Tentang Dashboard Ini**

Dashboard ini dibangun berdasarkan pengalaman nyata sebagai apoteker industri yang kesulitan menganalisis data Product Quality Review (PQR) secara manual — proses yang biasanya memakan waktu berhari-hari kini bisa divisualisasikan dalam hitungan detik.

Dibangun oleh **Wanda Rizqi Amaliah** — Pharmacist × AI Engineer | Rubythalib AI Bootcamp 2026
""")

# ─── LOAD DATA ─────────────────────────────────────────────
df = pd.read_csv("pqr_dummy_dataset_with_capa.csv")
df['production_date'] = pd.to_datetime(df['production_date'])
df['month'] = df['production_date'].dt.to_period('M')
df['month_str'] = df['production_date'].dt.strftime('%Y-%m')

# ─── SIDEBAR FILTER ────────────────────────────────────────
st.sidebar.header("🔍 Filter Data")
produk_list = ['Semua'] + list(df['product_name'].unique())
pilihan_produk = st.sidebar.selectbox("Pilih Produk", produk_list)

if pilihan_produk != 'Semua':
    df_filtered = df[df['product_name'] == pilihan_produk]
else:
    df_filtered = df.copy()

# ─── SUMMARY METRICS ───────────────────────────────────────
st.subheader("📋 Summary")
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Batch", len(df_filtered))
col2.metric("Batch PASS", len(df_filtered[df_filtered['status'] == 'PASS']))
col3.metric("Batch FAIL", len(df_filtered[df_filtered['status'] == 'FAIL']))
col4.metric("Total Deviasi", int(df_filtered['deviation_count'].sum()))
col5.metric("Rata-rata Yield", f"{df_filtered['yield_pct'].mean():.2f}%")

st.markdown("---")

# ─── TREND YIELD ───────────────────────────────────────────
st.subheader("📈 Trend Rata-rata Yield per Bulan")
yield_per_bulan = df_filtered.groupby('month_str')['yield_pct'].mean().reset_index()
yield_per_bulan.columns = ['month', 'avg_yield']

fig1 = px.line(
    yield_per_bulan, x='month', y='avg_yield',
    markers=True,
    labels={'month': 'Bulan', 'avg_yield': 'Rata-rata Yield (%)'}
)
fig1.update_layout(yaxis_range=[85, 100])
st.plotly_chart(fig1, use_container_width=True)

st.markdown("---")

# ─── DEVIASI & ROOT CAUSE ──────────────────────────────────
st.subheader("⚠️ Analisis Deviasi")
col_a, col_b = st.columns(2)

with col_a:
    st.markdown("**Total Deviasi per Produk**")
    deviasi_per_produk = df_filtered.groupby('product_name')['deviation_count'].sum().reset_index()
    deviasi_per_produk.columns = ['product_name', 'total_deviasi']
    fig2 = px.bar(
        deviasi_per_produk, x='product_name', y='total_deviasi',
        color='product_name',
        labels={'product_name': 'Produk', 'total_deviasi': 'Jumlah Deviasi'}
    )
    st.plotly_chart(fig2, use_container_width=True)

with col_b:
    st.markdown("**Distribusi Penyebab Deviasi**")
    deviasi_type = df_filtered[df_filtered['deviation_type'].notna()]['deviation_type']
    deviasi_type = deviasi_type.str.split(';').explode().str.strip()
    deviasi_count = deviasi_type.value_counts().reset_index()
    deviasi_count.columns = ['deviation_type', 'count']
    fig3 = px.pie(
        deviasi_count, names='deviation_type', values='count'
    )
    st.plotly_chart(fig3, use_container_width=True)

st.markdown("---")

# ─── OOS & OOT ─────────────────────────────────────────────
st.subheader("🔴 OOS & OOT per Bulan")
oos_oot_bulan = df_filtered.groupby('month_str')[['oos_count', 'oot_count']].sum().reset_index()
fig4 = px.bar(
    oos_oot_bulan, x='month_str', y=['oos_count', 'oot_count'],
    barmode='group',
    labels={'month_str': 'Bulan', 'value': 'Jumlah Kejadian'}
)
st.plotly_chart(fig4, use_container_width=True)

st.markdown("---")

# ─── CAPA TRACKER ──────────────────────────────────────────
st.subheader("✅ CAPA Tracker")
col_c, col_d = st.columns(2)

capa_df = df_filtered[df_filtered['capa_id'].notna()][[
    'batch_number', 'product_name', 'capa_id',
    'capa_description', 'capa_status', 'due_date', 'pic', 'closed_date'
]]

with col_c:
    st.markdown("**Status CAPA**")
    status_count = capa_df['capa_status'].value_counts().reset_index()
    status_count.columns = ['status', 'count']
    fig5 = px.pie(
        status_count, names='status', values='count',
        color='status',
        color_discrete_map={'Closed': 'green', 'In Progress': 'orange', 'Open': 'red'}
    )
    st.plotly_chart(fig5, use_container_width=True)

with col_d:
    st.markdown("**Detail CAPA**")
    st.dataframe(capa_df.reset_index(drop=True), use_container_width=True)

st.markdown("---")

# ─── PROCESS CAPABILITY ────────────────────────────────────
st.subheader("📐 Process Capability Chart")

usl = 100
lsl = 97
mean_yield = df_filtered['yield_pct'].mean()
std_yield = df_filtered['yield_pct'].std()
std_overall = df_filtered['yield_pct'].std(ddof=0)

ucl = mean_yield + 3 * std_yield
lcl = mean_yield - 3 * std_yield
cp = (usl - lsl) / (6 * std_yield)
cpk = min((usl - mean_yield), (mean_yield - lsl)) / (3 * std_yield)
pp = (usl - lsl) / (6 * std_overall)
ppk = min((usl - mean_yield), (mean_yield - lsl)) / (3 * std_overall)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Cp", f"{cp:.2f}", delta="≥1.33 capable" if cp >= 1.33 else "❌ not capable")
col2.metric("Cpk", f"{cpk:.2f}", delta="≥1.33 capable" if cpk >= 1.33 else "❌ not capable")
col3.metric("Pp", f"{pp:.2f}", delta="≥1.33 capable" if pp >= 1.33 else "❌ not capable")
col4.metric("Ppk", f"{ppk:.2f}", delta="≥1.33 capable" if ppk >= 1.33 else "❌ not capable")

fig6 = go.Figure()
fig6.add_trace(go.Scatter(
    x=df_filtered['batch_number'], y=df_filtered['yield_pct'],
    mode='lines+markers', name='Yield (%)',
    line=dict(color='royalblue')
))
fig6.add_hline(y=mean_yield, line_dash='dash', line_color='green',
               annotation_text=f'Mean: {mean_yield:.2f}%', annotation_position='right')
fig6.add_hline(y=ucl, line_dash='dot', line_color='orange',
               annotation_text=f'UCL: {ucl:.2f}%', annotation_position='right')
fig6.add_hline(y=lcl, line_dash='dot', line_color='orange',
               annotation_text=f'LCL: {lcl:.2f}%', annotation_position='right')
fig6.add_hline(y=usl, line_dash='solid', line_color='red',
               annotation_text=f'USL: {usl}%', annotation_position='right')
fig6.add_hline(y=lsl, line_dash='solid', line_color='red',
               annotation_text=f'LSL: {lsl}%', annotation_position='right')
fig6.update_layout(
    xaxis_title='Batch Number',
    yaxis_title='Yield (%)',
    yaxis_range=[83, 102]
)
st.plotly_chart(fig6, use_container_width=True)

st.markdown("---")
st.caption("Built by Wanda Rizqi Amaliah | Pharmacist × AI Engineer | Rubythalib AI Bootcamp 2024")