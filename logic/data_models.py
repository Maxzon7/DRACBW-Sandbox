from dataclasses import dataclass
import pandas as pd
from typing import Optional, Dict

@dataclass
class Baseline:
    """
    Represents the original status quo of a client's energy profile before any hardware additions.
    Serves as the foundation for future sub-scenarios.
    """
    name: str
    raw_data: pd.DataFrame
    grid_limit_kw: float

@dataclass
class SubScenario:
    """
    Represents a modified scenario containing solar or battery hardware configurations.
    It is always linked to a specific Baseline profile.
    """
    name: str
    parent_baseline: Baseline
    solar_params: Optional[Dict] = None
    battery_params: Optional[Dict] = None
    #wind data is missing because there`s currently no module to support it`