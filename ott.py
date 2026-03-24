"""
StreamIQ — OTT Viewer Retention Dashboard
==========================================
Run locally:
    pip install streamlit pandas plotly
    streamlit run ott_dashboard.py

Place  dataset.csv  in the same folder as this file.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="StreamIQ · OTT Retention Dashboard",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Dark theme CSS ────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }

/* Background */
.stApp { background-color: #0b0b10; }
[data-testid="stSidebar"] { background-color: #131320 !important; border-right: 1px solid rgba(255,255,255,0.07); }
[data-testid="block-container"] { padding: 2rem 2.5rem 3rem; }

/* Sidebar text */
[data-testid="stSidebar"] * { color: #9898c0 !important; }
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #f5a623 !important; }

/* Metric cards */
[data-testid="stMetric"] {
    background: #131320;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 12px;
    padding: 16px !important;
}
[data-testid="stMetricLabel"] { color: #6a6a9a !important; font-size: 11px !important; text-transform: uppercase; letter-spacing: 1.5px; }
[data-testid="stMetricValue"] { color: #f5a623 !important; font-family: 'Bebas Neue', cursive !important; font-size: 2.2rem !important; }
[data-testid="stMetricDelta"] { font-size: 11px !important; }

/* Headers */
h1 { font-family: 'Bebas Neue', cursive !important; font-size: 2.6rem !important; color: #eeeeff !important; letter-spacing: 2px; }
h2, h3 { color: #eeeeff !important; }
p, li { color: #9898c0 !important; }

/* Divider */
hr { border-color: rgba(255,255,255,0.07); }

/* Plotly chart bg override */
.js-plotly-plot { background: transparent !important; }

/* Selectbox / slider */
[data-testid="stSelectbox"] > div, [data-testid="stMultiSelect"] > div {
    background: #1c1c2e !important;
    border-color: rgba(255,255,255,0.1) !important;
    color: #eeeeff !important;
}
.stSlider [data-baseweb="slider"] { color: #f5a623; }
</style>
""", unsafe_allow_html=True)

# ── Plotly dark layout defaults ───────────────────────────────────────────────
PLOT_BG   = "#131320"
PAPER_BG  = "#0b0b10"
GRID_CLR  = "rgba(255,255,255,0.05)"
FONT_CLR  = "#9898c0"
ACCENT    = "#f5a623"
DANGER    = "#e84040"
SAFE      = "#2ecc71"
INFO      = "#4da6ff"
PURPLE    = "#9b7ff5"

def dark_layout(fig, title="", height=350):
    fig.update_layout(
        title=dict(text=title, font=dict(color="#eeeeff", size=14, family="DM Sans")),
        plot_bgcolor=PLOT_BG,
        paper_bgcolor=PAPER_BG,
        font=dict(color=FONT_CLR, family="DM Sans"),
        height=height,
        margin=dict(l=10, r=10, t=40 if title else 10, b=10),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            font=dict(color=FONT_CLR, size=11),
        ),
        xaxis=dict(gridcolor=GRID_CLR, linecolor=GRID_CLR, zerolinecolor=GRID_CLR),
        yaxis=dict(gridcolor=GRID_CLR, linecolor=GRID_CLR, zerolinecolor=GRID_CLR),
    )
    return fig

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data(path="dataset.csv"):
    df = pd.read_csv(path)
    df["retention_risk"] = df["retention_risk"].str.lower().str.strip()
    df["attention_required"] = df["attention_required"].str.lower().str.strip()
    return df

try:
    df_raw = load_data()
