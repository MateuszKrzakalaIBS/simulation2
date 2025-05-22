"""
Simplified interactive dashboard for demographic simulation.
This script creates a simple web interface using Streamlit
to run simulations and view summary statistics.
"""

import streamlit as st
import pandas as pd
# import numpy as np # No longer directly used in this simplified version
import os
import json
import sys

# Add the parent directory to sys.path to import simulation modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

# Helper function to resolve paths
def resolve_path(relative_path):
    """Resolve a path relative to the parent directory of the web app."""
    return os.path.join(parent_dir, relative_path)

# Import simulation modules
import simulation2
# import interactive_visualizations # No longer needed for this simplified version

def load_config():
    """Load configuration from JSON file."""
    try:
        # First try in parent directory, then in current directory
        # parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # Already defined globally
        config_path = os.path.join(parent_dir, "config.json")
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
            st.sidebar.success(f"Loaded configuration from {config_path}")
            return config
        elif os.path.exists("config.json"): # Fallback to current dir, though parent_dir should be preferred
            with open("config.json", 'r') as f:
                config = json.load(f)
            return config
        else:
            st.sidebar.warning("Configuration file not found. Using default settings.")
            # Simplified default config for clarity
            return {
                "simulation": {
                    "input_file": "Input.xlsx",
                    "output_file": "Output.xlsx",
                    "detailed_output_file": "DetailedOutput.xlsx",
                    "shock_scenario": {
                        "s1_change": -0.1,
                        "s2_change": 0.1,
                        "s3_change": 0.0
                    },
                    "variables_to_exclude": []
                }
            }
    except Exception as e:
        st.error(f"Error loading configuration: {str(e)}")
        return {} # Return empty dict on error

def run_simulation(config):
    """Run simulation with the current configuration."""
    try:
        with st.spinner("Running simulation..."):
            sim_config = config.get("simulation", {})
            
            if "input_file" in sim_config:
                sim_config["input_file"] = resolve_path(sim_config["input_file"])
            if "output_file" in sim_config:
                sim_config["output_file"] = resolve_path(sim_config["output_file"]) 
            if "detailed_output_file" in sim_config:
                sim_config["detailed_output_file"] = resolve_path(sim_config["detailed_output_file"])
            
            summary_df, detailed_df_dict = simulation2.run_simulation(config)
            st.success("Simulation completed successfully!")

            # Removed text report generation
            # if summary_df is not None:
            #     report_path = resolve_path("simulation_summary_report.txt")
            #     try:
            #         summary_df.to_csv(report_path, sep='\t', index=False)
            #         st.info(f"Summary report saved to: {report_path}")
            #     except Exception as e_report:
            #         st.error(f"Failed to save summary report: {str(e_report)}")
            
        return summary_df, detailed_df_dict
    except Exception as e:
        st.error(f"Error during simulation: {str(e)}")
        return None, None

