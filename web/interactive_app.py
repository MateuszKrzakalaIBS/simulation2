"""
Interactive dashboard for demographic simulation.
This script creates an interactive web interface using Streamlit and Plotly.
"""

import streamlit as st
import pandas as pd
import numpy as np
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
import interactive_visualizations

def load_config():
    """Load configuration from JSON file."""
    try:
        # First try in parent directory, then in current directory
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
                    "plot_format": "html",
                    "color_scheme": "RdBu"
                }
            }
    except Exception as e:
        st.error(f"Error loading configuration: {str(e)}")
        return {}

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

def run_interactive_visualization(config):
    """Run interactive visualization with the current configuration."""
    try:
        with st.spinner("Creating interactive visualizations..."):
            # Make sure all paths are resolved correctly
            output_folder = config.get("visualization", {}).get("output_folder", "plots")
            output_folder = resolve_path(output_folder)
            
            input_file = config.get("simulation", {}).get("input_file", "Input.xlsx")
            output_file = config.get("simulation", {}).get("output_file", "Output.xlsx")
            detailed_output_file = config.get("simulation", {}).get("detailed_output_file", "DetailedOutput.xlsx")
            
            # Resolve paths
            output_file_path = resolve_path(output_file)
            detailed_output_file_path = resolve_path(detailed_output_file)
            
            # Load data
            summary_df = pd.read_excel(output_file_path)
            
            # Get the detailed DataFrames for each variable
            detailed_dfs = {}
            for _, row in summary_df.iterrows():
                var = row['variable']
                try:
                    # Read the variable-specific sheet from the detailed output
                    var_df = pd.read_excel(detailed_output_file_path, sheet_name=var[:30])  # Sheet names limited to 30 chars
                    detailed_dfs[var] = var_df
                except Exception as var_e:
                    st.warning(f"Could not read detailed data for {var}: {str(var_e)}")
            
            # Generate the interactive dashboard
            dashboard_path = interactive_visualizations.generate_interactive_dashboard(
                summary_df=summary_df,
                detailed_dfs=detailed_dfs,
                config=config
            )
            
            # Create individual visualizations for summary
            summary_figs = interactive_visualizations.visualize_summary_interactive(summary_df, config)
            
            st.success("Interactive visualizations created successfully!")
            return summary_figs, detailed_dfs, dashboard_path
            
    except Exception as e:
        st.error(f"Error creating interactive visualizations: {str(e)}")
        return None, None, None

