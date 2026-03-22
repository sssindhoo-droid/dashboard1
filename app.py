import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="PENG Strategy Portal", layout="wide")

# --- 2. DATA LOADING (Updated for Stability) ---
@st.cache_data(show_spinner=False)
def load_data():
    df = pd.read_csv('dashboard_database.csv')
    # Ensure columns are numeric to prevent errors
    df['Burnup'] = pd.to_numeric(df['Burnup'], errors='coerce').fillna(0)
    df['Logged_Hours'] = pd.to_numeric(df['Logged_Hours'], errors='coerce').fillna(0)
    df['Estimated_Hours'] = pd.to_numeric(df['Estimated_Hours'], errors='coerce').fillna(0)
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"⚠️ Error loading database: {e}")
    st.stop()

# --- 3. SIDEBAR NAVIGATION ---
st.sidebar.title("🔍 PENG Navigation")
all_teams = sorted(df['Team'].unique().tolist())
# We add a unique 'key' to fix the switching bug
selected_team = st.sidebar.selectbox(
    "🎯 Select a View", 
    ["Global Overview"] + all_teams,
    key="team_selector_widget"
)

st.sidebar.markdown("---")
st.sidebar.info("Dashboard auto-syncs with your Excel tracking.")

# --- 4. MAIN PAGE ---
st.title("🚀 Engineering Initiatives Portal")

if selected_team == "Global Overview":
    # --- METRICS SECTION ---
    # Group by Initiative to get unique hour counts
    init_sum = df.groupby('Initiative').agg({
        'Logged_Hours': 'first',
        'Estimated_Hours': 'first'
    }).reset_index()

    t_est = init_sum['Estimated_Hours'].sum()
    t_burn = init_sum['Logged_Hours'].sum()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Organization Capacity (Est)", f"{int(t_est):,} hrs")
    with col2:
        st.metric("Total Burned Hours (Logged)", f"{int(t_burn):,} hrs")
    with col3:
        active_c = init_sum[init_sum['Logged_Hours'] > 0]['Initiative'].nunique()
        st.metric("Active Initiatives", f"{active_c} / {len(init_sum)}")

    st.markdown("---")

    # --- ABSOLUTE TEAM PROGRESS CHART ---
    st.subheader("🔥 Total Logged Hours per Team (Absolute Values)")
    # Correctly sum unique initiative hours per team
    team_hours = df.groupby(['Team', 'Initiative'])['Logged_Hours'].first().reset_index()
    team_abs = team_hours.groupby('Team')['Logged_Hours'].sum().reset_index().sort_values('Logged_Hours')
    
    fig = px.bar(team_abs, x='Logged_Hours', y='Team', orientation='h', 
                 color='Logged_Hours', color_continuous_scale='Reds',
                 labels={'Logged_Hours': 'Total Burned Hours'})
    st.plotly_chart(fig, use_container_width=True)

else:
    # --- TEAM SPECIFIC VIEW ---
    st.subheader(f"🛡️ {selected_team} Initiative Portfolio")
    team_df = df[df['Team'] == selected_team]
    
    # Initiative Drill-down
    team_inits = team_df[['Initiative', 'Burnup', 'Logged_Hours', 'Estimated_Hours']].drop_duplicates()
    
    for _, row in team_inits.iterrows():
        c_left, c_right = st.columns([4, 1])
        with c_left:
            st.write(f"### {row['Initiative']}")
            st.progress(min(float(row['Burnup'])/100.0, 1.0))
        with c_right:
            st.write("**Hours Burned**")
            st.write(f"{int(row['Logged_Hours'])} / {int(row['Estimated_Hours'])}")
        
        with st.expander(f"📋 View Deliverables ({selected_team})"):
            deliv_table = team_df[team_df['Initiative'] == row['Initiative']][['Deliverable', 'Done']]
            st.table(deliv_table)
        st.markdown("<br>", unsafe_allow_value=True)
