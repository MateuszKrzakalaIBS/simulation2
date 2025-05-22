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
    # Removed commented out st.write

    with st.expander("About this Simulation Tool", expanded=True):
        st.markdown("""
            ### Welcome to the Demographic Counterfactual Simulation Tool!

            This application runs demographic counterfactual analyses. It compares a baseline scenario 
            to an alternative scenario where a defined 'shock' is applied, allowing you to assess the impact on various population variables.
        """)

    with st.expander("Understanding the Input and Output Files"):
        st.markdown("""
            #### Input File (`Input.xlsx` by default)
            The primary source of data, containing baseline population data, variable parameters, and scenario definitions. The simulation expects specific sheet names and column structures.
            *   **Key Content**: Demographic data (age, sex), parameters for variable calculation.
            *   **`data_2012` sheet**: Used for the "Use 2012 Values" scenario.
            *   **`parameters` sheet**: Can define `friendly_name` and `variable_type` for dynamic loading in the simulation.

            #### Output File (`Output.xlsx` by default)
            Stores summary results, showing aggregated impacts for each variable (baseline vs. alternative, absolute/relative changes).
            *   **Key Content**: `variable`, `result_bs`, `result_as`, `absolute_change`, `relative_change_pct`.

            #### Detailed Output File (`DetailedOutput.xlsx` by default)
            Provides granular results, often with separate sheets for variables, disaggregated by demographic groups (e.g., age, sex).
            *   **Key Content**: Disaggregated `result_bs`, `result_as`, `difference` by demographic groups.
        """)

    config = load_config()
    
    with st.sidebar:
        st.header("Simulation Configuration")
        st.markdown("Use the controls below to configure the simulation run.")
        
        st.subheader("Files")
        st.markdown("Specify the Excel files for input and output. Ensure `Input.xlsx` is formatted correctly.")
        
        # --- START NEW INPUT FILE HANDLING ---
        # Get the initial input file path from config (could be absolute or basename)
        config_input_file_path = config.get("simulation", {}).get("input_file", "Input.xlsx")
        
        uploaded_file = st.file_uploader(
            "Upload Custom Input.xlsx (Optional)",
            type=["xlsx"],
            help="If you upload a file, it will be used instead of the one specified in the text field below. The uploaded file will be named 'uploaded_input.xlsx' in the simulation's root directory."
        )

        # This variable will hold the path/name that config should use for the input file.
        # It's an absolute path for successful uploads, otherwise a basename from text_input/config.
        input_file_for_config = config_input_file_path 
        # This is what the text_input box will display.
        display_filename_in_text_box = os.path.basename(config_input_file_path)
        # Controls if the text_input box is editable.
        input_text_field_is_disabled = False

        if uploaded_file is not None:
            # parent_dir is defined globally: os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            temp_uploaded_file_path = os.path.join(parent_dir, "uploaded_input.xlsx")
            try:
                with open(temp_uploaded_file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                input_file_for_config = temp_uploaded_file_path # Use absolute path for the simulation
                display_filename_in_text_box = "uploaded_input.xlsx (using uploaded file)"
                input_text_field_is_disabled = True # Disable text field as upload takes precedence
                st.sidebar.success(f"Using uploaded file: {os.path.basename(temp_uploaded_file_path)}")
            except Exception as e:
                st.sidebar.error(f"Error saving uploaded file: {e}. Using file from text input or config.")
                # Fallback: input_file_for_config remains as config_input_file_path (original or default)
                # display_filename_in_text_box remains os.path.basename(config_input_file_path)
                # input_text_field_is_disabled remains False
        
        # Text input for input file:
        # - If upload succeeded, it's disabled and shows "uploaded_input.xlsx (...)" 
        # - If no upload or upload failed, it's enabled and shows the current config/default filename, and is editable.
        input_file_from_text_field = st.text_input(
            "Input Excel File",
            value=display_filename_in_text_box,
            help="Name of the Input Excel file. If not an uploaded file, it's relative to the simulation's root directory.",
            disabled=input_text_field_is_disabled
        )

        # Determine the final input_file value for the config dictionary:
        if uploaded_file is not None and input_file_for_config.endswith("uploaded_input.xlsx"):
            # If upload was successful and processed, config uses the absolute path to the uploaded file.
            config["simulation"]["input_file"] = input_file_for_config
        else:
            # No upload, or upload failed: use the value from the (potentially user-edited) text field.
            # This value is expected to be a basename or a relative path that resolve_path can handle.
            config["simulation"]["input_file"] = input_file_from_text_field
        # --- END NEW INPUT FILE HANDLING ---

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

        # config["simulation"]["input_file"] = input_file # This line is removed/obsolete; handled by the new logic above.
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

        # Section for downloading and previewing output files
        st.markdown("---")
        st.header("Download and Preview Output Files")

        output_file_config_key = "output_file"
        detailed_output_config_key = "detailed_output_file"

        # Get base filenames for display, handle potential None or empty strings
        raw_output_filename = config.get("simulation", {}).get(output_file_config_key, "Output.xlsx")
        output_filename = os.path.basename(raw_output_filename) if raw_output_filename else "Output.xlsx"
        
        raw_detailed_output_filename = config.get("simulation", {}).get(detailed_output_config_key, "DetailedOutput.xlsx")
        detailed_output_filename = os.path.basename(raw_detailed_output_filename) if raw_detailed_output_filename else "DetailedOutput.xlsx"

        output_file_path = resolve_path(raw_output_filename)
        detailed_output_file_path = resolve_path(raw_detailed_output_filename)
        
        output_exists = os.path.exists(output_file_path)
        detailed_output_exists = os.path.exists(detailed_output_file_path)

        tabs_to_create = []
        if output_exists:
            tabs_to_create.append(f"Output File (`{output_filename}`)")
        if detailed_output_exists:
            tabs_to_create.append(f"Detailed Output File (`{detailed_output_filename}`)")

        if not tabs_to_create:
            st.info("Run the simulation to generate output files. If files were generated, ensure paths in the sidebar are correct.")
        else:
            tabs = st.tabs(tabs_to_create)
            tab_idx = 0

            if output_exists:
                with tabs[tab_idx]:
                    st.subheader(f"Manage: `{output_filename}`")
                    try:
                        with open(output_file_path, "rb") as fp:
                            st.download_button(
                                label=f"Download `{output_filename}`",
                                data=fp,
                                file_name=output_filename,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                        
                        st.markdown("#### Preview Content (first 5 rows of selected sheet)")
                        xls_output = pd.ExcelFile(output_file_path)
                        sheet_names_output = xls_output.sheet_names
                        if sheet_names_output:
                            selected_sheet_output = st.selectbox(
                                "Select a sheet to preview", 
                                sheet_names_output, 
                                key="output_sheet_select" # Unique key
                            )
                            if selected_sheet_output:
                                df_preview_output = xls_output.parse(selected_sheet_output)
                                st.dataframe(df_preview_output.head(), use_container_width=True)
                        else:
                            st.warning(f"`{output_filename}` contains no sheets or is not a valid Excel file.")
                    except Exception as e:
                        st.error(f"Error processing `{output_filename}`: {e}")
                tab_idx += 1

            if detailed_output_exists:
                with tabs[tab_idx]:
                    st.subheader(f"Manage: `{detailed_output_filename}`")
                    try:
                        with open(detailed_output_file_path, "rb") as fp:
                            st.download_button(
                                label=f"Download `{detailed_output_filename}`",
                                data=fp,
                                file_name=detailed_output_filename,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                        
                        st.markdown("#### Preview Content (first 5 rows of selected sheet)")
                        xls_detailed = pd.ExcelFile(detailed_output_file_path)
                        sheet_names_detailed = xls_detailed.sheet_names
                        if sheet_names_detailed:
                            selected_sheet_detailed = st.selectbox(
                                "Select a sheet to preview", 
                                sheet_names_detailed, 
                                key="detailed_sheet_select" # Unique key
                            )
                            if selected_sheet_detailed:
                                df_preview_detailed = xls_detailed.parse(selected_sheet_detailed)
                                st.dataframe(df_preview_detailed.head(), use_container_width=True)
                        else:
                            st.warning(f"`{detailed_output_filename}` contains no sheets or is not a valid Excel file.")
                    except Exception as e:
                        st.error(f"Error processing `{detailed_output_filename}`: {e}")
                # tab_idx += 1 # Not needed for the last possible tab

if __name__ == "__main__":
    main()