except FileNotFoundError:
    st.error("❌  `dataset.csv` not found. Place it in the same folder as this script.")
    st.stop()

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎬 StreamIQ")
    st.markdown("**OTT Analytics Suite**")
    st.divider()

    st.markdown("### Filters")

    # Platform
    all_platforms = sorted(df_raw["platform"].dropna().unique())
    sel_platforms = st.multiselect(
        "Platform", all_platforms,
        default=["Netflix", "Hulu", "Prime Video", "Disney+", "HBO Max"],
        help="Select one or more platforms"
    )

    # Genre
    all_genres = sorted(df_raw["genre"].dropna().unique())
    sel_genres = st.multiselect(
        "Genre", all_genres, default=all_genres,
        help="Select genres to include"
    )

    # Retention risk
    sel_risk = st.multiselect(
        "Retention Risk", ["low", "medium", "high"],
        default=["low", "medium", "high"]
    )

    # Drop-off filter
    drop_choice = st.radio(
        "Drop-off Status",
        ["All", "Dropped Off", "Retained"],
        horizontal=True
    )

    # Episode range
    ep_min, ep_max = int(df_raw["episode_number"].min()), int(df_raw["episode_number"].max())
    ep_range = st.slider("Episode # Range", ep_min, min(ep_max, 50), (1, 20))

    # Hook strength
    hook_min, hook_max = int(df_raw["hook_strength"].min()), int(df_raw["hook_strength"].max())
    hook_range = st.slider("Hook Strength", hook_min, hook_max, (hook_min, hook_max))

    st.divider()
    st.markdown(f"**Dataset v1.0** · {len(df_raw):,} rows")
    st.markdown(f"{df_raw['show_id'].nunique()} unique shows")

# ── Apply filters ──────────────────────────────────────────────────────────────
df = df_raw.copy()
if sel_platforms:
    df = df[df["platform"].isin(sel_platforms)]
if sel_genres:
    df = df[df["genre"].isin(sel_genres)]
if sel_risk:
    df = df[df["retention_risk"].isin(sel_risk)]
if drop_choice == "Dropped Off":
    df = df[df["drop_off"] == 1]
elif drop_choice == "Retained":
    df = df[df["drop_off"] == 0]
df = df[df["episode_number"].between(*ep_range)]
df = df[df["hook_strength"].between(*hook_range)]

if df.empty:
    st.warning("No data matches the current filters. Please adjust sidebar filters.")
    st.stop()

# ── Title ─────────────────────────────────────────────────────────────────────
st.markdown("<h1>VIEWER <span style='color:#f5a623'>RETENTION</span> DASHBOARD</h1>", unsafe_allow_html=True)
st.markdown(
    f"<p style='color:#6a6a9a;font-size:12px;margin-top:-12px;'>"
    f"{df['show_id'].nunique()} shows · {len(df):,} episodes · "
    f"{df['platform'].nunique()} platforms after filters</p>",
    unsafe_allow_html=True
)
st.divider()

# ── KPI Row ────────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)

with k1:
    st.metric("Unique Shows", df["show_id"].nunique())
with k2:
    avg_watch = df["avg_watch_percentage"].mean()
    st.metric("Avg Watch %", f"{avg_watch:.1f}%")
with k3:
    drop_rate = df["drop_off"].mean() * 100
    st.metric("Drop-off Rate", f"{drop_rate:.1f}%")
with k4:
    avg_prob = df["drop_off_probability"].mean()
    st.metric("Avg Drop-off Prob", f"{avg_prob:.3f}")
with k5:
    high_risk = (df["retention_risk"] == "high").sum()
    st.metric("High-Risk Episodes", f"{high_risk:,}")

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# ROW 1 — Episode drop-off trend + Retention risk donut
# ─────────────────────────────────────────────────────────────────────────────
col1, col2 = st.columns([2, 1])

