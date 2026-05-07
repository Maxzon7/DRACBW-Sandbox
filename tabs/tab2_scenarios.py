import streamlit as st
from logic.data_models import SubScenario

def render_tab2():
    """
    Renders the UI and logic for configuring sub-scenarios.
    Allows creating new scenarios, viewing detailed data of existing ones,
    and editing or deleting them (CRUD operations).
    """
    st.header("Configure Solution Modules")
    
    # Guardrail: We need a baseline first before doing anything
    if not st.session_state.get('baselines'):
        st.info("Please create a Baseline in Tab 1 first before building sub-scenarios.")
        return
        
    # ---------------------------------------------------------
    # SECTION 1: OVERVIEW OF EXISTING SCENARIOS (Read & Delete)
    # ---------------------------------------------------------
    if st.session_state.get('sub_scenarios'):
        st.subheader("Current Sub-Scenarios Overview")
        
        # Loop through all saved scenarios and display their details
        for index, scenario in enumerate(st.session_state['sub_scenarios']):
            with st.expander(f"📦 Scenario: {scenario.name} (Base: {scenario.parent_baseline.name})"):
                col_info1, col_info2 = st.columns(2)
                
                with col_info1:
                    st.markdown("**🌞 Solar PV Details**")
                    if scenario.solar_params:
                        st.write(f"- **Capacity:** {scenario.solar_params['capacity_kwp']} kWp")
                        st.write(f"- **Yield:** {scenario.solar_params['yield_factor']} kWh/kWp")
                        st.write(f"- **Capex:** € {scenario.solar_params['capex_per_kwp']} / kWp")
                    else:
                        st.write("- No Solar PV configured.")
                        
                with col_info2:
                    st.markdown("**🔋 Battery Storage Details**")
                    if scenario.battery_params:
                        st.write(f"- **Capacity:** {scenario.battery_params['capacity_kwh']} kWh")
                        st.write(f"- **Power:** {scenario.battery_params['max_power_kw']} kW")
                        st.write(f"- **Efficiency:** {scenario.battery_params['efficiency_pct']} %")
                        st.write(f"- **Min SoC:** {scenario.battery_params['min_soc_pct']} %")
                        st.write(f"- **Capex:** € {scenario.battery_params['capex_per_kwh']} / kWh")
                    else:
                        st.write("- No Battery configured.")
                
                # Delete Button: Removes the specific scenario from memory and refreshes the UI
                if st.button(f"🗑️ Delete '{scenario.name}'", key=f"delete_{index}"):
                    st.session_state['sub_scenarios'].pop(index)
                    st.rerun()
        
        st.divider()

    # ---------------------------------------------------------
    # SECTION 2: CREATE OR EDIT FORM (Create & Update)
    # ---------------------------------------------------------
    st.subheader("Scenario Builder")
    
    # Determine the mode. If no scenarios exist, force "Create New". 
    # Otherwise, let the user choose.
    mode = "Create New"
    if st.session_state.get('sub_scenarios'):
        mode = st.radio("Action", ["Create New", "Edit Existing"], horizontal=True)
        
    target_scenario = None
    if mode == "Edit Existing":
        scenario_names = [s.name for s in st.session_state['sub_scenarios']]
        selected_edit_name = st.selectbox("Select scenario to edit", scenario_names)
        # Find the actual object in memory that matches the selected name
        target_scenario = next(s for s in st.session_state['sub_scenarios'] if s.name == selected_edit_name)

    # ---------------------------------------------------------
    # SETTING DEFAULT VALUES FOR THE FORM
    # ---------------------------------------------------------
    # If we are editing, we pre-fill the form with the target_scenario data. 
    # If creating new, we use empty/default values.
    
    # 1. Base Profile Default
    baseline_names = [b.name for b in st.session_state['baselines']]
    def_base_index = 0
    if target_scenario and target_scenario.parent_baseline.name in baseline_names:
        def_base_index = baseline_names.index(target_scenario.parent_baseline.name)
            
    def_name = target_scenario.name if target_scenario else ""
    
    # 2. Solar Defaults
    def_use_solar = target_scenario.solar_params is not None if target_scenario else False
    def_sol_kwp = target_scenario.solar_params["capacity_kwp"] if (target_scenario and target_scenario.solar_params) else 100.0
    def_sol_yield = target_scenario.solar_params["yield_factor"] if (target_scenario and target_scenario.solar_params) else 1000.0
    def_sol_capex = target_scenario.solar_params["capex_per_kwp"] if (target_scenario and target_scenario.solar_params) else 1000.0
    
    # 3. Battery Defaults
    def_use_batt = target_scenario.battery_params is not None if target_scenario else False
    def_bat_cap = target_scenario.battery_params["capacity_kwh"] if (target_scenario and target_scenario.battery_params) else 200.0
    def_bat_pwr = target_scenario.battery_params["max_power_kw"] if (target_scenario and target_scenario.battery_params) else 100.0
    def_bat_eff = target_scenario.battery_params["efficiency_pct"] if (target_scenario and target_scenario.battery_params) else 90.0
    def_bat_soc = target_scenario.battery_params["min_soc_pct"] if (target_scenario and target_scenario.battery_params) else 20.0
    def_bat_capex = target_scenario.battery_params["capex_per_kwh"] if (target_scenario and target_scenario.battery_params) else 350.0

    # ---------------------------------------------------------
    # RENDER THE INPUT FORM
    # ---------------------------------------------------------
    selected_base_name = st.selectbox("Select Baseline Scenario", baseline_names, index=def_base_index)
    selected_baseline = next(b for b in st.session_state['baselines'] if b.name == selected_base_name)
    
    sub_name = st.text_input("Sub-Scenario Name", value=def_name, placeholder="e.g., Solar + 200kWh Battery")
    
    st.markdown("#### Add Energy Modules")
    col1, col2 = st.columns(2)
    
    # SOLAR INPUTS
    with col1:
        use_solar = st.toggle("Add Solar PV", value=def_use_solar)
        if use_solar:
            with st.container(border=True):
                st.markdown("#### Technical Specifications")
                solar_kwp = st.number_input("Solar Capacity (kWp)", min_value=0.0, value=float(def_sol_kwp))
                solar_yield = st.number_input("Annual Yield (kWh/kWp)", min_value=0.0, value=float(def_sol_yield))
                
                st.markdown("#### Financials")
                solar_capex = st.number_input("Investment Cost (€/kWp)", min_value=0.0, value=float(def_sol_capex))
    
    # BATTERY INPUTS
    with col2:
        use_battery = st.toggle("Add Battery Storage", value=def_use_batt)
        if use_battery:
            with st.container(border=True):
                st.markdown("#### Technical Specifications")
                bat_cap = st.number_input("Battery Capacity (kWh)", min_value=0.0, value=float(def_bat_cap))
                bat_pwr = st.number_input("Max Charge/Discharge Power (kW)", min_value=0.0, value=float(def_bat_pwr))
                
                col_bat1, col_bat2 = st.columns(2)
                with col_bat1:
                    bat_efficiency = st.number_input("Round-Trip Efficiency (%)", min_value=50.0, max_value=100.0, value=float(def_bat_eff))
                with col_bat2:
                    bat_min_soc = st.number_input("Minimum SoC (%)", min_value=0.0, max_value=50.0, value=float(def_bat_soc))
                
                st.markdown("#### Financials")
                bat_capex = st.number_input("Investment Cost (€/kWh)", min_value=0.0, value=float(def_bat_capex))
    
    # ---------------------------------------------------------
    # SAVE OR UPDATE LOGIC
    # ---------------------------------------------------------
    st.divider()
    button_label = "Update Scenario" if mode == "Edit Existing" else "Save New Scenario"
    
    if st.button(button_label, type="primary"):
        if not sub_name:
            st.error("Please provide a name for this Sub-Scenario.")
            return
            
        # Prevent creating a new scenario with a name that already exists
        if mode == "Create New" and any(s.name == sub_name for s in st.session_state['sub_scenarios']):
            st.error(f"A scenario named '{sub_name}' already exists. Please choose a different name.")
            return

        # Build the new or updated scenario object
        new_sub = SubScenario(name=sub_name, parent_baseline=selected_baseline)
        
        if use_solar:
            new_sub.solar_params = {
                "capacity_kwp": solar_kwp, 
                "yield_factor": solar_yield,
                "capex_per_kwp": solar_capex
            }
        if use_battery:
            new_sub.battery_params = {
                "capacity_kwh": bat_cap, 
                "max_power_kw": bat_pwr,
                "efficiency_pct": bat_efficiency,
                "min_soc_pct": bat_min_soc,
                "capex_per_kwh": bat_capex
            }
        
        # Apply the changes to the central memory
        if mode == "Create New":
            st.session_state['sub_scenarios'].append(new_sub)
            st.success(f"Sub-Scenario '{sub_name}' successfully created!")
        else:
            # Find the old scenario's position in the list and overwrite it
            idx = st.session_state['sub_scenarios'].index(target_scenario)
            st.session_state['sub_scenarios'][idx] = new_sub
            st.success(f"Sub-Scenario '{sub_name}' successfully updated!")
        
        # Force a refresh so the overview at the top shows the new data immediately
        st.rerun()