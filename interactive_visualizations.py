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
    
    # 4. Total Impact Changes - New visualization for total impacts across the population
    # First create a dataframe with variables that have total impact metrics
    impact_metrics = []
    
    # Process each variable to get the right impact metric based on its type
    for _, row in summary_df.iterrows():
        var = row['variable']
        impact_row = {
            'variable': var,
            'friendly_name': var.replace('_', ' ').title()  # Simple transformation for display
        }
        
        # Employment variables - show total employed
        if 'total_employed_bs' in row and 'total_employed_as' in row:
            impact_row.update({
                'impact_type': 'Employment',
                'total_bs': row['total_employed_bs'],
                'total_as': row['total_employed_as'],
                'total_change': row['employed_change'],
                'total_change_pct': row['employed_change_pct'] if 'employed_change_pct' in row else None
            })
            impact_metrics.append(impact_row)
        
        # Health indicators and per-capita variables - show total impact
        elif 'total_impact_bs' in row and 'total_impact_as' in row:
            impact_row.update({
                'impact_type': 'Total Impact',
                'total_bs': row['total_impact_bs'],
                'total_as': row['total_impact_as'],
                'total_change': row['impact_change'],
                'total_change_pct': row['impact_change_pct'] if 'impact_change_pct' in row else None
            })
            impact_metrics.append(impact_row)
            
            # For specific variables, add specialized metrics
            if var == 'absence' and 'total_days_lost_bs' in row:
                impact_row = {
                    'variable': var + '_days',
                    'friendly_name': 'Absence Days Lost',
                    'impact_type': 'Days Lost',
                    'total_bs': row['total_days_lost_bs'],
                    'total_as': row['total_days_lost_as'],
                    'total_change': row['days_lost_change'],
                    'total_change_pct': row['days_lost_change_pct'] if 'days_lost_change_pct' in row else None
                }
                impact_metrics.append(impact_row)
            
            elif var == 'public_health_costs' and 'total_costs_bs' in row:
                impact_row = {
                    'variable': var + '_costs',
                    'friendly_name': 'Public Health Costs',
                    'impact_type': 'Costs',
                    'total_bs': row['total_costs_bs'],
                    'total_as': row['total_costs_as'],
                    'total_change': row['cost_savings'] if 'cost_savings' in row and row['cost_savings'] > 0 else row['additional_costs'] if 'additional_costs' in row else None,
                    'is_saving': 'cost_savings' in row and row['cost_savings'] > 0
                }
                impact_metrics.append(impact_row)
        
        # Prevalence variables - show total affected individuals
        elif 'total_affected_bs' in row and 'total_affected_as' in row:
            impact_row.update({
                'impact_type': 'Affected Population',
                'total_bs': row['total_affected_bs'],
                'total_as': row['total_affected_as'],
                'total_change': row['affected_change'],
                'total_change_pct': row['affected_change_pct'] if 'affected_change_pct' in row else None
            })
            impact_metrics.append(impact_row)
    
    # Create the visualization if we have impact metrics
    if impact_metrics:
        impact_df = pd.DataFrame(impact_metrics)
        
        # Sort by absolute change for better visualization
        impact_df = impact_df.sort_values('total_change', key=abs, ascending=False)
        
        # Create the visualization
        fig_total_impact = px.bar(
            impact_df,
            x='friendly_name',
            y='total_change',
            color='total_change',
            color_continuous_scale=color_scheme,
            title='Total Population-Level Impact of Scenario Change',
            labels={'total_change': 'Total Change', 'friendly_name': 'Variable'},
            text=impact_df['total_change'].apply(lambda x: f"{x:.1f}"),
            hover_data=['total_bs', 'total_as', 'total_change_pct'],
            category_orders={"friendly_name": impact_df['friendly_name'].tolist()}
        )
        
        fig_total_impact.update_layout(
            font=dict(size=14),
            hoverlabel=dict(font_size=14),
            height=600,
            xaxis=dict(tickangle=45)
        )
        
        figures['total_impact'] = fig_total_impact
        
        # 5. Before/After Total Impact Comparison
        fig_total_comparison = px.bar(
            impact_df,
            x='friendly_name',
            y=['total_bs', 'total_as'],
            barmode='group',
            title='Comparison of Total Impact Before and After Scenario Change',
            labels={'value': 'Total Value', 'friendly_name': 'Variable', 'variable': 'Scenario'},
            category_orders={"friendly_name": impact_df['friendly_name'].tolist()},
            color_discrete_map={'total_bs': '#1f77b4', 'total_as': '#ff7f0e'}
        )
        
        # Update names in legend
        new_names = {'total_bs': 'Baseline', 'total_as': 'Alternative'}
        fig_total_comparison.for_each_trace(lambda t: t.update(name=new_names[t.name]))
        
        fig_total_comparison.update_layout(
            font=dict(size=14),
            hoverlabel=dict(font_size=14),
            height=600,
            xaxis=dict(tickangle=45),
            legend_title="Scenario"
        )
        
        figures['total_comparison'] = fig_total_comparison
    
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
        rows=3, cols=2,
        subplot_titles=(
            "Relative Changes (%)", 
            "Before vs After Comparison",
            "Absolute Changes",
            "Total Population Impact",
            "Total Impact Before/After",
            "Variable Selection"
        ),
        specs=[
            [{"type": "bar"}, {"type": "bar"}],
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
    
    # Total Impact (if available)
    if 'total_impact' in summary_figs:
        total_impact_fig = summary_figs['total_impact']
        for trace in total_impact_fig.data:
            dashboard.add_trace(trace, row=2, col=2)
    
    # Total Comparison (if available)
    if 'total_comparison' in summary_figs:
        total_comparison_fig = summary_figs['total_comparison']
        for trace in total_comparison_fig.data:
            dashboard.add_trace(trace, row=3, col=1)
    
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
        <style>            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
            .dashboard-container { width: 95%; margin: 0 auto; }
            .header { text-align: center; margin-bottom: 20px; }
            select { padding: 8px; font-size: 16px; margin: 10px 0; }
            .variable-details { margin-top: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
            .metric-container { display: flex; flex-wrap: wrap; margin-bottom: 15px; }
            .metric-box { flex: 1; min-width: 200px; padding: 15px; margin: 5px; border: 1px solid #eee; border-radius: 5px; text-align: center; }
            .metric-value { font-size: 24px; font-weight: bold; margin: 10px 0; }
            .metric-title { font-size: 14px; color: #555; }
            .metric-change { font-size: 14px; }
            .metric-change.positive { color: green; }
            .metric-change.negative { color: red; }
            .tabs { display: flex; border-bottom: 1px solid #ddd; margin-bottom: 20px; }
            .tab { padding: 10px 20px; cursor: pointer; }
            .tab.active { background-color: #f5f5f5; border: 1px solid #ddd; border-bottom: none; }
            .tab-content { display: none; }
            .tab-content.active { display: block; }
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
            // Plotly.newPlot(dashboardDiv, { // This line will be effectively replaced by the logic below
    """
    
    # Add the dashboard JSON
    dashboard_json_str = dashboard.to_json() # Get the JSON string for the figure
    # Properly embed it as a JavaScript object literal
    html_content += f"var figure = {dashboard_json_str};\\n" 
    
    html_content += """
            Plotly.newPlot(dashboardDiv, figure.data, figure.layout, {responsive: true});
            
            // Variable details
            var variableSelect = document.getElementById('variable-select');
            var variableDetails = document.getElementById('variable-details');
            var heatmapDiv = document.getElementById('demographic-heatmap');
            var ageCompDiv = document.getElementById('age-comparison');
            var ageDiffDiv = document.getElementById('age-difference');
            
            // Populate the variable dropdown (to be filled with actual variables)
            var variables = [];
    """
    
    # Add the variables list as JavaScript
    var_list_js = "[" + ", ".join([f"\\\'{var}\\\'" for var in summary_df['variable']]) + "]" # Escaped quotes for JS
    html_content += f"variables = {var_list_js};\\n" # Added newline for clarity
    
    html_content += """
            function renderFetchedPlot(targetDiv, htmlContent) {
                var parser = new DOMParser();
                var doc = parser.parseFromString(htmlContent, 'text/html');
                var scripts = Array.from(doc.getElementsByTagName('script'));
                var plotlyScript = scripts.find(s => s.textContent.includes('Plotly.newPlot') || s.textContent.includes('Plotly.react'));

                if (plotlyScript) {
                    var scriptText = plotlyScript.textContent;
                    // Regex to capture data (an array) and layout (an object) from Plotly's newPlot/react calls
                    var match = scriptText.match(/Plotly\\\\.(?:newPlot|react)\\\\s*\\\\(\\\\s*[^,]+,\\\\s*(\\\\[[\\\\s\\\\S]*?\\\\])\\\\s*,\\\\s*(\\\\{[\\\\s\\\\S]*?\\\\})\\\\s*(?:,\\\\s*(\\\\{[\\\\s\\\\S]*?\\\\}))?\\\\s*\\\\);/);
                    if (match) {
                        var dataStr = match[1];
                        var layoutStr = match[2];
                        try {
                            var dataObj = (new Function('return ' + dataStr))();
                            var layoutObj = (new Function('return ' + layoutStr))();
                            Plotly.newPlot(targetDiv, dataObj, layoutObj, {responsive: true});
                        } catch (e) {
                            console.error('Error parsing plot data/layout from script:', e, 'Data:', dataStr, 'Layout:', layoutStr);
                            targetDiv.textContent = 'Error rendering plot.';
                        }
                    } else {
                        console.error('Could not extract plot arguments from script. Script content:', scriptText);
                        targetDiv.textContent = 'Could not parse plot data from fetched HTML.';
                    }
                } else {
                    targetDiv.textContent = 'Could not find Plotly script in fetched HTML.';
                }
            }

            // Add options to the dropdown
            variables.forEach(function(variable) {
                var option = document.createElement('option');
                option.value = variable;
                option.textContent = variable.replace(/_/g, ' ').toUpperCase();
                variableSelect.appendChild(option);
            });
            
            // Handle variable selection
            variableSelect.addEventListener('change', function() {
                var selectedVar = variableSelect.value;
                if (!selectedVar) {
                    variableDetails.style.display = 'none';
                    return;
                }
                
                variableDetails.style.display = 'block';
                
                // Load the detailed visualizations for this variable
                var basePath = './'; // Relative to dashboard.html

                // Load heatmap
                fetch(basePath + selectedVar + '/' + selectedVar + '_demographic_heatmap.html')
                    .then(response => {
                        if (!response.ok) throw new Error('Network response was not ok for heatmap: ' + response.statusText);
                        return response.text();
                    })
                    .then(html => renderFetchedPlot(heatmapDiv, html))
                    .catch(error => {
                        console.error('Error fetching heatmap HTML:', error);
                        heatmapDiv.textContent = 'Failed to load heatmap. Check console for details.';
                    });
                
                // Load age comparison
                fetch(basePath + selectedVar + '/' + selectedVar + '_age_comparison.html')
                    .then(response => {
                        if (!response.ok) throw new Error('Network response was not ok for age comparison: ' + response.statusText);
                        return response.text();
                    })
                    .then(html => renderFetchedPlot(ageCompDiv, html))
                    .catch(error => {
                        console.error('Error fetching age comparison HTML:', error);
                        ageCompDiv.textContent = 'Failed to load age comparison plot. Check console for details.';
                    });
                
                // Load age difference
                fetch(basePath + selectedVar + '/' + selectedVar + '_age_difference.html')
                    .then(response => {
                        if (!response.ok) throw new Error('Network response was not ok for age difference: ' + response.statusText);
                        return response.text();
                    })
                    .then(html => renderFetchedPlot(ageDiffDiv, html))
                    .catch(error => {
                        console.error('Error fetching age difference HTML:', error);
                        ageDiffDiv.textContent = 'Failed to load age difference plot. Check console for details.';
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

def create_demographic_contribution_chart(summary_df, detailed_df, variable_name, config=None):
    """
    Create an interactive chart showing demographic contributions to the change in a variable.
    
    Parameters:
    -----------
    summary_df : pandas.DataFrame
        DataFrame containing the summary results
    detailed_df : pandas.DataFrame
        DataFrame containing detailed results for the variable
    variable_name : str
        Name of the variable to analyze
    config : dict
        Configuration dictionary with visualization settings
        
    Returns:
    --------
    plotly.graph_objects.Figure
        Plotly figure showing demographic contributions
    """
    # Load config if not provided
    if config is None:
        config = load_config()
    
    # Extract visualization settings
    vis_config = config.get("visualization", {})
    color_scheme = vis_config.get("color_scheme", "RdBu")
    
    # Identify variable type
    var_type = None
    if "total_employed_bs" in summary_df.columns:
        var_type = "employment"
    elif "total_impact_bs" in summary_df.columns:
        var_type = "per_capita"
    elif "total_affected_bs" in summary_df.columns:
        var_type = "prevalence"
    
    # Extract the contribution data
    contribution_col = variable_name + "_contribution"
    diff_col = variable_name + "_diff"
    abs_diff_col = variable_name + "_absolute_diff" if var_type == "prevalence" else None
    total_diff_col = variable_name + "_total_diff" if var_type == "per_capita" else None
    
    # Calculate contribution by age-sex groups
    if var_type == "employment":
        group_col = contribution_col
    elif var_type == "prevalence":
        group_col = abs_diff_col
    elif var_type == "per_capita":
        group_col = total_diff_col
    else:
        group_col = diff_col
      # Calculate demographic contributions
    contribution_data = detailed_df.groupby(['age', 'sex']).apply(
        lambda x: pd.Series({
            'contribution': x[group_col].sum(),
            'abs_contribution': abs(x[group_col].sum()),
            'population': x['population'].sum()
        })
    ).reset_index()
    
    # Calculate % contribution based on the sum of absolute contributions
    total_abs_contribution = contribution_data['abs_contribution'].sum()
    if total_abs_contribution > 0:
        contribution_data['contribution_pct'] = contribution_data['abs_contribution'] / total_abs_contribution * 100
    else:
        contribution_data['contribution_pct'] = 0
    
    # Sort by absolute contribution
    contribution_data = contribution_data.sort_values('abs_contribution', ascending=False)
    
    # Create a column for the demographic group label
    contribution_data['group'] = contribution_data.apply(lambda row: f"{row['age']} {row['sex']}", axis=1)
    
    # Create the visualization - horizontal bar chart of contributions
    fig = px.bar(
        contribution_data,
        y='group',
        x='contribution',
        color='contribution',
        color_continuous_scale=color_scheme,
        title=f'Demographic Contributions to Change in {variable_name.replace("_", " ").title()}',
        labels={'contribution': 'Contribution to Change', 'group': 'Demographic Group'},
        text=contribution_data['contribution'].apply(lambda x: f"{x:.2f}"),
        hover_data={
            'population': True,
            'contribution_pct': ':.1f%'
        }
    )
    
    fig.update_layout(
        font=dict(size=14),
        hoverlabel=dict(font_size=14),
        height=700,
        yaxis={'categoryorder': 'total ascending'}
    )
    
    return fig

def create_demographic_impact_heatmap(detailed_df, variable_name, metric_col, config=None):
    """
    Create a heatmap showing the impact of a variable across demographic groups.
    
    Parameters:
    -----------
    detailed_df : pandas.DataFrame
        DataFrame containing detailed results for the variable
    variable_name : str
        Name of the variable to analyze
    metric_col : str
        Column name containing the metric to visualize
    config : dict
        Configuration dictionary with visualization settings
        
    Returns:
    --------
    plotly.graph_objects.Figure
        Plotly figure showing demographic impact heatmap
    """
    # Load config if not provided
    if config is None:
        config = load_config()
    
    # Extract visualization settings
    vis_config = config.get("visualization", {})
    color_scheme = vis_config.get("color_scheme", "RdBu")
    
    # Create pivot table for the heatmap
    pivot_data = detailed_df.pivot_table(
        values=metric_col,
        index='age',
        columns='sex',
        aggfunc='sum'
    )
    
    # Create the heatmap
    fig = px.imshow(
        pivot_data,
        color_continuous_scale=color_scheme,
        title=f'{variable_name.replace("_", " ").title()} Impact by Demographic Group',
        labels={
            'sex': 'Sex',
            'age': 'Age Group',
            'value': variable_name.replace("_", " ").title() + ' Impact'
        },
        text_auto='.2f'
    )
    
    fig.update_layout(
        font=dict(size=14),
        hoverlabel=dict(font_size=14),
        height=600,
        xaxis_title="Sex",
        yaxis_title="Age Group"
    )
    
    return fig
