"""
Visualization script for simulation results.
This script creates various charts and visualizations of the simulation results.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys
import json
import argparse
from matplotlib.ticker import FuncFormatter
import datetime

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
                    "plot_format": "png",
                    "color_scheme": "RdBu_r"
                }
            }
    except Exception as e:
        print(f"Error loading configuration: {str(e)}. Using default settings.")
        return {
            "visualization": {
                "output_folder": "plots",
                "create_summary_plots": True,
                "create_detailed_plots": True,
                "plot_format": "png",
                "color_scheme": "RdBu_r"
            }
        }

def format_percentage(x, pos):
    """Format as percentage for chart display"""
    return f'{x:.1f}%'

def format_large_number(x, pos):
    """Format large numbers with K, M, B suffixes"""
    if abs(x) >= 1e9:
        return f'{x*1e-9:.1f}B'
    elif abs(x) >= 1e6:
        return f'{x*1e-6:.1f}M'
    elif abs(x) >= 1e3:
        return f'{x*1e-3:.1f}K'
    else:
        return f'{x:.1f}'

def visualize_summary(summary_df, config=None):
    """
    Create visualizations for the summary results.
    
    Parameters:
    -----------
    summary_df : pandas.DataFrame
        DataFrame containing the summary results
    config : dict
        Configuration dictionary with visualization settings
    """
    # Load config if not provided
    if config is None:
        config = load_config()
    
    # Extract visualization settings
    vis_config = config.get("visualization", {})
    output_folder = vis_config.get("output_folder", "plots")
    plot_format = vis_config.get("plot_format", "png")
    color_scheme = vis_config.get("color_scheme", "RdBu_r")
    
    print(f"Creating summary visualizations in folder: {output_folder}")
    
    # Ensure output folder exists
    os.makedirs(output_folder, exist_ok=True)
    print(f"Created output folder: {output_folder}")
    
    # Set style
    sns.set(style="whitegrid")
    plt.rcParams['figure.figsize'] = (12, 8)
    plt.rcParams['font.size'] = 12
    
    # 1. Bar chart of relative changes
    plt.figure(figsize=(14, 10))
    # Sort by relative change magnitude for better visualization
    sorted_df = summary_df.sort_values('relative_change_pct')
    
    # Plot bars
    ax = sns.barplot(x='relative_change_pct', y='variable', data=sorted_df, 
                    palette=sns.color_palette("RdBu_r", n_colors=len(sorted_df)))
    
    # Add formatting
    plt.axvline(x=0, color='black', linestyle='-', alpha=0.7)
    plt.title('Relative Change (%) in Variables Due to Scenario Change', fontsize=16)
    plt.xlabel('Relative Change (%)', fontsize=14)
    plt.ylabel('Variable', fontsize=14)
    
    # Format x-axis as percentage
    ax.xaxis.set_major_formatter(FuncFormatter(format_percentage))
    
    # Add value labels
    for i, v in enumerate(sorted_df['relative_change_pct']):
        if not np.isnan(v):
            ax.text(v + (0.5 if v < 0 else -0.5), i, f"{v:.2f}%", 
                   color='black', va='center', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, 'relative_changes.png'))
    plt.close()
    
    # 2. Before and After comparison
    plt.figure(figsize=(14, 10))
    
    # Create a DataFrame for plotting
    plot_df = summary_df.copy()
    # Determine variables with large values
    max_val = plot_df[['result_bs', 'result_as']].max().max()
    
    # If we have very different scales, create separate plots
    if max_val > 100:
        # Split into large and small value variables
        large_vals = plot_df[(plot_df['result_bs'] > 100) | (plot_df['result_as'] > 100)]
        small_vals = plot_df[(plot_df['result_bs'] <= 100) & (plot_df['result_as'] <= 100)]
        
        if not large_vals.empty:
            plt.figure(figsize=(14, 10))
            large_vals = large_vals.sort_values('result_bs', ascending=False)
            
            # Prepare data for grouped bar chart
            variables = large_vals['variable']
            baseline = large_vals['result_bs']
            alternative = large_vals['result_as']
            
            x = np.arange(len(variables))
            width = 0.35
            
            fig, ax = plt.subplots(figsize=(14, 10))
            rects1 = ax.bar(x - width/2, baseline, width, label='Baseline')
            rects2 = ax.bar(x + width/2, alternative, width, label='Alternative')
            
            # Add formatting
            ax.set_ylabel('Value', fontsize=14)
            ax.set_title('Comparison of Baseline and Alternative Scenarios (Large Values)', fontsize=16)
            ax.set_xticks(x)
            ax.set_xticklabels(variables, rotation=45, ha='right')
            ax.legend()
            ax.yaxis.set_major_formatter(FuncFormatter(format_large_number))
            
            # Add value labels
            for rect in rects1:
                height = rect.get_height()
                ax.annotate(f'{height:.1f}',
                            xy=(rect.get_x() + rect.get_width()/2, height),
                            xytext=(0, 3),
                            textcoords="offset points",
                            ha='center', va='bottom')
            
            for rect in rects2:
                height = rect.get_height()
                ax.annotate(f'{height:.1f}',
                            xy=(rect.get_x() + rect.get_width()/2, height),
                            xytext=(0, 3),
                            textcoords="offset points",
                            ha='center', va='bottom')
            
            fig.tight_layout()
            plt.savefig(os.path.join(output_folder, 'before_after_large.png'))
            plt.close()
        
        if not small_vals.empty:
            plt.figure(figsize=(14, 10))
            small_vals = small_vals.sort_values('result_bs', ascending=False)
            
            # Prepare data for grouped bar chart
            variables = small_vals['variable']
            baseline = small_vals['result_bs']
            alternative = small_vals['result_as']
            
            x = np.arange(len(variables))
            width = 0.35
            
            fig, ax = plt.subplots(figsize=(14, 10))
            rects1 = ax.bar(x - width/2, baseline, width, label='Baseline')
            rects2 = ax.bar(x + width/2, alternative, width, label='Alternative')
            
            # Add formatting
            ax.set_ylabel('Value', fontsize=14)
            ax.set_title('Comparison of Baseline and Alternative Scenarios (Small Values)', fontsize=16)
            ax.set_xticks(x)
            ax.set_xticklabels(variables, rotation=45, ha='right')
            ax.legend()
            
            # Add value labels
            for rect in rects1:
                height = rect.get_height()
                ax.annotate(f'{height:.4f}',
                            xy=(rect.get_x() + rect.get_width()/2, height),
                            xytext=(0, 3),
                            textcoords="offset points",
                            ha='center', va='bottom')
            
            for rect in rects2:
                height = rect.get_height()
                ax.annotate(f'{height:.4f}',
                            xy=(rect.get_x() + rect.get_width()/2, height),
                            xytext=(0, 3),
                            textcoords="offset points",
                            ha='center', va='bottom')
            
            fig.tight_layout()
            plt.savefig(os.path.join(output_folder, 'before_after_small.png'))
            plt.close()
    else:
        # If all values are on a similar scale, create a single chart
        plot_df = plot_df.sort_values('result_bs', ascending=False)
        
        # Prepare data for grouped bar chart
        variables = plot_df['variable']
        baseline = plot_df['result_bs']
        alternative = plot_df['result_as']
        
        x = np.arange(len(variables))
        width = 0.35
        
        fig, ax = plt.subplots(figsize=(14, 10))
        rects1 = ax.bar(x - width/2, baseline, width, label='Baseline')
        rects2 = ax.bar(x + width/2, alternative, width, label='Alternative')
        
        # Add formatting
        ax.set_ylabel('Value', fontsize=14)
        ax.set_title('Comparison of Baseline and Alternative Scenarios', fontsize=16)
        ax.set_xticks(x)
        ax.set_xticklabels(variables, rotation=45, ha='right')
        ax.legend()
        
        # Add value labels
        for rect in rects1:
            height = rect.get_height()
            ax.annotate(f'{height:.4f}',
                        xy=(rect.get_x() + rect.get_width()/2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom')
        
        for rect in rects2:
            height = rect.get_height()
            ax.annotate(f'{height:.4f}',
                        xy=(rect.get_x() + rect.get_width()/2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom')
        
        fig.tight_layout()
        plt.savefig(os.path.join(output_folder, 'before_after.png'))
        plt.close()
    
    # 3. Absolute change chart
    plt.figure(figsize=(14, 10))
    # Sort by absolute change magnitude
    sorted_abs_df = summary_df.sort_values('absolute_change')
    
    # Plot bars
    ax = sns.barplot(x='absolute_change', y='variable', data=sorted_abs_df,
                    palette=sns.color_palette("RdBu_r", n_colors=len(sorted_abs_df)))
    
    # Add formatting
    plt.axvline(x=0, color='black', linestyle='-', alpha=0.7)
    plt.title('Absolute Change in Variables Due to Scenario Change', fontsize=16)
    plt.xlabel('Absolute Change', fontsize=14)
    plt.ylabel('Variable', fontsize=14)
    
    # Add value labels with appropriate formatting
    for i, v in enumerate(sorted_abs_df['absolute_change']):
        if not np.isnan(v):
            sign = "" if v < 0 else "+"
            if abs(v) >= 1000:
                ax.text(v + (5 if v < 0 else -5), i, f"{sign}{v:.2f}", 
                       color='black', va='center', fontweight='bold')
            else:
                ax.text(v + (0.01 if v < 0 else -0.01), i, f"{sign}{v:.4f}", 
                       color='black', va='center', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, 'absolute_changes.png'))
    plt.close()
    
    print(f"Visualizations saved to {output_folder} folder")

def visualize_detailed(detailed_df, var_name, output_folder='plots'):
    """
    Create detailed visualizations for a specific variable.
    
    Parameters:
    -----------
    detailed_df : pandas.DataFrame
        DataFrame containing the detailed results
    var_name : str
        Name of the variable to visualize
    output_folder : str
        Folder to save the visualizations
    """
    # Ensure output folder exists
    os.makedirs(output_folder, exist_ok=True)
    
    # Set style
    sns.set(style="whitegrid")
    plt.rcParams['figure.figsize'] = (12, 8)
    plt.rcParams['font.size'] = 12
    
    # Check if the variable exists in the dataframe
    if var_name not in detailed_df.columns:
        print(f"Variable {var_name} not found in detailed results")
        return
    
    # Get all columns related to this variable
    var_cols = [col for col in detailed_df.columns if var_name in col or col in ['age', 'sex', 'population']]
    subset_df = detailed_df[var_cols].copy()
    
    # 1. Demographic distribution (by age and sex)
    plt.figure(figsize=(14, 10))
    
    # Create pivot table for age and sex
    pivot_df = pd.pivot_table(subset_df, 
                               values=var_name + '_bs', 
                               index='age', 
                               columns='sex', 
                               aggfunc='mean')
    
    # Plot heatmap
    sns.heatmap(pivot_df, annot=True, cmap='viridis', fmt=".4f")
    plt.title(f'{var_name} - Baseline Value by Age and Sex', fontsize=16)
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, f'{var_name}_demographic_heatmap.png'))
    plt.close()
    
    # 2. Before vs After by Age Group
    plt.figure(figsize=(14, 10))
    
    # Aggregate by age
    age_df = subset_df.groupby('age').agg({
        var_name + '_bs': 'mean',
        var_name + '_as': 'mean'
    }).reset_index()
    
    # Reshape for plotting
    age_melted = pd.melt(age_df, 
                          id_vars=['age'], 
                          value_vars=[var_name + '_bs', var_name + '_as'],
                          var_name='scenario', 
                          value_name='value')
    
    # Replace scenario names for better labeling
    age_melted['scenario'] = age_melted['scenario'].map({
        var_name + '_bs': 'Baseline',
        var_name + '_as': 'Alternative'
    })
    
    # Plot
    sns.barplot(x='age', y='value', hue='scenario', data=age_melted)
    plt.title(f'{var_name} - Comparison by Age Group', fontsize=16)
    plt.xlabel('Age Group', fontsize=14)
    plt.ylabel('Value', fontsize=14)
    plt.xticks(rotation=45)
    plt.legend(title='Scenario')
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, f'{var_name}_age_comparison.png'))
    plt.close()
    
    # 3. Difference by age group (alternative - baseline)
    plt.figure(figsize=(14, 10))
    
    # Calculate difference
    age_df['difference'] = age_df[var_name + '_as'] - age_df[var_name + '_bs']
    age_df['difference_pct'] = (age_df['difference'] / age_df[var_name + '_bs'] * 100).replace([np.inf, -np.inf], np.nan)
    
    # Plot absolute difference
    plt.subplot(2, 1, 1)
    colors = ['red' if x < 0 else 'green' for x in age_df['difference']]
    sns.barplot(x='age', y='difference', data=age_df, palette=colors)
    plt.title(f'{var_name} - Absolute Difference by Age Group', fontsize=14)
    plt.xlabel('')
    plt.ylabel('Absolute Difference', fontsize=12)
    plt.xticks(rotation=45)
    
    # Plot percentage difference
    plt.subplot(2, 1, 2)
    colors = ['red' if x < 0 else 'green' for x in age_df['difference_pct']]
    sns.barplot(x='age', y='difference_pct', data=age_df, palette=colors)
    plt.title(f'{var_name} - Percentage Difference by Age Group', fontsize=14)
    plt.xlabel('Age Group', fontsize=12)
    plt.ylabel('Percentage Difference (%)', fontsize=12)
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, f'{var_name}_age_difference.png'))
    plt.close()
    
    print(f"Detailed visualizations for {var_name} saved to {output_folder} folder")

def main():
    """Main function to run the visualizations"""
    try:
        # Check if file exists
        if not os.path.exists('Output.xlsx'):
            print("Error: Output.xlsx not found. Run simulation2.py first.")
            return
        
        # Load summary results
        summary_df = pd.read_excel('Output.xlsx')
        print(f"Loaded summary results with {len(summary_df)} variables")
        
        # Create visualizations of summary results
        visualize_summary(summary_df)
        
        # Check if detailed results exist
        if os.path.exists('DetailedOutput.xlsx'):
            print("Detailed results found. Creating detailed visualizations...")
            
            # Load detailed results
            with pd.ExcelFile('DetailedOutput.xlsx') as xls:
                # Get all sheet names except 'Summary'
                sheets = [sheet for sheet in xls.sheet_names if sheet != 'Summary']
                
                # Get mapping of sheet names to variable names
                var_mapping = {}
                for var in summary_df['variable']:
                    # Find the matching sheet (the sheet name might be truncated)
                    matching_sheets = [s for s in sheets if s.startswith(var) or var.startswith(s)]
                    if matching_sheets:
                        var_mapping[matching_sheets[0]] = var
                
                # Process each variable sheet
                for sheet in sheets:
                    print(f"Processing detailed visualizations for sheet {sheet}...")
                    df = pd.read_excel(xls, sheet_name=sheet)
                    var_name = var_mapping.get(sheet, sheet) if var_mapping else sheet
                    visualize_detailed(df, var_name)
        
        print("All visualizations completed!")
    
    except Exception as e:
        print(f"Error during visualization: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