def main():
    """Main Streamlit app."""
    st.set_page_config(
        page_title="Simplified Demographic Simulation",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    
    st.title("Simplified Demographic Counterfactual Simulation")
    # st.write(""" # Original brief write, replaced by detailed explanation below
    # This tool allows you to run demographic simulations and view summary statistics.
    # Configure your simulation parameters in the sidebar and run the analysis.
    # """)

    with st.expander("About this Simulation Tool", expanded=True):
        st.markdown("""
            ### Welcome to the Demographic Counterfactual Simulation Tool!

            This application allows you to explore the potential impacts of various demographic scenarios (or 'shocks') 
            on a range of population variables. It performs a counterfactual analysis, comparing a baseline scenario 
            (without the shock) to an alternative scenario (with the shock applied).

            **Core Logic:**
            1.  **Baseline Calculation**: The simulation first establishes a baseline for each variable based on the input data.
            2.  **Shock Application**: You can define a 'shock' through the parameters in the sidebar (s1, s2, s3 changes). These shocks modify underlying factors that influence the variables.
            3.  **Alternative Scenario Calculation**: The simulation recalculates the variables under this new shocked condition.
            4.  **Impact Assessment**: Finally, it compares the results from the baseline and alternative scenarios to quantify the impact of the shock, showing absolute and relative changes.
        """)

    with st.expander("Understanding the Input and Output Files"):
        st.markdown("""
            #### Input File (`Input.xlsx` by default)
            This Excel file is the primary source of data for the simulation. It typically contains:
            *   **Population Data**: Baseline demographic data, often broken down by age, sex, and other relevant categories.
            *   **Variable Parameters**: Coefficients, base rates, and other parameters that define how each variable is calculated and how it responds to demographic factors and shocks.
            *   **Scenario Definitions**: May contain predefined scenarios or parameters used by the simulation engine.
            *   **Sheet Structure**: The simulation expects specific sheet names and column headers. Refer to the simulation's documentation or `simulation2.py` for the exact structure required.

            #### Output File (`Output.xlsx` by default)
            This file stores the **summary results** of the simulation. For each variable analyzed, it typically includes:
            *   `variable`: The name of the variable.
            *   `result_bs`: The aggregated result for the variable in the baseline scenario.
            *   `result_as`: The aggregated result for the variable in the alternative (shocked) scenario.
            *   `absolute_change`: The difference between `result_as` and `result_bs`.
            *   `relative_change_pct`: The percentage change from baseline to alternative.
            *   Other aggregated metrics depending on the variable type (e.g., total employed, total affected population).

            #### Detailed Output File (`DetailedOutput.xlsx` by default)
            This file provides more granular results. It often contains:
            *   **A summary sheet**: Similar to `Output.xlsx`.
            *   **Individual Variable Sheets**: For each key variable, a separate sheet showing results disaggregated by demographic groups (e.g., age and sex). This allows for a deeper understanding of how the shock impacts different segments of the population.
            *   Columns in these sheets might include `age`, `sex`, `population`, `result_bs` (for that group), `result_as` (for that group), `difference`, `difference_pct`, and contribution metrics.
        """)

    config = load_config()
    
    with st.sidebar:
        st.header("Simulation Configuration")
        st.markdown("Use the controls below to configure the simulation run.")
        
        st.subheader("Files")
        st.markdown("Specify the Excel files for input and output. Ensure `Input.xlsx` is formatted correctly.")
        input_file = st.text_input("Input Excel File", 
                                  value=config.get("simulation", {}).get("input_file", "Input.xlsx"))
        output_file = st.text_input("Output Excel File", 
                                   value=config.get("simulation", {}).get("output_file", "Output.xlsx"))
        detailed_output_file = st.text_input("Detailed Output Excel File", 
                                           value=config.get("simulation", {}).get("detailed_output_file", "DetailedOutput.xlsx"))
        
        st.subheader("Counterfactual Scenario")
        # Ensure shock_scenario and its nested keys exist, providing defaults
        default_sim_config = {
            "input_file": "Input.xlsx",
            "output_file": "Output.xlsx",
            "detailed_output_file": "DetailedOutput.xlsx",
            "shock_scenario": {
                "scenario_type": "Percentage Change",
                "s1_change": -0.1,
                "s2_change": 0.1,
                "s3_change": 0.0,
                "s1_reallocation_percentage": 0.5
            },
            "variables_to_exclude": []
        }
        simulation_config = config.get("simulation", default_sim_config.copy())
        # Ensure shock_scenario itself exists and has all keys
        shock_scenario_config = simulation_config.get("shock_scenario", default_sim_config["shock_scenario"].copy())
        for key, value in default_sim_config["shock_scenario"].items():
            shock_scenario_config.setdefault(key, value)

        # Define internal keys that simulation2.py expects
        internal_scenario_keys = ["Percentage Change", "use_2012_values", "s1_reallocated_to_s2"]
        default_internal_key = "Percentage Change" # Must be one of internal_scenario_keys

        # Get scenario_type from loaded config (might be old format or new internal key)
        raw_scenario_type_from_config = shock_scenario_config.get("scenario_type", default_internal_key)

        # Normalize it to an internal key for determining initial selection
        normalized_initial_key = raw_scenario_type_from_config
        if raw_scenario_type_from_config == "Use 2012 Values": # Handle old display name from config
            normalized_initial_key = "use_2012_values"
        elif raw_scenario_type_from_config == "S1 Reallocated to S2": # Handle old display name from config
            normalized_initial_key = "s1_reallocated_to_s2"
        elif raw_scenario_type_from_config not in internal_scenario_keys: # If it's something unexpected
            normalized_initial_key = default_internal_key
        
        # Now, normalized_initial_key is guaranteed to be one of the internal_scenario_keys
        try:
            initial_selectbox_index = internal_scenario_keys.index(normalized_initial_key)
        except ValueError: 
            initial_selectbox_index = internal_scenario_keys.index(default_internal_key)

        # The st.selectbox will display and return the internal keys directly
        selected_scenario_key = st.selectbox(
            "Select Scenario Type",
            options=internal_scenario_keys, # Users see these internal keys
            index=initial_selectbox_index,
            help="Choose the type of counterfactual scenario to apply. 'use_2012_values' and 's1_reallocated_to_s2' are internal keys."
        )
        # selected_scenario_key is now the definitive internal key for this run

        # Update the working copy of shock_scenario_config with the selected (and correct internal) key
        shock_scenario_config["scenario_type"] = selected_scenario_key

        s1_change_val = float(shock_scenario_config.get("s1_change", -0.1))
        s2_change_val = float(shock_scenario_config.get("s2_change", 0.1))
        s3_change_val = float(shock_scenario_config.get("s3_change", 0.0))
        s1_reallocation_percentage_val = float(shock_scenario_config.get("s1_reallocation_percentage", 0.5))

        if selected_scenario_key == "Percentage Change":
            st.markdown("Define the direct changes to s1, s2, and s3 parameters.")
            s1_change_val = st.slider("s1 Change", -1.0, 1.0, s1_change_val, 0.05, help="Direct additive change to s1.")
            s2_change_val = st.slider("s2 Change", -1.0, 1.0, s2_change_val, 0.05, help="Direct additive change to s2.")
            s3_change_val = st.slider("s3 Change", -1.0, 1.0, s3_change_val, 0.05, help="Direct additive change to s3.")
        elif selected_scenario_key == "use_2012_values":
            st.markdown("The simulation will use s1, s2, and s3 values from the `data_2012` sheet in `Input.xlsx` for each corresponding demographic group.")
            # Sliders for s1,s2,s3_change are ignored for this scenario.
        elif selected_scenario_key == "s1_reallocated_to_s2":
            st.markdown("A percentage of s1 will be subtracted from s1 and added to s2. s3 remains unchanged from baseline.")
            s1_reallocation_percentage_val = st.slider(
                "S1 Reallocation to S2 (%)", 
                min_value=0.0, 
                max_value=1.0, 
                value=s1_reallocation_percentage_val, 
                step=0.01, 
                format="%.2f",
                help="The proportion of s1 to reallocate to s2 (e.g., 0.5 means 50% of s1 is moved to s2)."
            )
            # s1_change and s2_change sliders are ignored. s3_change could optionally still apply if desired.
            # For now, let's assume s3_change is also ignored for simplicity of this scenario.
            # If s3_change should still apply, uncomment the next line:
            # s3_change_val = st.slider("s3 Change (Optional)", -1.0, 1.0, s3_change_val, 0.05, help="Optional direct additive change to s3.")

        # Update the main config dictionary that will be passed to the simulation
        if "simulation" not in config:
            config["simulation"] = default_sim_config.copy()
        else: # Ensure sub-dictionaries exist if simulation key exists
            config["simulation"].setdefault("shock_scenario", default_sim_config["shock_scenario"].copy())
            config["simulation"].setdefault("variables_to_exclude", default_sim_config["variables_to_exclude"][:])

        config["simulation"]["input_file"] = input_file
        config["simulation"]["output_file"] = output_file
        config["simulation"]["detailed_output_file"] = detailed_output_file
        
        # Update shock_scenario part of the config
        config["simulation"]["shock_scenario"]["scenario_type"] = selected_scenario_key # Use the corrected internal key
        config["simulation"]["shock_scenario"]["s1_change"] = s1_change_val
        config["simulation"]["shock_scenario"]["s2_change"] = s2_change_val
        config["simulation"]["shock_scenario"]["s3_change"] = s3_change_val
        config["simulation"]["shock_scenario"]["s1_reallocation_percentage"] = s1_reallocation_percentage_val
        
        st.subheader("Variable Exclusions")
        var_exclude_text = st.text_area("Variables to Exclude (comma-separated)", 
                                      value=",".join(config.get("simulation", {}).get("variables_to_exclude", [])))
        var_excludes = [v.strip() for v in var_exclude_text.split(",") if v.strip()]
        config["simulation"]["variables_to_exclude"] = var_excludes

        # Removed visualization settings from sidebar as they are not used in this simplified version

    # Main content area
    st.header("Run Simulation and View Summary")
    st.markdown("Click the button below to run the simulation with the current settings from the sidebar. The summary results will be displayed in a table.")
    
    st.subheader("Current Shock Scenario")
    # Display current scenario type (now an internal key)
    default_internal_key_display = "Percentage Change" # Consistent default for display
    current_scenario_key_for_display = config.get("simulation", {}).get("shock_scenario", {}).get("scenario_type", default_internal_key_display)
    st.metric("Scenario Type", current_scenario_key_for_display)
    
    current_scenario_type = current_scenario_key_for_display # Use this for logic below
    s1_disp, s2_disp, s3_disp = "N/A", "N/A", "N/A"

    if current_scenario_type == "Percentage Change":
        s1_val = config.get("simulation", {}).get("shock_scenario", {}).get("s1_change", 0)
        s2_val = config.get("simulation", {}).get("shock_scenario", {}).get("s2_change", 0)
        s3_val = config.get("simulation", {}).get("shock_scenario", {}).get("s3_change", 0)
        s1_disp = f"{s1_val:+.2f} (change)"
        s2_disp = f"{s2_val:+.2f} (change)"
        s3_disp = f"{s3_val:+.2f} (change)"
    elif current_scenario_type == "use_2012_values": # Compare with internal key
        s1_disp = "From data_2012"
        s2_disp = "From data_2012"
        s3_disp = "From data_2012"
    elif current_scenario_type == "s1_reallocated_to_s2": # Compare with internal key
        realloc_perc = config.get("simulation", {}).get("shock_scenario", {}).get("s1_reallocation_percentage", 0)
        s1_disp = f"{realloc_perc*100:.0f}% of s1 to s2"
        s2_disp = "s2 + reallocated s1"
        s3_disp = "Baseline s3"

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("s1 Effect", s1_disp)
    with col2:
        st.metric("s2 Effect", s2_disp)
    with col3:
        st.metric("s3 Effect", s3_disp)
    
    if st.button("Run Simulation"):
        # Pass the updated config from the sidebar
        summary_df, _ = run_simulation(config) # We only need summary_df for display here
        
        if summary_df is not None:
            st.subheader("Simulation Summary Statistics")
            st.markdown("The table below shows the aggregated impact of the simulated shock on each variable. See the 'Understanding the Input and Output Files' section for more details on these metrics.")
            st.dataframe(summary_df, use_container_width=True)
            # The message about report saving is now in run_simulation
        else:
            st.info("Simulation ran, but no summary data was returned or an error occurred.")

    st.markdown("---") # Visual separator
    st.header("About the Simulation and Files")

    with st.expander("Simulation Logic and Process"):
        st.markdown("""
        **Purpose:**
        This simulation tool is designed to model and analyze the impact of hypothetical demographic shocks on various socio-economic outcome variables. It allows users to define a "shock scenario" by altering key parameters (s1, s2, s3) and observe the resulting changes.

        **Core Logic:**
        1.  **Baseline Data:** The simulation starts by loading baseline data and parameters from the `Input.xlsx` file. This file establishes the initial state of the demographic and economic environment.
        2.  **Shock Application:** Users define a shock scenario through the sidebar by specifying percentage changes to three core parameters: `s1_change`, `s2_change`, and `s3_change`. These parameters are abstract and their specific meaning (e.g., change in fertility rates, migration, labor force participation) depends on the underlying model structure defined in `simulation2.py`.
        3.  **Recalculation:** The simulation engine (`simulation2.py`) takes these shock parameters and recalculates all dependent outcome variables. The exact formulas and relationships are embedded within the `simulation2.py` script.
        4.  **Comparison:** The core of the analysis involves comparing the outcome variables from the "after shock" scenario to the "baseline" scenario.
        5.  **Output Generation:** The simulation produces:
            *   A summary of key changes, displayed directly in this web application.
            *   An `Output.xlsx` file containing these summary statistics.
            *   A `DetailedOutput.xlsx` file providing more granular, disaggregated results for in-depth analysis.

        **Generation Process:**
        *   The simulation is executed by the `simulation2.run_simulation()` function, which is part of the `simulation2.py` script located in the parent directory of this web application.
        *   This function processes the configurations set in the sidebar (file paths, shock values, variable exclusions) to perform its calculations.
        """)

    with st.expander("Input File: Input.xlsx"):
        st.markdown("""
        **Purpose:**
        The `Input.xlsx` file is the primary source of data for the simulation. It contains all the baseline figures, parameters, and coefficients required to define the initial state of the model before any shocks are applied.

        **Structure:**
        *   It is an Excel workbook, typically containing multiple sheets.
        *   Each sheet usually represents a different category of data, such as:
            *   Demographic cohorts and their characteristics.
            *   Baseline values for various outcome variables (e.g., health indicators, economic metrics).
            *   Model parameters and coefficients that might be affected by the s1, s2, s3 shocks.
            *   Lookup tables or assumptions used in the simulation's calculations.

        **Content Example (Illustrative):**
        *   A sheet named 'Demographics' might have age groups, population counts, and baseline fertility/mortality rates.
        *   A sheet named 'LaborMarket' could contain employment rates, wages, and participation rates by demographic group.
        *   A sheet named 'HealthIndicators' might list prevalence rates for certain conditions.
        *   A sheet named 'Parameters' could define how s1, s2, and s3 relate to specific model inputs.

        **Usage:**
        The `simulation2.py` script reads this file at the beginning of each simulation run to establish the "before shock" scenario. The accuracy and completeness of this file are crucial for meaningful simulation results. The default path is relative to the main simulation directory.
        """)

    with st.expander("Output File: Output.xlsx"):
        st.markdown("""
        **Purpose:**
        The `Output.xlsx` file stores the main summary results of the simulation run. It provides a high-level overview of the impacts of the applied shock scenario.

        **Structure:**
        *   An Excel workbook.
        *   Typically contains one or more sheets presenting aggregated results.
        *   The primary content is often a table similar to the "Simulation Summary Statistics" displayed in this web app.

        **Content Example:**
        *   A sheet named 'SummaryResults' might show:
            *   Baseline values for key indicators.
            *   Values for these indicators after the shock.
            *   Absolute and percentage changes.
            *   Aggregated impacts across different demographic groups or regions.

        **Generation:**
        This file is generated by `simulation2.py` at the end of a successful simulation. It reflects the `summary_df` (summary DataFrame) returned by the simulation logic. The default path is relative to the main simulation directory.
        """)

    with st.expander("Detailed Output File: DetailedOutput.xlsx"):
        st.markdown("""
        **Purpose:**
        The `DetailedOutput.xlsx` file provides more granular and disaggregated results from the simulation. It is intended for users who need to perform a deeper dive into the specific changes across various dimensions.

        **Structure:**
        *   An Excel workbook, often containing multiple sheets.
        *   Each sheet might correspond to a specific outcome variable, demographic segment, or intermediate calculation step.

        **Content Example:**
        *   If the simulation models multiple health conditions, there might be separate sheets for each condition showing changes by age, gender, etc.
        *   Sheets could contain time-series data if the model projects outcomes over several periods (though the current app focuses on a single shock event).
        *   Breakdowns of how the s1, s2, s3 shocks propagated through different parts of the model.

        **Generation:**
        This file is also generated by `simulation2.py`. It corresponds to the `detailed_df_dict` (dictionary of detailed DataFrames) returned by the simulation logic, where dictionary keys often become sheet names. The default path is relative to the main simulation directory.
        """)

    with st.expander("Using the Sidebar Configuration"):
        st.markdown("""
        The sidebar on the left allows you to customize the simulation:

        *   **Files:**
            *   `Input Excel File`: Specify the name of your input data file (e.g., `Input.xlsx`). The application expects this file to be in the main simulation directory.
            *   `Output Excel File`: Define the name for the summary output Excel file (e.g., `Output.xlsx`).
            *   `Detailed Output Excel File`: Define the name for the detailed output Excel file (e.g., `DetailedOutput.xlsx`).
        *   **Shock Scenario:**
            *   Adjust the sliders for `s1 Change`, `s2 Change`, and `s3 Change`. These represent percentage point changes (e.g., a value of 0.1 means a +10% change, -0.05 means a -5% change) to the respective underlying parameters in the simulation model.
        *   **Variable Exclusions:**
            *   `Variables to Exclude`: Enter a comma-separated list of variable names that you want the simulation to ignore or not process. This can be useful for sensitivity analysis or focusing on specific parts of the model.

        Click the "Run Simulation" button after setting your desired configurations. The results (summary statistics) will be displayed on this page, and the configured Excel files will be generated/updated in the main simulation directory.
        """)

if __name__ == "__main__":
    main()