def main():
    """Main Streamlit app."""
    st.set_page_config(
        page_title="Interactive Demographic Simulation",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    
    st.title("Interactive Demographic Counterfactual Simulation")
    st.write("""
    This interactive dashboard allows you to run demographic simulations and visualize their results.
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
                                  options=["RdBu", "Viridis", "Plasma", "Inferno", "Magma", "Cividis"],
                                  index=0)
        
        # Update visualization config
        if "visualization" not in config:
            config["visualization"] = {}
        
        config["visualization"]["output_folder"] = output_folder
        config["visualization"]["color_scheme"] = color_scheme
        
        # Process variable exclusions
        var_excludes = [v.strip() for v in var_exclude_text.split(",") if v.strip()]
        config["simulation"]["variables_to_exclude"] = var_excludes
    
    # Main content
    tab1, tab2, tab3 = st.tabs(["Simulation", "Interactive Dashboard", "Data Explorer"])
    
    # Tab 1: Simulation
    with tab1:
        st.header("Run Simulation")
        st.write("""
        This will run the demographic simulation with the current configuration.
        The simulation applies demographic factors and shock scenarios to analyze their impact on variables.
        """)
        
        # Show current shock scenario
        st.subheader("Current Shock Scenario")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("s1 Change", f"{s1_change:+.2f}")
        with col2:
            st.metric("s2 Change", f"{s2_change:+.2f}")
        with col3:
            st.metric("s3 Change", f"{s3_change:+.2f}")
        
        # Button to run simulation
        if st.button("Run Simulation"):
            summary_df, detailed_df = run_simulation(config)
            
            if summary_df is not None:
                st.subheader("Simulation Results Summary")
                st.dataframe(summary_df, use_container_width=True)
                
                # Visualization button
                if st.button("Create Interactive Visualizations"):
                    summary_figs, detailed_dfs, dashboard_path = run_interactive_visualization(config)
                    
                    # Display dashboard link
                    if dashboard_path:
                        st.success(f"Interactive dashboard created at: {dashboard_path}")
                        st.info("Go to the 'Interactive Dashboard' tab to explore the results.")
    
    # Tab 2: Interactive Dashboard
    with tab2:
        st.header("Interactive Visualization Dashboard")
        
        # Check if visualization outputs exist
        output_folder = config.get("visualization", {}).get("output_folder", "plots")
        interactive_folder = os.path.join(resolve_path(output_folder), "interactive")
        dashboard_path = os.path.join(interactive_folder, "dashboard.html")
        
        if os.path.exists(dashboard_path):
            st.write("Interactive dashboard is available. You can explore it directly in the browser.")
            
            # Create a button to open the dashboard in a new tab
            st.markdown(f'''
                <a href="file://{dashboard_path}" target="_blank">
                    <button style="background-color:#4CAF50;color:white;padding:12px 20px;border:none;border-radius:4px;cursor:pointer;">
                        Open Interactive Dashboard
                    </button>
                </a>
                ''', 
                unsafe_allow_html=True
            )
            
            # Try to load summary figures
            try:
                output_file_path = resolve_path(config.get("simulation", {}).get("output_file", "Output.xlsx"))
                summary_df = pd.read_excel(output_file_path)
                
                # Create interactive plots for display in Streamlit
                summary_figs = interactive_visualizations.visualize_summary_interactive(summary_df, config)
                
                # Display plots in Streamlit
                st.subheader("Relative Changes (%)")
                st.plotly_chart(summary_figs['relative_changes'], use_container_width=True)
                
                st.subheader("Before vs After Comparison")
                st.plotly_chart(summary_figs['before_after'], use_container_width=True)
                
                st.subheader("Absolute Changes")
                st.plotly_chart(summary_figs['absolute_changes'], use_container_width=True)
                
                # Variable explorer
                st.subheader("Variable Explorer")
                selected_var = st.selectbox("Select a variable to explore", 
                                           options=[""] + list(summary_df['variable']))
                
                if selected_var:
                    try:
                        # Load detailed data for this variable
                        detailed_output_file_path = resolve_path(config.get("simulation", {}).get("detailed_output_file", "DetailedOutput.xlsx"))
                        var_df = pd.read_excel(detailed_output_file_path, sheet_name=selected_var[:30])
                          # Create interactive visualizations for this variable
                        var_figs = interactive_visualizations.visualize_detailed_interactive(var_df, selected_var, config)
                        
                        # Display the basic visualizations
                        st.subheader(f"Demographic Impact Analysis for {selected_var}")
                        
                        # Get variable type and additional metrics
                        var_type = None
                        var_row = summary_df[summary_df['variable'] == selected_var].iloc[0] if not summary_df[summary_df['variable'] == selected_var].empty else None
                        
                        if var_row is not None:
                            # Display both relative and absolute metrics
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Relative Change (%)", f"{var_row.get('relative_change_pct', 0):.2f}%")
                            with col2:
                                st.metric("Absolute Change", f"{var_row.get('absolute_change', 0):.4f}")
                                
                            # Display specialized metrics based on variable type
                            if "total_employed_bs" in var_row:
                                # Employment metrics
                                st.subheader("Employment Metrics")
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.metric("Total Employed (Baseline)", f"{var_row.get('total_employed_bs', 0):,.0f}")
                                    st.metric("Total Employed (Alternative)", f"{var_row.get('total_employed_as', 0):,.0f}")
                                with col2:
                                    st.metric("Net Employment Change", f"{var_row.get('employed_change', 0):,.0f}")
                                    st.metric("Employment Change (%)", f"{var_row.get('employed_change_pct', 0):.2f}%")
                                var_type = "employment"
                                diff_col = selected_var + "_contribution"
                                
                            elif "total_impact_bs" in var_row:
                                # Per-capita variables (health indicators, absence, costs)
                                st.subheader("Total Impact Metrics")
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.metric("Total Impact (Baseline)", f"{var_row.get('total_impact_bs', 0):,.2f}")
                                    st.metric("Total Impact (Alternative)", f"{var_row.get('total_impact_as', 0):,.2f}")
                                with col2:
                                    st.metric("Net Impact Change", f"{var_row.get('impact_change', 0):,.2f}")
                                    st.metric("Impact Change (%)", f"{var_row.get('impact_change_pct', 0):.2f}%")
                                var_type = "per_capita"
                                diff_col = selected_var + "_total_diff"
                                
                                # Special case for absence
                                if selected_var == "absence" and "total_days_lost_bs" in var_row:
                                    st.subheader("Absence Days Metrics")
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.metric("Total Days Lost (Baseline)", f"{var_row.get('total_days_lost_bs', 0):,.0f}")
                                        st.metric("Total Days Lost (Alternative)", f"{var_row.get('total_days_lost_as', 0):,.0f}")
                                    with col2:
                                        st.metric("Days Lost Change", f"{var_row.get('days_lost_change', 0):,.0f}")
                                        if 'economic_impact_change' in var_row:
                                            st.metric("Economic Impact", f"${var_row.get('economic_impact_change', 0):,.2f}")
                                
                                # Special case for public health costs
                                if selected_var == "public_health_costs" and "total_costs_bs" in var_row:
                                    st.subheader("Public Health Costs Metrics")
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.metric("Total Costs (Baseline)", f"${var_row.get('total_costs_bs', 0):,.2f}")
                                        st.metric("Total Costs (Alternative)", f"${var_row.get('total_costs_as', 0):,.2f}")
                                    with col2:
                                        cost_savings = var_row.get('cost_savings', 0)
                                        additional_costs = var_row.get('additional_costs', 0)
                                        if cost_savings > 0:
                                            st.metric("Cost Savings", f"${cost_savings:,.2f}")
                                        else:
                                            st.metric("Additional Costs", f"${additional_costs:,.2f}")
                                        if 'per_capita_cost_change' in var_row:
                                            st.metric("Per Capita Change", f"${var_row.get('per_capita_cost_change', 0):,.2f}")
                                
                            elif "total_affected_bs" in var_row:
                                # Prevalence variables
                                st.subheader("Prevalence Metrics")
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.metric("Total Affected (Baseline)", f"{var_row.get('total_affected_bs', 0):,.0f}")
                                    st.metric("Total Affected (Alternative)", f"{var_row.get('total_affected_as', 0):,.0f}")
                                with col2:
                                    st.metric("Affected Change", f"{var_row.get('affected_change', 0):,.0f}")
                                    if 'prevalence_change' in var_row:
                                        st.metric("Prevalence Change (%)", f"{var_row.get('prevalence_change', 0):.2f}%")
                                var_type = "prevalence"
                                diff_col = selected_var + "_absolute_diff"
                        
                        # Create demographic visualizations for this variable
                        st.subheader("Demographic Analysis")
                        
                        try:
                            # Create tabs for different visualizations
                            demo_tab1, demo_tab2, demo_tab3 = st.tabs(["Original Visualizations", "Contribution Analysis", "Demographic Heatmap"])
                            
                            with demo_tab1:
                                # Display the original visualizations
                                st.subheader(f"Demographic Heatmap")
                                st.plotly_chart(var_figs['demographic_heatmap'], use_container_width=True)
                                
                                st.subheader(f"Age Group Comparison")
                                st.plotly_chart(var_figs['age_comparison'], use_container_width=True)
                                
                                st.subheader(f"Age Group Differences")
                                st.plotly_chart(var_figs['age_difference'], use_container_width=True)
                            
                            with demo_tab2:
                                st.write("This chart shows which demographic groups contribute most to the overall change:")
                                # Create demographic contribution chart
                                if var_type is not None and 'diff_col' in locals():
                                    contrib_fig = interactive_visualizations.create_demographic_contribution_chart(
                                        summary_df, var_df, selected_var, config
                                    )
                                    st.plotly_chart(contrib_fig, use_container_width=True)
                                else:
                                    st.write("Demographic contribution data not available for this variable.")
                            
                            with demo_tab3:
                                st.write("This heatmap shows the distribution of impact across age and sex groups:")
                                # Create heat map visualization
                                if var_type == "employment":
                                    heatmap_col = selected_var + "_contribution"
                                elif var_type == "per_capita":
                                    heatmap_col = selected_var + "_total_diff"
                                elif var_type == "prevalence":
                                    heatmap_col = selected_var + "_absolute_diff"
                                else:
                                    heatmap_col = selected_var + "_diff"
                                    
                                heatmap_fig = interactive_visualizations.create_demographic_impact_heatmap(
                                    var_df, selected_var, heatmap_col, config
                                )
                                st.plotly_chart(heatmap_fig, use_container_width=True)
                                
                        except Exception as viz_err:
                            st.error(f"Error creating demographic visualizations: {str(viz_err)}")
                        
                        # Display detailed data
                        st.subheader("Detailed Data")
                        st.dataframe(var_df, use_container_width=True)
                    except Exception as e:
                        st.error(f"Error displaying variable details: {str(e)}")
                
            except Exception as e:
                st.error(f"Error loading interactive visualizations: {str(e)}")
        else:
            st.info("No interactive dashboard found. Please run a simulation and create visualizations first.")
    
    # Tab 3: Data Explorer
    with tab3:
        st.header("Data Explorer")
        
        try:
            # Load input data
            input_file_path = resolve_path(config.get("simulation", {}).get("input_file", "Input.xlsx"))
            output_file_path = resolve_path(config.get("simulation", {}).get("output_file", "Output.xlsx"))
            detailed_output_file_path = resolve_path(config.get("simulation", {}).get("detailed_output_file", "DetailedOutput.xlsx"))
            
            # Input data
            st.subheader("Input Data")
            if os.path.exists(input_file_path):
                # Show available sheets
                input_xl = pd.ExcelFile(input_file_path)
                input_sheets = input_xl.sheet_names
                selected_input_sheet = st.selectbox("Select Input Sheet", options=input_sheets)
                
                if selected_input_sheet:
                    input_df = pd.read_excel(input_file_path, sheet_name=selected_input_sheet)
                    st.dataframe(input_df, use_container_width=True)
            else:
                st.warning(f"Input file not found: {input_file_path}")
            
            # Output data
            st.subheader("Output Data")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("Summary Results")
                if os.path.exists(output_file_path):
                    summary_df = pd.read_excel(output_file_path)
                    st.dataframe(summary_df, use_container_width=True)
                else:
                    st.warning(f"Output file not found: {output_file_path}")
            
            with col2:
                st.write("Detailed Results")
                if os.path.exists(detailed_output_file_path):
                    # Show available sheets
                    detailed_xl = pd.ExcelFile(detailed_output_file_path)
                    detailed_sheets = detailed_xl.sheet_names
                    selected_detailed_sheet = st.selectbox("Select Variable", options=detailed_sheets)
                    
                    if selected_detailed_sheet:
                        detailed_df = pd.read_excel(detailed_output_file_path, sheet_name=selected_detailed_sheet)
                        st.dataframe(detailed_df, use_container_width=True)
                else:
                    st.warning(f"Detailed output file not found: {detailed_output_file_path}")
            
        except Exception as e:
            st.error(f"Error in Data Explorer: {str(e)}")

if __name__ == "__main__":
    main()
