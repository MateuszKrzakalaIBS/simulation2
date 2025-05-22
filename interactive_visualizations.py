"""
Interactive visualization module for demographic simulation using Plotly.
This module provides interactive charts and visualizations of simulation results.
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import json
import sys

def load_config(config_path="config.json"):
    """
    Load configuration from JSON file.
    
    Parameters:
    -----------
    config_path : str
        Path to the configuration file
    
    Returns:
    --------
    dict
        Configuration dictionary
    """
    try:
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
            print(f"Loaded visualization configuration from {config_path}")
            return config
        else:
            print(f"Configuration file {config_path} not found. Using default settings.")
            return {
                "visualization": {
                    "output_folder": "plots",
                    "create_summary_plots": True,
                    "create_detailed_plots": True,
                    "plot_format": "html",
                    "color_scheme": "RdBu"
                }
            }
    except Exception as e:
        print(f"Error loading configuration: {str(e)}. Using default settings.")
        return {
            "visualization": {
                "output_folder": "plots",
                "create_summary_plots": True,
                "create_detailed_plots": True,
                "plot_format": "html",
                "color_scheme": "RdBu"
            }
        }

def visualize_summary_interactive(summary_df, config=None):
    """
    Create interactive visualizations for the summary results using Plotly.
    
    Parameters:
    -----------
    summary_df : pandas.DataFrame
        DataFrame containing the summary results
    config : dict
        Configuration dictionary with visualization settings
        
    Returns:
    --------
    dict
        Dictionary of Plotly figures that can be displayed in Streamlit
    """
    # Load config if not provided
    if config is None:
        config = load_config()
    
    # Extract visualization settings
    vis_config = config.get("visualization", {})
    output_folder = vis_config.get("output_folder", "plots")
    plot_format = vis_config.get("plot_format", "html")
    color_scheme = vis_config.get("color_scheme", "RdBu")
    
    # Create interactive plots folder
    interactive_folder = os.path.join(output_folder, "interactive")
    os.makedirs(interactive_folder, exist_ok=True)
    
    figures = {}
    
    # 1. Bar chart of relative changes
    sorted_df = summary_df.sort_values('relative_change_pct')
    
    fig_rel_changes = px.bar(
        sorted_df,
        x='relative_change_pct',
        y='variable',
        orientation='h',
        color='relative_change_pct',
        color_continuous_scale=color_scheme,
        title='Relative Change (%) in Variables Due to Scenario Change',
        labels={'relative_change_pct': 'Relative Change (%)', 'variable': 'Variable'},
        text=sorted_df['relative_change_pct'].apply(lambda x: f"{x:.2f}%")
    )
    
    fig_rel_changes.add_vline(x=0, line_width=2, line_dash="dash", line_color="black")
    fig_rel_changes.update_layout(
        font=dict(size=14),
        hoverlabel=dict(font_size=14),
        height=600,
        xaxis=dict(ticksuffix="%")
    )
    
    figures['relative_changes'] = fig_rel_changes
    
    # 2. Before and After comparison
    plot_df = summary_df.copy()
    max_val = plot_df[['result_bs', 'result_as']].max().max()
    
    # Create a more readable format for the data
    comparison_df = pd.DataFrame({
        'Variable': np.concatenate([plot_df['variable'], plot_df['variable']]),
        'Value': np.concatenate([plot_df['result_bs'], plot_df['result_as']]),
        'Scenario': np.concatenate([['Baseline'] * len(plot_df), ['Alternative'] * len(plot_df)])
    })
    
    fig_before_after = px.bar(
        comparison_df,
        x='Variable',
        y='Value',
        color='Scenario',
        barmode='group',
        title='Comparison of Baseline and Alternative Scenarios',
        labels={'Value': 'Value', 'Variable': 'Variable'},
        color_discrete_sequence=['#1f77b4', '#ff7f0e'],
        hover_data={'Value': ':.2f', 'Scenario': True, 'Variable': True}
    )
    
    fig_before_after.update_layout(
        font=dict(size=14),
        hoverlabel=dict(font_size=14),
        height=600,
        xaxis=dict(tickangle=45)
    )
    
    figures['before_after'] = fig_before_after
    
    # 3. Absolute Changes
    fig_abs_changes = px.bar(
        summary_df.sort_values('absolute_change', ascending=False),
        x='variable',
        y='absolute_change',
        color='absolute_change',
        color_continuous_scale=color_scheme,
        title='Absolute Change in Variables Due to Scenario Change',
        labels={'absolute_change': 'Absolute Change', 'variable': 'Variable'},
        text=summary_df.sort_values('absolute_change', ascending=False)['absolute_change'].apply(lambda x: f"{x:.2f}")
    )
    
    fig_abs_changes.update_layout(
        font=dict(size=14),
        hoverlabel=dict(font_size=14),
        height=600,
        xaxis=dict(tickangle=45)
    )
    
    figures['absolute_changes'] = fig_abs_changes
    
    # Save figures to HTML files
    if plot_format == "html":
        for name, fig in figures.items():
            fig.write_html(os.path.join(interactive_folder, f"{name}.html"))
    
    return figures

def visualize_detailed_interactive(detailed_df, variable_name, config=None):
    """
    Create interactive visualizations for detailed results using Plotly.
    
    Parameters:
    -----------
    detailed_df : pandas.DataFrame
        DataFrame containing the detailed results for a specific variable
    variable_name : str
        Name of the variable being visualized
    config : dict
        Configuration dictionary with visualization settings
        
    Returns:
    --------
    dict
        Dictionary of Plotly figures that can be displayed in Streamlit
    """
    # Load config if not provided
    if config is None:
        config = load_config()
    
    # Extract visualization settings
    vis_config = config.get("visualization", {})
    output_folder = vis_config.get("output_folder", "plots")
    plot_format = vis_config.get("plot_format", "html")
    color_scheme = vis_config.get("color_scheme", "RdBu")
    
    # Create interactive plots folder
    interactive_folder = os.path.join(output_folder, "interactive", variable_name)
    os.makedirs(interactive_folder, exist_ok=True)
    
    figures = {}
    
    # Check if necessary columns exist
    required_cols = ['age', 'sex', 'result_bs', 'result_as', 'difference', 'difference_pct']
    if not all(col in detailed_df.columns for col in required_cols):
        print(f"Warning: Detailed dataframe for {variable_name} is missing required columns.")
        return figures
    
    # 1. Heatmap of values by demographic group
    pivot_df = detailed_df.pivot_table(
        index='age', 
        columns='sex',
        values='difference_pct'
    )
    
    fig_heatmap = px.imshow(
        pivot_df,
        title=f"Change in {variable_name} by Demographic Group (%)",
        labels=dict(x="Sex", y="Age Group", color="Change (%)"),
        color_continuous_scale=color_scheme,
        zmin=-10,  # Adjust as needed
        zmax=10,   # Adjust as needed
        aspect="auto",
        text_auto='.1f'
    )
    
    fig_heatmap.update_layout(
        height=800,
        width=600,
        coloraxis_colorbar=dict(title="Change (%)")
    )
    
    figures['demographic_heatmap'] = fig_heatmap
    
    # 2. Age group comparison (before vs after)
    age_comparison_df = detailed_df.groupby('age').agg({
        'result_bs': 'mean',
        'result_as': 'mean',
        'difference': 'mean',
        'difference_pct': 'mean'
    }).reset_index()
    
    # Create a more readable format for the data
    age_comp_df = pd.DataFrame({
        'Age Group': np.concatenate([age_comparison_df['age'], age_comparison_df['age']]),
        'Value': np.concatenate([age_comparison_df['result_bs'], age_comparison_df['result_as']]),
        'Scenario': np.concatenate([['Baseline'] * len(age_comparison_df), ['Alternative'] * len(age_comparison_df)])
    })
    
    fig_age_comparison = px.bar(
        age_comp_df,
        x='Age Group',
        y='Value',
        color='Scenario',
        barmode='group',
        title=f"{variable_name} by Age Group - Baseline vs Alternative",
        labels={'Value': 'Value', 'Age Group': 'Age Group'},
        color_discrete_sequence=['#1f77b4', '#ff7f0e']
    )
    
    fig_age_comparison.update_layout(
        font=dict(size=14),
        hoverlabel=dict(font_size=14),
        height=500
    )
    
    figures['age_comparison'] = fig_age_comparison
    
    # 3. Age group differences
    fig_age_diff = px.bar(
        age_comparison_df,
        x='age',
        y='difference_pct',
        title=f"Difference in {variable_name} by Age Group (%)",
        labels={'difference_pct': 'Difference (%)', 'age': 'Age Group'},
        color='difference_pct',
        color_continuous_scale=color_scheme,
        text=age_comparison_df['difference_pct'].apply(lambda x: f"{x:.2f}%")
    )
    
    fig_age_diff.add_hline(y=0, line_width=2, line_dash="dash", line_color="black")
    fig_age_diff.update_layout(
        font=dict(size=14),
        hoverlabel=dict(font_size=14),
        height=500,
        yaxis=dict(ticksuffix="%")
    )
    
    figures['age_difference'] = fig_age_diff
    
    # Save figures to HTML files
    if plot_format == "html":
        for name, fig in figures.items():
            fig.write_html(os.path.join(interactive_folder, f"{variable_name}_{name}.html"))
    
    return figures


def generate_interactive_dashboard(summary_df, detailed_dfs, config=None):
    """
    Generate an interactive dashboard HTML file with multiple plots
    
    Parameters:
    -----------
    summary_df : pandas.DataFrame
        DataFrame with summary results
    detailed_dfs : dict
        Dictionary of detailed DataFrames by variable
    config : dict
        Configuration dictionary
        
    Returns:
    --------
    str
        Path to the generated dashboard HTML file
    """
    if config is None:
        config = load_config()
    
    vis_config = config.get("visualization", {})
    output_folder = vis_config.get("output_folder", "plots")
    interactive_folder = os.path.join(output_folder, "interactive")
    os.makedirs(interactive_folder, exist_ok=True)
    
    dashboard_path = os.path.join(interactive_folder, "dashboard.html")
    
    # Generate summary visualizations
    summary_figs = visualize_summary_interactive(summary_df, config)
    
    # Create a dashboard with subplots
    dashboard = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "Relative Changes (%)", 
            "Before vs After Comparison",
            "Absolute Changes",
            "Variable Selection"
        ),
        specs=[
            [{"type": "bar"}, {"type": "bar"}],
            [{"type": "bar"}, {"type": "indicator"}]
        ],
        vertical_spacing=0.1,
        horizontal_spacing=0.05
    )
    
    # Add the plots
    # Relative Changes
    rel_changes_fig = summary_figs['relative_changes']
    for trace in rel_changes_fig.data:
        dashboard.add_trace(trace, row=1, col=1)
    
    # Before vs After
    before_after_fig = summary_figs['before_after']
    for trace in before_after_fig.data:
        dashboard.add_trace(trace, row=1, col=2)
    
    # Absolute Changes
    abs_changes_fig = summary_figs['absolute_changes']
    for trace in abs_changes_fig.data:
        dashboard.add_trace(trace, row=2, col=1)
    
    # Variable Selector - we'll add a dropdown with JavaScript in the HTML
    
    # Update layout
    dashboard.update_layout(
        title_text="Demographic Simulation Dashboard",
        height=1200,
        width=1600,
        template="plotly_white",
        showlegend=True
    )
    
    # Add some custom HTML/JS for variable selection interactivity
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Demographic Simulation Dashboard</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
            .dashboard-container { width: 95%; margin: 0 auto; }
            .header { text-align: center; margin-bottom: 20px; }
            select { padding: 8px; font-size: 16px; margin: 10px 0; }
            .variable-details { margin-top: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="dashboard-container">
            <div class="header">
                <h1>Demographic Simulation Interactive Dashboard</h1>
                <p>Explore the impacts of demographic changes across variables and population segments</p>
            </div>
            
            <div id="main-dashboard"></div>
            
            <div class="variable-selector">
                <h2>Variable Details</h2>
                <select id="variable-select">
                    <option value="">Select a variable to view details...</option>
                </select>
            </div>
            
            <div id="variable-details" class="variable-details" style="display:none;">
                <div id="demographic-heatmap"></div>
                <div id="age-comparison"></div>
                <div id="age-difference"></div>
            </div>
        </div>
        
        <script>
            // Main dashboard
            var dashboardDiv = document.getElementById('main-dashboard');
            
            // Load the main dashboard
            Plotly.newPlot(dashboardDiv, {
    """
    
    # Add the dashboard JSON
    dashboard_json = dashboard.to_json()
    html_content += f"data: {dashboard_json},"
    
    html_content += """
            }, {responsive: true});
            
            // Variable selector
            var variableSelect = document.getElementById('variable-select');
            var variableDetails = document.getElementById('variable-details');
            var heatmapDiv = document.getElementById('demographic-heatmap');
            var ageCompDiv = document.getElementById('age-comparison');
            var ageDiffDiv = document.getElementById('age-difference');
            
            // Populate the variable dropdown (to be filled with actual variables)
            var variables = [];
    """
    
    # Add the variables list as JavaScript
    var_list_js = "[" + ", ".join([f"'{var}'" for var in summary_df['variable']]) + "]"
    html_content += f"variables = {var_list_js};"
    
    html_content += """
            // Add options to the dropdown
            variables.forEach(function(variable) {
                var option = document.createElement('option');
                option.value = variable;
                option.text = variable;
                variableSelect.appendChild(option);
            });
            
            // Handle variable selection
            variableSelect.addEventListener('change', function() {
                var selectedVar = this.value;
                if (!selectedVar) {
                    variableDetails.style.display = 'none';
                    return;
                }
                
                variableDetails.style.display = 'block';
                
                // Load the detailed visualizations for this variable
                // This would be replaced with actual paths to the generated files
                var basePath = './'; // Adjust as needed
                
                // Load heatmap
                fetch(basePath + selectedVar + '_demographic_heatmap.html')
                    .then(response => response.text())
                    .then(html => {
                        var parser = new DOMParser();
                        var doc = parser.parseFromString(html, 'text/html');
                        var plotlyDiv = doc.getElementById('plotly');
                        var plotlyData = JSON.parse(plotlyDiv.getAttribute('data-plotly'));
                        Plotly.newPlot(heatmapDiv, plotlyData.data, plotlyData.layout);
                    });
                
                // Load age comparison
                fetch(basePath + selectedVar + '_age_comparison.html')
                    .then(response => response.text())
                    .then(html => {
                        var parser = new DOMParser();
                        var doc = parser.parseFromString(html, 'text/html');
                        var plotlyDiv = doc.getElementById('plotly');
                        var plotlyData = JSON.parse(plotlyDiv.getAttribute('data-plotly'));
                        Plotly.newPlot(ageCompDiv, plotlyData.data, plotlyData.layout);
                    });
                
                // Load age difference
                fetch(basePath + selectedVar + '_age_difference.html')
                    .then(response => response.text())
                    .then(html => {
                        var parser = new DOMParser();
                        var doc = parser.parseFromString(html, 'text/html');
                        var plotlyDiv = doc.getElementById('plotly');
                        var plotlyData = JSON.parse(plotlyDiv.getAttribute('data-plotly'));
                        Plotly.newPlot(ageDiffDiv, plotlyData.data, plotlyData.layout);
                    });
            });
        </script>
    </body>
    </html>
    """
    
    # Write the HTML file
    with open(dashboard_path, 'w') as f:
        f.write(html_content)
    
    # Generate individual variable visualizations
    for var_name, df in detailed_dfs.items():
        visualize_detailed_interactive(df, var_name, config)
    
    return dashboard_path
