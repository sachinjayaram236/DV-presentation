import streamlit as st
import pandas as pd
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt

# ----------------------------
# PAGE CONFIG
# ----------------------------
st.set_page_config(page_title="OTT Retention Dashboard", layout="wide")

st.title("🎬 OTT Viewer Retention Dashboard")

# ----------------------------
# LOAD DATA
# ----------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("dataset.csv")
    return df

df = load_data()

# ----------------------------
# SIDEBAR FILTERS
# ----------------------------
st.sidebar.header("🔍 Filters")

platform = st.sidebar.multiselect("Platform", df["platform"].unique(), default=df["platform"].unique())
genre = st.sidebar.multiselect("Genre", df["genre"].unique(), default=df["genre"].unique())

year_range = st.sidebar.slider(
    "Release Year",
    int(df["release_year"].min()),
    int(df["release_year"].max()),
    (int(df["release_year"].min()), int(df["release_year"].max()))
)

filtered_df = df[
    (df["platform"].isin(platform)) &
    (df["genre"].isin(genre)) &
    (df["release_year"].between(year_range[0], year_range[1]))
]

# ----------------------------
# KPI CARDS
# ----------------------------
st.subheader("📊 Overview Metrics")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Avg Watch %", f"{filtered_df['avg_watch_percentage'].mean():.2f}")
col2.metric("Drop-off Rate", f"{filtered_df['drop_off'].mean()*100:.2f}%")
col3.metric("Avg Hook Strength", f"{filtered_df['hook_strength'].mean():.2f}")
col4.metric("Avg Cognitive Load", f"{filtered_df['cognitive_load'].mean():.2f}")

# ----------------------------
# SHOW SELECTION
# ----------------------------
st.subheader("🎥 Select Show")

selected_show = st.selectbox("Choose a Show", filtered_df["title"].unique())

show_df = filtered_df[filtered_df["title"] == selected_show]

# ----------------------------
# DROP-OFF TREND
# ----------------------------
st.subheader("📉 Episode Drop-off Trend")

fig1 = px.line(
    show_df,
    x="episode_number",
    y="drop_off_probability",
    color="season_number",
    markers=True,
    title="Drop-off Probability per Episode"
)

st.plotly_chart(fig1, use_container_width=True)

# ----------------------------
# RETENTION RISK DISTRIBUTION
# ----------------------------
st.subheader("⚠️ Retention Risk Distribution")

risk_counts = show_df["retention_risk"].value_counts().reset_index()
risk_counts.columns = ["risk", "count"]

fig2 = px.pie(risk_counts, values="count", names="risk", title="Risk Levels")

st.plotly_chart(fig2, use_container_width=True)

# ----------------------------
# SEASON-WISE ANALYSIS
# ----------------------------
st.subheader("📊 Season-wise Retention")

season_stats = show_df.groupby("season_number").agg({
    "avg_watch_percentage": "mean",
    "drop_off": "mean"
}).reset_index()

fig3 = px.bar(
    season_stats,
    x="season_number",
    y=["avg_watch_percentage", "drop_off"],
    barmode="group",
    title="Season Performance"
)

st.plotly_chart(fig3, use_container_width=True)

# ----------------------------
# SCATTER: BEHAVIOR ANALYSIS
# ----------------------------
st.subheader("🧠 Cognitive Load vs Drop-off")

fig4 = px.scatter(
    show_df,
    x="cognitive_load",
    y="drop_off_probability",
    color="retention_risk",
    size="pause_count",
    title="Cognitive Load Impact"
)

st.plotly_chart(fig4, use_container_width=True)

# ----------------------------
# CORRELATION HEATMAP
# ----------------------------
st.subheader("🔥 Feature Correlation")

# Select only numeric columns
corr_df = show_df.select_dtypes(include=['number'])

# Compute correlation
corr = corr_df.corr()

# Plot
fig, ax = plt.subplots()
sns.heatmap(corr, annot=True, cmap="coolwarm", ax=ax)

st.pyplot(fig)
# ----------------------------
# RISK TABLE
# ----------------------------
st.subheader("📋 Episode Risk Table")

st.dataframe(
    show_df.sort_values(by="drop_off_probability", ascending=False),
    use_container_width=True
)