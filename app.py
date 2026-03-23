import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="PENG Strategy Portal", layout="wide")

@st.cache_data(ttl=5)
def load_data():
    df = pd.read_csv('dashboard_database.csv')
    # Standardize column names to remove hidden spaces
    df.columns = df.columns.str.strip()
    # Force columns to be numbers
    cols = ['Burnup', 'Logged_Hours', 'Estimated_Hours']
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

try:
    df = load_data()
    
    # 🚨 Fix for KeyError: Verify columns exist
    required = ['Team', 'Initiative', 'Logged_Hours', 'Estimated_Hours']
    missing = [c for c in required if c not in df.columns]
    if missing:
        st.error(f"❌ CSV is missing columns: {missing}")
        st.stop()

    # Sidebar with UNIQUE KEY to fix switching bug
    teams = sorted(df['Team'].unique().tolist())
    view = st.sidebar.selectbox("🎯 Select View", ["Global Overview"] + teams, key="nav_fix_26")

    if view == "Global Overview":
        st.title("🚀 Global Strategy Overview")
        col1, col2 = st.columns(2)
        
        # Absolute Chart
        team_hrs = df.groupby(['Team', 'Initiative'])['Logged_Hours'].first().reset_index()
        team_abs = team_hrs.groupby('Team')['Logged_Hours'].sum().reset_index().sort_values('Logged_Hours')
        
        fig = px.bar(team_abs, x='Logged_Hours', y='Team', orientation='h', 
                     title="Absolute Burned Hours by Team", color_continuous_scale='Reds')
        st.plotly_chart(fig, use_container_width=True)
        
        col1.metric("Total Hours Logged", f"{int(df.groupby('Initiative')['Logged_Hours'].first().sum()):,} hrs")

    else:
        st.title(f"🛡️ {view} Initiatives")
        tdf = df[df['Team'] == view]
        inits = tdf[['Initiative', 'Burnup', 'Logged_Hours', 'Estimated_Hours']].drop_duplicates()
        
        for _, row in inits.iterrows():
            st.subheader(row['Initiative'])
            st.progress(max(0.0, min(float(row['Burnup'])/100.0, 1.0)))
            st.write(f"**Status:** {int(row['Logged_Hours'])} / {int(row['Estimated_Hours'])} hrs burned")
            with st.expander("Show Deliverables"):
                st.table(tdf[tdf['Initiative'] == row['Initiative']][['Deliverable', 'Done']])

except Exception as e:
    st.error(f"Something went wrong: {e}")
