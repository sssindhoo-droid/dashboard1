import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="PENG Strategy Portal", layout="wide")

@st.cache_data(ttl=10)
def load_data():
    df = pd.read_csv('dashboard_database.csv')
    df.columns = df.columns.str.strip()
    for col in ['Burnup', 'Logged_Hours', 'Estimated_Hours', 'Maint_Hours']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

try:
    df = load_data()
    view = st.sidebar.selectbox("🎯 Select View", ["Global Overview"] + sorted(df['Team'].unique().tolist()), key="nav_final")

    if view == "Global Overview":
        st.title("🚀 Global Strategy & Capacity Overview")
        
        # --- CALCULATION LOGIC ---
        init_sum = df.groupby('Initiative').agg({
            'Logged_Hours': 'first', 
            'Estimated_Hours': 'first',
            'Maint_Hours': 'first'
        }).reset_index()
        
        total_est = init_sum['Estimated_Hours'].sum()
        total_burn = init_sum['Logged_Hours'].sum()
        total_maint = init_sum['Maint_Hours'].sum()
        over_budget = len(init_sum[init_sum['Logged_Hours'] > init_sum['Estimated_Hours']])
        active = len(init_sum[init_sum['Logged_Hours'] > 0])
        planned = len(init_sum[init_sum['Logged_Hours'] == 0])

        # --- TILES (Row 1) ---
        col1, col2, col3 = st.columns(3)
        col1.metric("Capacity: Est vs Burned", f"{int(total_est):,} / {int(total_burn):,}", f"{int(total_est - total_burn)} left")
        col2.metric("Initiatives: Total (Act/Plan)", f"{len(init_sum)} ({active} / {planned})")
        col3.metric("Over Budget Warning", f"{over_budget} Initiatives", delta=over_budget, delta_color="inverse")

        # --- TILES (Row 2) ---
        col4, col5 = st.columns(2)
        col4.metric("Maintenance Burden", f"{int(total_maint):,} hrs", "Hours logged to Maint")
        
        st.markdown("---")

        # --- CHART 1: TEAM CAPACITY (EST VS LOGGED) ---
        st.subheader("📊 Team Capacity: Estimated vs. Logged Hours")
        team_data = df.groupby(['Team', 'Initiative']).agg({'Estimated_Hours':'first', 'Logged_Hours':'first'}).reset_index()
        team_totals = team_data.groupby('Team').sum().reset_index()

        fig1 = go.Figure(data=[
            go.Bar(name='Estimated', x=team_totals['Team'], y=team_totals['Estimated_Hours'], marker_color='#1f77b4'),
            go.Bar(name='Logged (Burned)', x=team_totals['Team'], y=team_totals['Logged_Hours'], marker_color='#d62728')
        ])
        fig1.update_layout(barmode='group', height=400)
        st.plotly_chart(fig1, use_container_width=True)

        # --- CHART 2: MAINTENANCE BURDEN ---
        st.subheader("🔧 Maintenance Logged Hours per Team")
        maint_data = df.groupby(['Team', 'Initiative'])['Maint_Hours'].first().reset_index()
        maint_totals = maint_data.groupby('Team')['Maint_Hours'].sum().reset_index()
        
        fig2 = px.bar(maint_totals, x='Team', y='Maint_Hours', color='Maint_Hours', color_continuous_scale='Oranges')
        st.plotly_chart(fig2, use_container_width=True)

    else:
        # (Team Detail View Logic remains same as previous version)
        st.title(f"🛡️ {view} Portfolio")
        tdf = df[df['Team'] == view]
        for _, row in tdf[['Initiative', 'Burnup', 'Logged_Hours', 'Estimated_Hours']].drop_duplicates().iterrows():
            st.subheader(row['Initiative'])
            st.progress(max(0.0, min(float(row['Burnup'])/100.0, 1.0)))
            st.write(f"**Burn:** {int(row['Logged_Hours'])} / {int(row['Estimated_Hours'])} hrs")

except Exception as e:
    st.error(f"Waiting for updated CSV: {e}")