with col1:
    ep_df = (
        df[df["episode_number"] <= 15]
        .groupby("episode_number", as_index=False)
        .agg(
            drop_off_rate=("drop_off", "mean"),
            avg_watch=("avg_watch_percentage", "mean"),
        )
    )
    ep_df["drop_off_pct"] = ep_df["drop_off_rate"] * 100

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(
            x=ep_df["episode_number"], y=ep_df["avg_watch"],
            name="Avg Watch %", mode="lines+markers",
            line=dict(color=ACCENT, width=2),
            marker=dict(size=6, color=ACCENT),
            fill="tozeroy", fillcolor="rgba(245,166,35,0.07)"
        ), secondary_y=False
    )
    fig.add_trace(
        go.Scatter(
            x=ep_df["episode_number"], y=ep_df["drop_off_pct"],
            name="Drop-off %", mode="lines+markers",
            line=dict(color=DANGER, width=2),
            marker=dict(size=6, color=DANGER),
            fill="tozeroy", fillcolor="rgba(232,64,64,0.07)"
        ), secondary_y=True
    )
    fig.update_yaxes(title_text="Avg Watch %", secondary_y=False,
                     gridcolor=GRID_CLR, color=FONT_CLR)
    fig.update_yaxes(title_text="Drop-off %", secondary_y=True,
                     gridcolor=GRID_CLR, color=DANGER)
    fig.update_xaxes(
        tickvals=ep_df["episode_number"].tolist(),
        ticktext=[f"Ep {e}" for e in ep_df["episode_number"].tolist()],
        gridcolor=GRID_CLR, color=FONT_CLR
    )
    dark_layout(fig, "Drop-off Rate & Avg Watch % by Episode", height=340)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    risk_counts = df["retention_risk"].value_counts().reset_index()
    risk_counts.columns = ["risk", "count"]
    risk_color_map = {"high": DANGER, "medium": ACCENT, "low": SAFE}
    fig2 = px.pie(
        risk_counts, names="risk", values="count",
        color="risk", color_discrete_map=risk_color_map,
        hole=0.65
    )
    fig2.update_traces(textinfo="percent+label", textfont_color="#eeeeff")
    dark_layout(fig2, "Retention Risk Distribution", height=340)
    st.plotly_chart(fig2, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# ROW 2 — Platform avg watch + Genre avg watch
# ─────────────────────────────────────────────────────────────────────────────
col3, col4 = st.columns(2)

with col3:
    plat_df = (
        df.groupby("platform", as_index=False)
        .agg(avg_watch=("avg_watch_percentage", "mean"), count=("drop_off", "count"))
        .sort_values("avg_watch", ascending=False)
        .head(10)
    )
    fig3 = px.bar(
        plat_df, x="platform", y="avg_watch",
        color="avg_watch", color_continuous_scale=[[0, DANGER], [0.5, ACCENT], [1, SAFE]],
        text=plat_df["avg_watch"].map(lambda v: f"{v:.1f}%"),
    )
    fig3.update_traces(textposition="outside", textfont_color="#eeeeff")
    fig3.update_coloraxes(showscale=False)
    fig3.update_layout(xaxis_tickangle=-30)
    dark_layout(fig3, "Top 10 Platforms — Avg Watch Completion %", height=360)
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    genre_df = (
        df.groupby("genre", as_index=False)
        .agg(avg_watch=("avg_watch_percentage", "mean"),
             drop_prob=("drop_off_probability", "mean"),
             count=("drop_off", "count"))
        .sort_values("avg_watch", ascending=True)
    )
    fig4 = go.Figure()
    fig4.add_trace(go.Bar(
        y=genre_df["genre"], x=genre_df["avg_watch"],
        orientation="h", name="Avg Watch %",
        marker=dict(
            color=genre_df["avg_watch"],
            colorscale=[[0, DANGER], [0.5, ACCENT], [1, SAFE]],
            showscale=False
        ),
        text=genre_df["avg_watch"].map(lambda v: f"{v:.1f}%"),
        textposition="outside", textfont=dict(color="#eeeeff", size=10)
    ))
    dark_layout(fig4, "Genre vs Avg Watch Completion %", height=360)
    fig4.update_xaxes(title_text="Avg Watch %")
    st.plotly_chart(fig4, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# ROW 3 — Hook strength dual-axis + Cognitive load bar
# ─────────────────────────────────────────────────────────────────────────────
col5, col6 = st.columns(2)

with col5:
    hook_df = (
        df.groupby("hook_strength", as_index=False)
        .agg(avg_watch=("avg_watch_percentage", "mean"),
             drop_prob=("drop_off_probability", "mean"))
    )
    fig5 = make_subplots(specs=[[{"secondary_y": True}]])
    fig5.add_trace(go.Bar(
        x=hook_df["hook_strength"], y=hook_df["avg_watch"],
        name="Avg Watch %",
        marker_color=ACCENT, opacity=0.8
    ), secondary_y=False)
    fig5.add_trace(go.Scatter(
        x=hook_df["hook_strength"], y=hook_df["drop_prob"] * 100,
        name="Drop-off Prob %",
        mode="lines+markers",
        line=dict(color=DANGER, width=2),
        marker=dict(size=7, color=DANGER)
    ), secondary_y=True)
    fig5.update_xaxes(title_text="Hook Strength Score", gridcolor=GRID_CLR, color=FONT_CLR)
    fig5.update_yaxes(title_text="Avg Watch %", secondary_y=False,
                      gridcolor=GRID_CLR, color=FONT_CLR)
    fig5.update_yaxes(title_text="Drop-off Prob %", secondary_y=True,
                      gridcolor=GRID_CLR, color=DANGER)
    dark_layout(fig5, "Hook Strength vs Watch % & Drop-off Probability", height=350)
    st.plotly_chart(fig5, use_container_width=True)

with col6:
    cog_df = (
        df.groupby("cognitive_load", as_index=False)
        .agg(drop_prob=("drop_off_probability", "mean"),
             avg_watch=("avg_watch_percentage", "mean"))
    )
    fig6 = go.Figure()
    fig6.add_trace(go.Bar(
        x=cog_df["cognitive_load"], y=cog_df["drop_prob"] * 100,
        name="Avg Drop-off Prob %",
        marker=dict(
            color=cog_df["drop_prob"],
            colorscale=[[0, SAFE], [0.5, ACCENT], [1, DANGER]],
            showscale=False
        ),
        text=(cog_df["drop_prob"] * 100).map(lambda v: f"{v:.1f}%"),
        textposition="outside", textfont=dict(color="#eeeeff", size=10)
    ))
    dark_layout(fig6, "Cognitive Load vs Drop-off Probability", height=350)
    fig6.update_xaxes(title_text="Cognitive Load Score (1–10)",
                      tickvals=cog_df["cognitive_load"].tolist())
    fig6.update_yaxes(title_text="Avg Drop-off Prob %")
    st.plotly_chart(fig6, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# ROW 4 — Attention pie + Skip intro + Night safe
# ─────────────────────────────────────────────────────────────────────────────
col7, col8, col9 = st.columns(3)

with col7:
    att_df = df["attention_required"].value_counts().reset_index()
    att_df.columns = ["attention", "count"]
    fig7 = px.pie(
        att_df, names="attention", values="count", hole=0.6,
        color="attention", color_discrete_map={"high": DANGER, "medium": INFO}
    )
    fig7.update_traces(textinfo="percent+label", textfont_color="#eeeeff")
    dark_layout(fig7, "Attention Required Split", height=300)
    st.plotly_chart(fig7, use_container_width=True)

with col8:
    skip_df = df["skip_intro"].map({0: "Watched Intro", 1: "Skipped Intro"}).value_counts().reset_index()
    skip_df.columns = ["type", "count"]
    fig8 = px.pie(
        skip_df, names="type", values="count", hole=0.6,
        color_discrete_sequence=[PURPLE, "rgba(155,127,245,0.25)"]
    )
    fig8.update_traces(textinfo="percent+label", textfont_color="#eeeeff")
    dark_layout(fig8, "Skip Intro Behaviour", height=300)
    st.plotly_chart(fig8, use_container_width=True)

with col9:
    night_df = df["night_watch_safe"].map({0: "Not Night-Safe", 1: "Night-Safe"}).value_counts().reset_index()
    night_df.columns = ["type", "count"]
    fig9 = px.pie(
        night_df, names="type", values="count", hole=0.6,
        color_discrete_sequence=[INFO, "rgba(77,166,255,0.2)"]
    )
    fig9.update_traces(textinfo="percent+label", textfont_color="#eeeeff")
    dark_layout(fig9, "Night Watch Safety", height=300)
    st.plotly_chart(fig9, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# ROW 5 — Pacing score vs watch % + Scatter drop-off prob vs watch
# ─────────────────────────────────────────────────────────────────────────────
col10, col11 = st.columns(2)

with col10:
    pacing_df = (
        df.groupby("pacing_score", as_index=False)
        .agg(avg_watch=("avg_watch_percentage", "mean"),
             drop_prob=("drop_off_probability", "mean"))
    )
    fig10 = make_subplots(specs=[[{"secondary_y": True}]])
    fig10.add_trace(go.Scatter(
        x=pacing_df["pacing_score"], y=pacing_df["avg_watch"],
        mode="lines+markers", name="Avg Watch %",
        line=dict(color=INFO, width=2),
        marker=dict(size=8, color=INFO),
        fill="tozeroy", fillcolor="rgba(77,166,255,0.07)"
    ), secondary_y=False)
    fig10.add_trace(go.Scatter(
        x=pacing_df["pacing_score"], y=pacing_df["drop_prob"] * 100,
        mode="lines+markers", name="Drop-off Prob %",
        line=dict(color=DANGER, width=2, dash="dot"),
        marker=dict(size=7, color=DANGER)
    ), secondary_y=True)
    fig10.update_xaxes(title_text="Pacing Score", gridcolor=GRID_CLR, color=FONT_CLR)
    fig10.update_yaxes(title_text="Avg Watch %", secondary_y=False,
                       gridcolor=GRID_CLR, color=FONT_CLR)
    fig10.update_yaxes(title_text="Drop-off Prob %", secondary_y=True,
                       gridcolor=GRID_CLR, color=DANGER)
    dark_layout(fig10, "Pacing Score vs Avg Watch & Drop-off Probability", height=340)
    st.plotly_chart(fig10, use_container_width=True)

with col11:
    sample = df.sample(min(1000, len(df)), random_state=42)
    risk_colors = {"high": DANGER, "medium": ACCENT, "low": SAFE}
    fig11 = px.scatter(
        sample, x="cognitive_load", y="drop_off_probability",
        color="retention_risk",
        color_discrete_map=risk_colors,
        size="avg_watch_percentage",
        size_max=14,
        hover_data=["title", "platform", "hook_strength"],
        opacity=0.7,
    )
    dark_layout(fig11, "Cognitive Load vs Drop-off Probability (Scatter)", height=340)
    fig11.update_xaxes(title_text="Cognitive Load (1–10)")
    fig11.update_yaxes(title_text="Drop-off Probability (0–1)")
    st.plotly_chart(fig11, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# ROW 6 — Dialogue density bar + Visual intensity bar
# ─────────────────────────────────────────────────────────────────────────────
col12, col13 = st.columns(2)

with col12:
    if "dialogue_density" in df.columns:
        dd_df = (
            df.groupby("dialogue_density", as_index=False)
            .agg(avg_watch=("avg_watch_percentage", "mean"),
                 drop_prob=("drop_off_probability", "mean"),
                 count=("drop_off", "count"))
            .sort_values("avg_watch", ascending=False)
        )
        fig12 = px.bar(
            dd_df, x="dialogue_density", y="avg_watch",
            color="avg_watch",
            color_continuous_scale=[[0, DANGER], [0.5, ACCENT], [1, SAFE]],
            text=dd_df["avg_watch"].map(lambda v: f"{v:.1f}%"),
        )
        fig12.update_traces(textposition="outside", textfont_color="#eeeeff")
        fig12.update_coloraxes(showscale=False)
        dark_layout(fig12, "Dialogue Density vs Avg Watch %", height=320)
        fig12.update_xaxes(title_text="Dialogue Density Level")
        st.plotly_chart(fig12, use_container_width=True)

with col13:
    vi_df = (
        df.groupby("visual_intensity", as_index=False)
        .agg(avg_watch=("avg_watch_percentage", "mean"),
             drop_prob=("drop_off_probability", "mean"))
        .sort_values("visual_intensity")
    )
    fig13 = go.Figure()
    fig13.add_trace(go.Scatter(
        x=vi_df["visual_intensity"], y=vi_df["avg_watch"],
        mode="lines+markers", name="Avg Watch %",
        line=dict(color=PURPLE, width=2),
        marker=dict(size=8, color=PURPLE),
        fill="tozeroy", fillcolor="rgba(155,127,245,0.08)"
    ))
    dark_layout(fig13, "Visual Intensity vs Avg Watch %", height=320)
    fig13.update_xaxes(title_text="Visual Intensity Score (1–10)",
                       tickvals=vi_df["visual_intensity"].tolist())
    fig13.update_yaxes(title_text="Avg Watch %")
    st.plotly_chart(fig13, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# ROW 7 — Episode duration histogram + Pause/Rewind counts
# ─────────────────────────────────────────────────────────────────────────────
col14, col15 = st.columns(2)

with col14:
    fig14 = px.histogram(
        df, x="episode_duration_min",
        color="retention_risk",
        color_discrete_map={"high": DANGER, "medium": ACCENT, "low": SAFE},
        nbins=30, barmode="overlay", opacity=0.75
    )
    dark_layout(fig14, "Episode Duration Distribution by Risk Level", height=320)
    fig14.update_xaxes(title_text="Episode Duration (min)")
    fig14.update_yaxes(title_text="Episode Count")
    st.plotly_chart(fig14, use_container_width=True)

with col15:
    pw_df = (
        df.groupby("platform", as_index=False)
        .agg(avg_pause=("pause_count", "mean"),
             avg_rewind=("rewind_count", "mean"))
        .sort_values("avg_pause", ascending=False)
        .head(8)
    )
    fig15 = go.Figure()
    fig15.add_trace(go.Bar(
        name="Avg Pause Count", x=pw_df["platform"], y=pw_df["avg_pause"],
        marker_color=INFO, opacity=0.85
    ))
    fig15.add_trace(go.Bar(
        name="Avg Rewind Count", x=pw_df["platform"], y=pw_df["avg_rewind"],
        marker_color=PURPLE, opacity=0.85
    ))
    fig15.update_layout(barmode="group", xaxis_tickangle=-30)
    dark_layout(fig15, "Avg Pause & Rewind Count by Platform", height=320)
    st.plotly_chart(fig15, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# DATA TABLE (filterable)
# ─────────────────────────────────────────────────────────────────────────────
st.divider()
st.markdown("### 🗂️ Episode-level Data Explorer")
st.markdown(
    f"<p style='color:#6a6a9a;font-size:12px;'>Showing <b style='color:#f5a623'>{len(df):,}</b> "
    f"filtered episodes from {df['show_id'].nunique()} unique shows</p>",
    unsafe_allow_html=True
)

tbl_cols = [
    "title", "platform", "genre", "season_number", "episode_number",
    "avg_watch_percentage", "hook_strength", "cognitive_load",
    "attention_required", "retention_risk", "drop_off", "drop_off_probability",
    "pacing_score", "pause_count", "rewind_count", "night_watch_safe"
]
tbl_df = df[tbl_cols].copy()
tbl_df.columns = [c.replace("_", " ").title() for c in tbl_cols]

search = st.text_input("🔍 Search by Show Title", placeholder="e.g. Stranger Things")
if search:
    tbl_df = tbl_df[tbl_df["Title"].str.contains(search, case=False, na=False)]

sort_col = st.selectbox(
    "Sort by",
    ["Avg Watch Percentage", "Drop Off Probability", "Hook Strength", "Cognitive Load"],
    index=1
)
sort_asc = st.checkbox("Ascending", value=False)
tbl_df = tbl_df.sort_values(sort_col, ascending=sort_asc)

st.dataframe(
    tbl_df,
    use_container_width=True,
    height=450,
    column_config={
        "Avg Watch Percentage": st.column_config.ProgressColumn(
            "Avg Watch %", format="%d%%", min_value=0, max_value=100
        ),
        "Drop Off Probability": st.column_config.ProgressColumn(
            "Drop-off Prob", format="%.3f", min_value=0, max_value=1
        ),
        "Hook Strength": st.column_config.NumberColumn("Hook Strength", format="%d/10"),
        "Cognitive Load": st.column_config.NumberColumn("Cognitive Load", format="%d/10"),
        "Retention Risk": st.column_config.TextColumn("Retention Risk"),
        "Drop Off": st.column_config.CheckboxColumn("Dropped?"),
    }
)

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    "<p style='text-align:center;color:#4a4a70;font-size:11px;'>"
    "Data: <b style='color:#f5a623'>OTT Viewer Drop-off & Retention Dataset v1.0</b> · "
    "TMDB metadata · Synthetic engagement signals · Educational use only"
    "</p>",
    unsafe_allow_html=True
)