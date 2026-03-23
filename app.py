import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="PENG Strategy Portal", layout="wide")

@st.cache_data(ttl=5)
def load_data():
    df = pd.read_csv('dashboard_database.csv')
    df.columns = df.columns.str.strip()
    # Ensure all numeric columns are handled
    cols = ['Burnup', 'Logged_Hours', 'Estimated_Hours', 'Maint_Hours']
    for col in cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

try:
    df = load_data()
    view = st.sidebar.selectbox("🎯 Select View", ["Global Overview"] + sorted(df['Team'].unique().tolist()), key="nav_v5")

    if view == "Global Overview":
        st.title("🌍 Global Strategy Overview")
        
        # Calculations
        init_sum = df.groupby('Initiative').agg({
            'Logged_Hours': 'first', 
            'Estimated_Hours': 'first',
            'Maint_Hours': 'first'
        }).reset_index()
        
        # Tiles logic
        t_est = init_sum['Estimated_Hours'].sum()
        t_burn = init_sum['Logged_Hours'].sum()
        t_maint = init_sum['Maint_Hours'].sum()
        over_budget = len(init_sum[init_sum['Logged_Hours'] > init_sum['Estimated_Hours']])
        active = len(init_sum[init_sum['Logged_Hours'] > 0])
        planned = len(init_sum[init_sum['Logged_Hours'] == 0])

        # --- ROW 1: CAPACITY & BUDGET ---
        c1, c2, c3 = st.columns(3)
        c1.metric("Est. vs Burned Hours", f"{int(t_est):,} / {int(t_burn):,}")
        c2.metric("Maintenance Logged", f"{int(t_maint):,} hrs")
        c3.metric("Over Budget Initiatives", f"{over_budget}", delta_color="inverse")

        # --- ROW 2: INITIATIVE STATUS ---
        c4, c5, c6 = st.columns(3)
        c4.metric("Total Initiatives", len(init_sum))
        c5.metric("Active", active)
        c6.metric("Planned", planned)

        st.markdown("---")

        # --- CHART 1: Team Est vs Logged ---
        st.subheader("📊 Team Capacity: Estimated vs. Logged")
        team_totals = df.groupby(['Team', 'Initiative']).agg({'Estimated_Hours':'first', 'Logged_Hours':'first'}).reset_index()
        team_final = team_totals.groupby('Team').sum().reset_index()
        
        fig1 = go.Figure(data=[
            go.Bar(name='Estimated', x=team_final['Team'], y=team_final['Estimated_Hours'], marker_color='#1f77b4'),
            go.Bar(name='Logged', x=team_final['Team'], y=team_final['Logged_Hours'], marker_color='#d62728')
        ])
        fig1.update_layout(barmode='group', height=400)
        st.plotly_chart(fig1, use_container_width=True)

        # --- CHART 2: Maintenance Chart ---
        st.subheader("🔧 Maintenance Hours per Team")
        team_maint = df.groupby(['Team', 'Initiative'])['Maint_Hours'].first().reset_index()
        maint_final = team_maint.groupby('Team')['Maint_Hours'].sum().reset_index()
        fig2 = px.bar(maint_final, x='Team', y='Maint_Hours', color='Maint_Hours', color_continuous_scale='Oranges')
        st.plotly_chart(fig2, use_container_width=True)

    else:
        # Team detail view (same as before)
        st.title(f"🛡️ {view} Portfolio")
        tdf = df[df['Team'] == view]
        for _, row in tdf[['Initiative', 'Burnup', 'Logged_Hours', 'Estimated_Hours']].drop_duplicates().iterrows():
            st.subheader(row['Initiative'])
            st.progress(max(0.0, min(float(row['Burnup'])/100.0, 1.0)))
            st.write(f"**Burn:** {int(row['Logged_Hours'])} / {int(row['Estimated_Hours'])} hrs")
            with st.expander("Show Deliverables"):
                st.table(tdf[tdf['Initiative'] == row['Initiative']][['Deliverable', 'Done']])

except Exception as e:
    st.error(f"Waiting for CSV column update: {e}")
