"""
Streamlit-based web interface for demographic simulation.
This module provides a user-friendly interface to run and visualize simulations.
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import json
import sys
import time
import subprocess
import io
from PIL import Image

# Add the parent directory to sys.path to import simulation modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

# Helper function to resolve paths
def resolve_path(relative_path):
    """Resolve a path relative to the parent directory of the web app."""
    return os.path.join(parent_dir, relative_path)

# Import simulation modules
import simulation2
import visualize_results
import time_series_projection
import multivariate_analysis


def load_config():
    """Load configuration from JSON file."""
    try:
        # First try in current directory, then in parent directory
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(parent_dir, "config.json")
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
            st.sidebar.success(f"Loaded configuration from {config_path}")
            return config
        elif os.path.exists("config.json"):
            with open("config.json", 'r') as f:
                config = json.load(f)
            return config
        else:
            st.sidebar.warning("Configuration file not found. Using default settings.")
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
                },
                "visualization": {
                    "output_folder": "plots",
                    "create_summary_plots": True,
                    "create_detailed_plots": True,
                    "plot_format": "png",
                    "color_scheme": "RdBu_r"
                }
            }
    except Exception as e:
        st.error(f"Error loading configuration: {str(e)}")
        return {}


def save_config(config):
    """Save configuration to JSON file."""
    try:
        with open("config.json", 'w') as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        st.error(f"Error saving configuration: {str(e)}")
        return False


def run_simulation(config):
    """Run simulation with the current configuration."""
    try:
        with st.spinner("Running simulation..."):
            # First make sure all paths are resolved correctly
            sim_config = config.get("simulation", {})
            
            # Resolve input/output file paths
            if "input_file" in sim_config:
                sim_config["input_file"] = resolve_path(sim_config["input_file"])
            if "output_file" in sim_config:
                sim_config["output_file"] = resolve_path(sim_config["output_file"]) 
            if "detailed_output_file" in sim_config:
                sim_config["detailed_output_file"] = resolve_path(sim_config["detailed_output_file"])
            
            summary_df, detailed_df = simulation2.run_simulation(config)
            st.success("Simulation completed successfully!")
        return summary_df, detailed_df
    except Exception as e:
        st.error(f"Error during simulation: {str(e)}")
        return None, None


def run_visualization(config):
    """Run visualization with the current configuration."""
    try:
        with st.spinner("Creating visualizations..."):
            output_folder = config.get("visualization", {}).get("output_folder", "plots")
            output_folder = resolve_path(output_folder)
            
            input_file = config.get("simulation", {}).get("input_file", "Input.xlsx")
            output_file = config.get("simulation", {}).get("output_file", "Output.xlsx")
            detailed_output_file = config.get("simulation", {}).get("detailed_output_file", "DetailedOutput.xlsx")
            
            # Resolve paths
            output_file_path = resolve_path(output_file)
            detailed_output_file_path = resolve_path(detailed_output_file)
            
            summary_df = pd.read_excel(output_file_path)
            detailed_df = pd.read_excel(detailed_output_file_path, sheet_name='Summary')
            
            # Run basic visualizations
            visualize_results.visualize_summary(summary_df, config)
            
            # For each variable, create detailed visualizations
            for _, row in summary_df.iterrows():
                var = row['variable']
                try:
                    # Read the variable-specific sheet from the detailed output
                    var_df = pd.read_excel(config.get("simulation", {}).get("detailed_output_file", "DetailedOutput.xlsx"), 
                                          sheet_name=var[:30])  # Sheet names limited to 30 chars
                    visualize_results.visualize_detailed(var_df, var, output_folder)
                except Exception as var_e:
                    st.warning(f"Could not create detailed visualization for {var}: {str(var_e)}")
            
            st.success("Visualizations created successfully!")
    except Exception as e:
        st.error(f"Error during visualization: {str(e)}")


def show_image(image_path):
    """Display an image with error handling."""
    try:
        img = Image.open(image_path)
        st.image(img, use_column_width=True)
    except Exception as e:
        st.error(f"Could not load image {image_path}: {str(e)}")


def main():
    """Main Streamlit app."""
    st.set_page_config(
        page_title="Demographic Simulation Tool",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    
    st.title("Demographic Counterfactual Simulation Tool")
    st.write("""
    This tool allows you to run demographic simulations and visualize their results.
    Configure your simulation parameters in the sidebar and run the analysis.
    """)
    
    # Load configuration
    config = load_config()
    
    # Sidebar - Configuration
    with st.sidebar:
        st.header("Simulation Configuration")
        
        # Input/Output files
        st.subheader("Files")
        input_file = st.text_input("Input Excel File", 
                                  value=config.get("simulation", {}).get("input_file", "Input.xlsx"))
        output_file = st.text_input("Output Excel File", 
                                   value=config.get("simulation", {}).get("output_file", "Output.xlsx"))
        detailed_output_file = st.text_input("Detailed Output Excel File", 
                                           value=config.get("simulation", {}).get("detailed_output_file", "DetailedOutput.xlsx"))
        
        # Shock parameters
        st.subheader("Shock Scenario")
        shock_scenario = config.get("simulation", {}).get("shock_scenario", {"s1_change": -0.1, "s2_change": 0.1, "s3_change": 0.0})
        s1_change = st.slider("s1 Change", -1.0, 1.0, float(shock_scenario.get("s1_change", -0.1)), 0.05)
        s2_change = st.slider("s2 Change", -1.0, 1.0, float(shock_scenario.get("s2_change", 0.1)), 0.05)
        s3_change = st.slider("s3 Change", -1.0, 1.0, float(shock_scenario.get("s3_change", 0.0)), 0.05)
        
        # Update config
        if "simulation" not in config:
            config["simulation"] = {}
        
        config["simulation"]["input_file"] = input_file
        config["simulation"]["output_file"] = output_file
        config["simulation"]["detailed_output_file"] = detailed_output_file
        config["simulation"]["shock_scenario"] = {
            "s1_change": s1_change,
            "s2_change": s2_change,
            "s3_change": s3_change
        }
        
        # Variable exclusions
        st.subheader("Variable Exclusions")
        var_exclude_text = st.text_area("Variables to Exclude (comma-separated)", 
                                      value=",".join(config.get("simulation", {}).get("variables_to_exclude", [])))
        
        # Visualization settings
        st.subheader("Visualization Settings")
        output_folder = st.text_input("Output Folder", 
                                     value=config.get("visualization", {}).get("output_folder", "plots"))
        color_scheme = st.selectbox("Color Scheme", 
                                  options=["RdBu_r", "viridis", "coolwarm", "plasma", "magma", "cividis"],
                                  index=0)
        
        # Update visualization config
        if "visualization" not in config:
            config["visualization"] = {}
        
        config["visualization"]["output_folder"] = output_folder
        config["visualization"]["color_scheme"] = color_scheme
        
        # Process variable exclusions
        var_excludes = [v.strip() for v in var_exclude_text.split(",") if v.strip()]
        config["simulation"]["variables_to_exclude"] = var_excludes
        
        # Save config
        if st.button("Save Configuration"):
            if save_config(config):
                st.success("Configuration saved to config.json")
    
    # Main content
    tab1, tab2, tab3, tab4 = st.tabs(["Simulation", "Results", "Visualizations", "Advanced Analysis"])
    
    # Tab 1: Simulation
    with tab1:
        st.header("Run Simulation")
        st.write("""
        This will run the demographic simulation with the current configuration.
        The simulation applies demographic factors and shock scenarios to analyze their impact on variables.
        """)
        
        # Show current shock scenario
        st.subheader("Current Shock Scenario")
        st.write(f"s1 Change: {s1_change:+.2f}")
        st.write(f"s2 Change: {s2_change:+.2f}")
        st.write(f"s3 Change: {s3_change:+.2f}")
        
        # Button to run simulation
        if st.button("Run Simulation"):
            summary_df, detailed_df = run_simulation(config)
            
            if summary_df is not None:
                st.subheader("Simulation Results Summary")
                st.dataframe(summary_df)
                
                # Visualization button
                if st.button("Create Visualizations"):
                    run_visualization(config)
      # Tab 2: Results
    with tab2:
        st.header("View Results")
        
        # Try to load results
        try:
            output_file = resolve_path(config.get("simulation", {}).get("output_file", "Output.xlsx"))
            detailed_output_file = resolve_path(config.get("simulation", {}).get("detailed_output_file", "DetailedOutput.xlsx"))
            
            summary_df = pd.read_excel(output_file)
            st.subheader("Summary Results")
            st.dataframe(summary_df)
            
            # Show detailed results
            st.subheader("Detailed Results")
            sheet_names = pd.ExcelFile(detailed_output_file).sheet_names
            selected_sheet = st.selectbox("Select Variable Sheet", options=sheet_names)
            
            if selected_sheet:
                detailed_df = pd.read_excel(detailed_output_file, sheet_name=selected_sheet)
                st.dataframe(detailed_df)
        except Exception as e:
            st.info(f"No results found. Please run a simulation first. Error: {str(e)}")
    
    # Tab 3: Visualizations
    with tab3:
        st.header("Visualization Gallery")
        
        # Try to load visualizations
        output_folder = config.get("visualization", {}).get("output_folder", "plots")
        full_output_folder = resolve_path(output_folder)
        
        if os.path.exists(full_output_folder):
            # Get all PNG files in the output folder
            image_files = [f for f in os.listdir(full_output_folder) if f.endswith(".png")]
            
            if image_files:
                # Categorize images
                summary_images = [f for f in image_files if not "_" in f or "_change" in f]
                detailed_images = [f for f in image_files if "_" in f and not f in summary_images]
                
                # Display summary visualizations
                st.subheader("Summary Visualizations")
                for img_file in summary_images:
                    st.write(f"**{img_file.replace('.png', '').replace('_', ' ').title()}**")
                    show_image(os.path.join(full_output_folder, img_file))
                    st.markdown("---")
                
                # Display detailed visualizations with selection
                if detailed_images:
                    st.subheader("Detailed Visualizations")
                    
                    # Group images by variable
                    var_groups = {}
                    for img_file in detailed_images:
                        var_name = img_file.split("_")[0]
                        if var_name not in var_groups:
                            var_groups[var_name] = []
                        var_groups[var_name].append(img_file)
                      # Select variable
                    selected_var = st.selectbox("Select Variable", options=list(var_groups.keys()))
                    if selected_var:
                        for img_file in var_groups[selected_var]:
                            st.write(f"**{img_file.replace('.png', '').replace('_', ' ').title()}**")
                            show_image(os.path.join(full_output_folder, img_file))
                            st.markdown("---")
            else:
                st.info("No visualizations found. Please run visualizations first.")
        else:
            st.info(f"Visualization folder not found at {full_output_folder}. Please run visualizations first.")
    
    # Tab 4: Advanced Analysis
    with tab4:
        st.header("Advanced Analysis")
        
        # Sub-tabs for different advanced analyses
        adv_tab1, adv_tab2 = st.tabs(["Time Series Projections", "Multivariate Analysis"])
        
        # Time Series Projections
        with adv_tab1:
            st.subheader("Time Series Projections")
            st.write("""
            Project simulation results into the future and visualize trends.
            """)
              # Time series parameters
            years_ahead = st.slider("Years to Project", 5, 50, 30, 5)
            highlight_years = st.multiselect("Highlight Years", options=list(range(0, years_ahead + 1, 5)))
            
            # Run time series projection
            if st.button("Generate Time Series Projections"):
                try:
                    with st.spinner("Generating time series projections..."):
                        # Ensure output folder is properly resolved
                        output_folder = config.get("visualization", {}).get("output_folder", "plots")
                        base_output_folder = resolve_path(output_folder)
                        proj_folder = os.path.join(base_output_folder, "projections")
                        os.makedirs(proj_folder, exist_ok=True)
                        
                        time_series_projection.run_time_series_analysis(
                            summary_file=resolve_path(config.get("simulation", {}).get("output_file", "Output.xlsx")),
                            output_folder=proj_folder,
                            years_ahead=years_ahead,
                            highlight_years=highlight_years
                        )
                        
                        st.success("Time series projections generated successfully!")
                        
                        # Show projections
                        if os.path.exists(proj_folder):
                            image_files = [f for f in os.listdir(proj_folder) if f.endswith(".png")]
                            
                            if image_files:
                                for img_file in image_files:
                                    st.write(f"**{img_file.replace('.png', '').replace('_', ' ').title()}**")
                                    show_image(os.path.join(proj_folder, img_file))
                                    st.markdown("---")
                except Exception as e:
                    st.error(f"Error generating time series projections: {str(e)}")
        
        # Multivariate Analysis
        with adv_tab2:
            st.subheader("Multivariate Analysis")
            st.write("""
            Analyze relationships between variables using correlation and principal component analysis.
            """)
            
            # Multivariate parameters
            st.write("**Demographic Filters**")
            include_all = st.checkbox("Include All Demographics", value=True)
            include_men = st.checkbox("Include Men Only", value=False)
            include_women = st.checkbox("Include Women Only", value=False)
            
            # Selected age groups
            age_groups = ["0-4", "5-9", "10-14", "15-19", "20-24", "25-29", "30-34", 
                         "35-39", "40-44", "45-49", "50-54", "55-59", "60-64", 
                         "65-69", "70-74", "75-79", "80-84", "85+"]
            selected_age_groups = st.multiselect("Include Specific Age Groups", options=age_groups)
              # Run multivariate analysis
            if st.button("Generate Multivariate Analysis"):
                try:
                    with st.spinner("Generating multivariate analysis..."):
                        # Ensure output folder is properly resolved
                        output_folder = config.get("visualization", {}).get("output_folder", "plots")
                        base_output_folder = resolve_path(output_folder)
                        multi_folder = os.path.join(base_output_folder, "multivariate")
                        os.makedirs(multi_folder, exist_ok=True)
                        
                        # Build demographic filters
                        demographic_filters = []
                        if include_all:
                            demographic_filters.append({})  # Empty dict means no filter                        if include_men:
                            demographic_filters.append({"sex": "M"})
                        if include_women:
                            demographic_filters.append({"sex": "K"})
                        
                        for age_group in selected_age_groups:
                            demographic_filters.append({"age": age_group})
                        
                        multivariate_analysis.run_multivariate_analysis(
                            detailed_file=resolve_path(config.get("simulation", {}).get("detailed_output_file", "DetailedOutput.xlsx")),
                            output_folder=multi_folder,
                            demographic_filters=demographic_filters
                        )
                        
                        st.success("Multivariate analysis generated successfully!")
                        
                        # Show analysis results
                        if os.path.exists(multi_folder):
                            image_files = [f for f in os.listdir(multi_folder) if f.endswith(".png")]
                            
                            if image_files:
                                correlation_images = [f for f in image_files if "correlation" in f]
                                pca_images = [f for f in image_files if "pca" in f]
                                
                                st.write("**Correlation Analysis**")
                                for img_file in correlation_images:
                                    st.write(f"**{img_file.replace('.png', '').replace('_', ' ').title()}**")
                                    show_image(os.path.join(multi_folder, img_file))
                                    st.markdown("---")
                                
                                st.write("**Principal Component Analysis**")
                                for img_file in pca_images:
                                    st.write(f"**{img_file.replace('.png', '').replace('_', ' ').title()}**")
                                    show_image(os.path.join(multi_folder, img_file))
                                    st.markdown("---")
                except Exception as e:
                    st.error(f"Error generating multivariate analysis: {str(e)}")


if __name__ == "__main__":
    main()
