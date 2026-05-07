import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from logic.data_models import Baseline
from logic.energy_logic import load_and_clean_csv, process_consumption_data

def render_tab1():
    """
    Renders the UI and logic for the Baseline Data Input tab.
    Allows users to upload load profiles, view key metrics (Peak, Total Consumption),
    and save them as Baseline scenarios for further evaluation.
    """
    st.header("Baseline Grid & Consumption Data")
    st.markdown("Upload your current load profile to establish the status quo before applying energy solutions.")

    # ---------------------------------------------------------
    # SECTION 1: OVERVIEW OF SAVED BASELINES (Read & Delete)
    # ---------------------------------------------------------
    if 'baselines' not in st.session_state:
        st.session_state['baselines'] = []

    if st.session_state['baselines']:
        st.subheader("Saved Baselines")
        for index, base in enumerate(st.session_state['baselines']):
            with st.expander(f"📊 Baseline: {base.name} | Limit: {base.grid_limit_kw} kW"):
                # Display quick facts about the saved baseline
                col_a, col_b, col_c = st.columns(3)
                max_peak = base.raw_data['consumption_kw'].max()
                # 15 min intervals = 0.25 hours
                total_kwh = base.raw_data['consumption_kw'].sum() * 0.25 
                
                col_a.metric("Max Peak", f"{max_peak:.1f} kW")
                col_b.metric("Grid Limit", f"{base.grid_limit_kw:.1f} kW")
                col_c.metric("Total Consumption", f"{total_kwh:,.0f} kWh")
                
                # Delete button
                if st.button(f"🗑️ Delete '{base.name}'", key=f"del_base_{index}"):
                    st.session_state['baselines'].pop(index)
                    st.rerun()
        st.divider()

    # ---------------------------------------------------------
    # SECTION 2: UPLOAD & ANALYZE NEW BASELINE
    # ---------------------------------------------------------
    st.subheader("Create New Baseline")
    
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            base_name = st.text_input("Baseline Name", placeholder="e.g., Facility Alpha - 2023")
        with col2:
            grid_limit = st.number_input("Current Grid Limit (kW)", min_value=0.0, value=150.0, step=10.0)

        uploaded_file = st.file_uploader("Upload Load Profile (CSV)", type=['csv'])

        if uploaded_file:
            try:
                # 1. Load and process the data using our logic engine
                raw_df = load_and_clean_csv(uploaded_file)
                # Hardcoded to 15 minutes as per standard industry profile
                processed_df = process_consumption_data(raw_df, interval_minutes=15)
                
                # 2. Calculate Key Performance Indicators (KPIs)
                peak_demand = processed_df['consumption_kw'].max()
                avg_demand = processed_df['consumption_kw'].mean()
                # Sum of kW * 0.25h gives us total kWh for 15-minute interval data
                total_consumption_kwh = processed_df['consumption_kw'].sum() * 0.25
                limit_breaches = (processed_df['consumption_kw'] > grid_limit).sum()

                # 3. Display the KPIs
                st.markdown("#### Load Profile Analysis")
                kpi1, kpi2, kpi3, kpi4 = st.columns(4)
                
                kpi1.metric("Maximum Peak", f"{peak_demand:.1f} kW", 
                            delta=f"{(peak_demand - grid_limit):.1f} kW over limit" if peak_demand > grid_limit else "Within limit",
                            delta_color="inverse")
                kpi2.metric("Annual Consumption", f"{total_consumption_kwh:,.0f} kWh")
                kpi3.metric("Average Load", f"{avg_demand:.1f} kW")
                kpi4.metric("Grid Limit Breaches", f"{limit_breaches} events", 
                            delta="Requires attention" if limit_breaches > 0 else "Safe", 
                            delta_color="inverse")

                # 4. Display visual chart
                st.markdown("#### Load Profile Chart")
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=processed_df['timestamp'], 
                    y=processed_df['consumption_kw'], 
                    mode='lines', 
                    name='Consumption',
                    line=dict(color='#A9A9A9', width=1)
                ))
                fig.add_hline(
                    y=grid_limit, 
                    line_dash="dash", 
                    line_color="red", 
                    annotation_text="Grid Limit"
                )
                fig.update_layout(yaxis_title="Power (kW)", xaxis_title="Time", height=400)
                st.plotly_chart(fig, use_container_width=True)

                # 5. Save Button
                if st.button("💾 Save as Baseline Scenario", type="primary"):
                    if not base_name:
                        st.error("Please provide a name for this Baseline before saving.")
                    elif any(b.name == base_name for b in st.session_state['baselines']):
                        st.error("A Baseline with this name already exists.")
                    else:
                        new_baseline = Baseline(
                            name=base_name, 
                            raw_data=processed_df, 
                            grid_limit_kw=grid_limit
                        )
                        st.session_state['baselines'].append(new_baseline)
                        st.success(f"Baseline '{base_name}' saved successfully!")
                        st.rerun() # Refresh to show it in the overview list

            except Exception as e:
                st.error(f"Failed to process the uploaded file. Ensure it is a valid time-series CSV. Error details: {e}")