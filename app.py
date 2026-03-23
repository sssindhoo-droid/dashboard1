import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="PENG Strategy Portal", layout="wide")

@st.cache_data(ttl=5)
def load_data():
    df = pd.read_csv('dashboard_database.csv')
    df.columns = df.columns.str.strip()
    for col in ['Burnup', 'Logged_Hours', 'Estimated_Hours', 'Maint_Hours']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

try:
    df = load_data()
    view = st.sidebar.selectbox("🎯 Select View", ["Global Overview"] + sorted(df['Team'].unique().tolist()), key="nav_final_v3")

    if view == "Global Overview":
        st.title("🌍 Global Strategy Overview")
        
        # --- FIXED MATH LOGIC ---
        # Get one row per unique initiative per team
        unique_inits = df.groupby(['Team', 'Initiative']).agg({
            'Logged_Hours': 'first', 
            'Estimated_Hours': 'first',
            'Maint_Hours': 'first'
        }).reset_index()
        
        t_est = unique_inits['Estimated_Hours'].sum()
        t_burn = unique_inits['Logged_Hours'].sum()
        t_maint = unique_inits['Maint_Hours'].sum()
        
        active = len(unique_inits[unique_inits['Logged_Hours'] > 0])
        planned = len(unique_inits[unique_inits['Logged_Hours'] == 0])
        over_budget = len(unique_inits[unique_inits['Logged_Hours'] > unique_inits['Estimated_Hours']])

        # --- METRIC TILES ---
        c1, c2, c3 = st.columns(3)
        c1.metric("Est. vs Burned Hours", f"{int(t_est):,} / {int(t_burn):,}")
        c2.metric("Maintenance Logged", f"{int(t_maint):,} hrs")
        c3.metric("Over Budget Initiatives", f"{over_budget}", delta_color="inverse")

        c4, c5, c6 = st.columns(3)
        c4.metric("Total Initiatives", len(unique_inits)) # Correct count
        c5.metric("Active", active)
        c6.metric("Planned", planned)

        st.markdown("---")

        # --- CHART 1: Est vs Logged (Per Team) ---
        st.subheader("📊 Team Capacity: Estimated vs. Logged")
        team_final = unique_inits.groupby('Team').sum().reset_index()
        
        fig1 = go.Figure(data=[
            go.Bar(name='Estimated', x=team_final['Team'], y=team_final['Estimated_Hours'], marker_color='#1f77b4'),
            go.Bar(name='Logged', x=team_final['Team'], y=team_final['Logged_Hours'], marker_color='#d62728')
        ])
        fig1.update_layout(barmode='group', height=400)
        st.plotly_chart(fig1, use_container_width=True)

        # --- CHART 2: Maintenance Per Team ---
        st.subheader("🔧 Maintenance Hours per Team")
        maint_final = unique_inits.groupby('Team')['Maint_Hours'].sum().reset_index()
        fig2 = px.bar(maint_final, x='Team', y='Maint_Hours', color='Maint_Hours', color_continuous_scale='Oranges')
        st.plotly_chart(fig2, use_container_width=True)

    else:
        st.title(f"🛡️ {view} Portfolio")
        tdf = df[df['Team'] == view]
        # Group by initiative to show progress bars
        inits_list = tdf.groupby('Initiative').agg({'Burnup':'first', 'Logged_Hours':'first', 'Estimated_Hours':'first'}).reset_index()
        
        for _, row in inits_list.iterrows():
            st.subheader(row['Initiative'])
            st.progress(max(0.0, min(float(row['Burnup'])/100.0, 1.0)))
            st.write(f"**Burn:** {int(row['Logged_Hours'])} / {int(row['Estimated_Hours'])} hrs")
            with st.expander("Show Deliverables"):
                st.table(tdf[tdf['Initiative'] == row['Initiative']][['Deliverable', 'Done']])

except Exception as e:
    st.error(f"Error: {e}")
