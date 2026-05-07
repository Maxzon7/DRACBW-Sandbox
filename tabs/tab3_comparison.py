import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Import required business logic and PDF generator
from logic.energy_logic import simulate_battery_logic, get_exact_minimum_requirements
from functions.pdf_converter import generate_tech_pdf

def render_tab3():
    """
    Renders the Technical Scenario Comparison tab.
    Provides a high-level comparison matrix, a combined grid load chart,
    a single-scenario deep dive, and a PDF export feature.
    """
    st.header("Technical Scenario Comparison & Export")
    st.markdown("Evaluate the physical feasibility, energy flows, and export reports of your configured scenarios.")
    
    # Guardrail: Check if scenarios exist in memory
    if not st.session_state.get('sub_scenarios'):
        st.info("No sub-scenarios found. Please build and save your scenarios in Tab 2 first.")
        return

    st.subheader("1. Benchmark Overview")
    scenario_names = [s.name for s in st.session_state['sub_scenarios']]
    
    # Let user select which scenarios to compare
    selected_scenarios = st.multiselect(
        "Active Scenarios for Comparison", 
        options=scenario_names, 
        default=scenario_names
    )
    
    if not selected_scenarios:
        st.warning("Please select at least one scenario from the list above to view the comparison.")
        return

    tech_data = []
    simulated_data = {} # Our "Tupperware cabinet" to store results for the deep dive
    
    # Initialize the combined grid chart
    fig_combined_grid = go.Figure()
    
    # Grab the grid limit from the first selected scenario for the red warning line
    first_scenario = next(s for s in st.session_state['sub_scenarios'] if s.name == selected_scenarios[0])
    grid_limit = first_scenario.parent_baseline.grid_limit_kw
    
    fig_combined_grid.add_hline(
        y=grid_limit, 
        line_dash="dash", 
        line_color="red", 
        annotation_text="Grid Contract Limit",
        line_width=2
    )
    
    # --- CALCULATION LOOP ---
    for s_name in selected_scenarios:
        s = next(s for s in st.session_state['sub_scenarios'] if s.name == s_name)
        df_sim = s.parent_baseline.raw_data.copy()
        
        # 1. Solar Module Logic
        df_sim['solar_generation_kw'] = 0.0
        solar_cap_display = "0 kWp"
        
        if s.solar_params:
            solar_capacity = s.solar_params.get("capacity_kwp", 0)
            solar_cap_display = f"{solar_capacity} kWp"
            
            # Simplified dummy logic: Solar produces 60% of capacity between 08:00 and 18:00
            daylight_mask = (df_sim['timestamp'].dt.hour >= 8) & (df_sim['timestamp'].dt.hour <= 18)
            df_sim.loc[daylight_mask, 'solar_generation_kw'] = solar_capacity * 0.6
        
        # Calculate what is left for the grid/battery to handle
        df_sim['net_load_kw'] = df_sim['consumption_kw'] - df_sim['solar_generation_kw']
        df_sim['net_load_kw'] = df_sim['net_load_kw'].clip(lower=0) 
        
        # 2. Battery Module Logic
        df_sim['battery_soc_kwh'] = 0.0
        df_sim['battery_action_kw'] = 0.0
        battery_cap_display = "0 kWh"
        battery_enabled = False
        
        if s.battery_params:
            battery_enabled = True
            b_cap = s.battery_params.get("capacity_kwh", 0)
            b_pwr = s.battery_params.get("max_power_kw", 0)
            
            battery_cap_display = f"{b_cap} kWh"
            
            df_temp = df_sim.copy()
            df_temp['consumption_kw'] = df_temp['net_load_kw'] 
            
            # Run the heavy battery physics simulation
            df_res = simulate_battery_logic(df_temp, grid_limit, b_cap, b_pwr, interval_min=15)
            
            df_sim['final_grid_load_kw'] = df_res['final_grid_load_kw']
            df_sim['battery_soc_kwh'] = df_res['battery_soc_kwh']
            df_sim['battery_action_kw'] = df_res['battery_action_kw']
        else:
            # If no battery, the final grid load is just the net load
            df_sim['final_grid_load_kw'] = df_sim['net_load_kw']
        
        # 3. Save calculated data for later use (the "Tupperware")
        simulated_data[s.name] = {
            "df": df_sim,
            "battery_enabled": battery_enabled
        }
        
        # 4. KPI Matrix Calculations
        max_peak = df_sim['final_grid_load_kw'].max()
        blackout_events = (df_sim['final_grid_load_kw'] > grid_limit).sum()
        is_feasible = "Yes" if blackout_events == 0 else "No"
        
        tech_data.append({
            "Scenario Name": s.name,
            "Solar Installed": solar_cap_display,
            "Battery Capacity": battery_cap_display,
            "Max Grid Load (kW)": max_peak,
            "Grid Limit Breaches": blackout_events,
            "Technically Feasible": is_feasible
        })
        
        # Add trace to the combined grid chart
        fig_combined_grid.add_trace(go.Scatter(
            x=df_sim['timestamp'], 
            y=df_sim['final_grid_load_kw'], 
            name=s.name, 
            mode='lines', 
            line=dict(width=1.5), 
            opacity=0.8
        ))
    
    # --- RENDER OVERVIEW ---
    df_tech = pd.DataFrame(tech_data)
    
    def color_feasibility(val):
        """Applies green/red coloring for quick technical assessment."""
        color = '#00CC96' if val == "Yes" else '#FF4B4B'
        return f'color: {color}; font-weight: bold'
        
    styled_tech_df = df_tech.style.map(color_feasibility, subset=['Technically Feasible']).format({
        "Max Grid Load (kW)": "{:.1f}"
    })
    
    st.dataframe(styled_tech_df, use_container_width=True, hide_index=True)
    
    st.markdown("#### Combined Grid Load")
    st.markdown("Displays the final power draw from the grid for all active scenarios.")
    fig_combined_grid.update_layout(yaxis_title="Grid Power Draw (kW)", xaxis_title="Time", hovermode="x unified")
    st.plotly_chart(fig_combined_grid, use_container_width=True)
    
    # --- DEEP DIVE & EXPORT (SINGLE SCENARIO) ---
    st.divider()
    st.subheader("2. Deep Dive & PDF Export")
    st.markdown("Select a specific scenario to investigate internal energy flows and download the technical report.")
    
    detail_scenario_name = st.selectbox("Select Scenario", options=selected_scenarios)
    
    if detail_scenario_name:
        # Retrieve the pre-calculated data from our dictionary
        df_detail = simulated_data[detail_scenario_name]["df"]
        bat_enabled = simulated_data[detail_scenario_name]["battery_enabled"]
        s_detail_obj = next(s for s in st.session_state['sub_scenarios'] if s.name == detail_scenario_name)
        
        col1, col2 = st.columns(2)
        
        # Solar Detailed Chart
        if s_detail_obj.solar_params:
            with col1:
                st.markdown(f"**Solar Yield: {detail_scenario_name}**")
                fig_solar = go.Figure()
                fig_solar.add_trace(go.Scatter(
                    x=df_detail['timestamp'], 
                    y=df_detail['solar_generation_kw'], 
                    name="Solar Generation", mode='lines', fill='tozeroy', line=dict(color='#FFD700')
                ))
                fig_solar.update_layout(yaxis_title="Power (kW)", xaxis_title="Time", height=300, margin=dict(t=10, b=10))
                st.plotly_chart(fig_solar, use_container_width=True)
        else:
            with col1:
                st.info("No Solar PV installed in this scenario.")
                
        # Battery Detailed Chart
        if s_detail_obj.battery_params:
            with col2:
                st.markdown(f"**Battery State of Charge: {detail_scenario_name}**")
                fig_soc = go.Figure()
                fig_soc.add_trace(go.Scatter(
                    x=df_detail['timestamp'], 
                    y=df_detail['battery_soc_kwh'], 
                    name="Battery SoC", mode='lines', fill='tozeroy', line=dict(color='#636EFA')
                ))
                fig_soc.update_layout(yaxis_title="Stored Energy (kWh)", xaxis_title="Time", height=300, margin=dict(t=10, b=10))
                st.plotly_chart(fig_soc, use_container_width=True)
        else:
            with col2:
                st.info("No Battery Storage installed in this scenario.")
        
        # --- PDF GENERATION ---
        st.markdown("#### Technical Report Export")
        
        # We need to calculate the exact minimum requirements just for the PDF export
        peak_raw = df_detail['consumption_kw'].max()
        min_reqs = get_exact_minimum_requirements(df_detail, grid_limit, 15)
        
        metrics = {
            "grid_limit": grid_limit,
            "peak_raw": peak_raw,
            "min_pwr": min_reqs["min_power_kw"],
            "min_cap": min_reqs["true_min_capacity_kwh"]
        }
        
        if st.button(f"📄 Generate PDF for '{detail_scenario_name}'", type="primary"):
            with st.spinner("Rendering PDF... This might take a few seconds (Matplotlib is painting)."):
                try:
                    pdf_bytes = generate_tech_pdf(
                        report_title=f"Energy Analysis: {detail_scenario_name}",
                        metrics=metrics,
                        plot_data=df_detail,
                        battery_enabled=bat_enabled
                    )
                    
                    st.download_button(
                        label="📥 Download PDF Report",
                        data=pdf_bytes,
                        file_name=f"{detail_scenario_name.replace(' ', '_')}_Report.pdf",
                        mime="application/pdf",
                        type="primary"
                    )
                except Exception as e:
                    st.error(f"PDF Generation failed. Details: {e}")