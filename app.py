import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="PENG Strategy Portal", layout="wide")

@st.cache_data
def load_data():
    return pd.read_csv('dashboard_database.csv')

try:
    df = load_data()
except Exception as e:
    st.error(f"⚠️ Error: {e}")
    st.stop()

# --- SIDEBAR ---
st.sidebar.title("🔍 PENG Navigation")
all_teams = sorted(df['Team'].unique())
selected_team = st.sidebar.selectbox("🎯 View Selection", ["Global Overview"] + list(all_teams))

# --- MAIN DASHBOARD ---
st.title("🚀 Engineering Initiatives Portal")

if selected_team == "Global Overview":
    # --- GLOBAL METRICS (Absolute Totals) ---
    # We group by Initiative to avoid counting hours multiple times per deliverable
    init_summary = df.groupby('Initiative').agg({
        'Logged_Hours': 'first',
        'Estimated_Hours': 'first',
        'Burnup': 'first'
    }).reset_index()

    total_est = init_summary['Estimated_Hours'].sum()
    total_logged = init_summary['Logged_Hours'].sum()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Estimated Hours", f"{int(total_est):,} hrs")
    with col2:
        st.metric("Total Logged (Burned)", f"{int(total_logged):,} hrs")
    with col3:
        active = init_summary[init_summary['Logged_Hours'] > 0]['Initiative'].nunique()
        st.metric("Active Initiatives", f"{active} of {len(init_summary)}")

    st.markdown("---")

    # --- TEAM CHART (Absolute Logged Hours) ---
    st.subheader("🔥 Total Logged Hours by Team")
    # Grouping by team and summing the unique initiative hours
    team_hours = df.groupby(['Team', 'Initiative'])['Logged_Hours'].first().reset_index()
    team_totals = team_hours.groupby('Team')['Logged_Hours'].sum().reset_index().sort_values('Logged_Hours')
    
    fig = px.bar(team_totals, x='Logged_Hours', y='Team', orientation='h', 
                 title="Total Burned Hours per Team",
                 color='Logged_Hours', color_continuous_scale='Reds',
                 labels={'Logged_Hours': 'Total Hours Logged'})
    st.plotly_chart(fig, use_container_width=True)

else:
    # --- TEAM SPECIFIC VIEW ---
    st.subheader(f"🛡️ {selected_team} Portfolio")
    team_df = df[df['Team'] == selected_team]
    inits = team_df[['Initiative', 'Burnup', 'Logged_Hours', 'Estimated_Hours']].drop_duplicates()
    
    for _, row in inits.iterrows():
        col_left, col_right = st.columns([3, 1])
        with col_left:
            st.write(f"### {row['Initiative']}")
            st.progress(min(float(row['Burnup'])/100, 1.0))
        with col_right:
            st.write("**Hours Burned**")
            st.write(f"{int(row['Logged_Hours'])} / {int(row['Estimated_Hours'])}")
        
        with st.expander("📋 View Deliverables"):
            st.table(team_df[team_df['Initiative'] == row['Initiative']][['Deliverable', 'Done']])
