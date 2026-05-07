import streamlit as st
import pandas as pd

# Import the UI modules for each tab
from tabs.tab1_baseline import render_tab1
from tabs.tab2_scenarios import render_tab2
from tabs.tab3_comparison import render_tab3

# -----------------------------------------------------------------------------
# DATA MODELS
# -----------------------------------------------------------------------------
class BaselineScenario:
    """
    Represents the foundational scenario containing raw data and grid constraints.
    """
    def __init__(self, name: str, raw_data: pd.DataFrame, grid_limit_kw: float):
        self.name = name
        self.raw_data = raw_data
        self.grid_limit_kw = grid_limit_kw

class SubScenario:
    """
    Represents a variation built upon a BaselineScenario.
    Stores only the delta parameters (Solar, Battery, Wind, Generator).
    """
    def __init__(self, name: str, parent_baseline: BaselineScenario):
        self.name = name
        self.parent_baseline = parent_baseline
        
        self.solar_params = None
        self.battery_params = None
        self.wind_params = None
        self.generator_params = None

# -----------------------------------------------------------------------------
# APP INITIALIZATION
# -----------------------------------------------------------------------------
def main():
    st.set_page_config(page_title="DRACBV Energy Simulator V2", layout="wide")
    st.title("DRACBV Energy Solution Simulator")

    # Initialize Global Memory
    if 'baselines' not in st.session_state:
        st.session_state['baselines'] = [] 

    if 'sub_scenarios' not in st.session_state:
        st.session_state['sub_scenarios'] = [] 

    # Create UI Tabs
    tab1, tab2, tab3 = st.tabs(["1. Create Baseline", "2. Build Sub-Scenarios", "3. Comparison"])

    # Route logic to individual modules
    with tab1:
        render_tab1()
        
    with tab2:
        render_tab2()
        
    with tab3:
        render_tab3()

if __name__ == "__main__":
    main()