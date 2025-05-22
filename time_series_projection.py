"""
Time Series Projection module for the demographic simulation.
This module provides functions to project simulation results into the future
and visualize the resulting time series.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from scipy.interpolate import interp1d
from matplotlib.ticker import FuncFormatter


def project_time_series(summary_df, years_ahead=30, growth_patterns=None):
    """
    Project the simulation results into the future.
    
    Parameters:
    -----------
    summary_df : pandas.DataFrame
        DataFrame containing the simulation results
    years_ahead : int
        Number of years to project into the future
    growth_patterns : dict
        A dictionary mapping variable names to annual growth rates or growth functions
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with time series projections
    """
    if growth_patterns is None:
        growth_patterns = {}
    
    # Create years range (base year is 0)
    years = list(range(years_ahead + 1))
    
    # Initialize results dictionary with years
    results = {'year': years}
    
    # For each variable in the summary
    for _, row in summary_df.iterrows():
        var = row['variable']
        baseline = row['result_bs']
        alternative = row['result_as']
        
        # Get growth pattern for this variable (default: linear interpolation)
        if var in growth_patterns:
            growth = growth_patterns[var]
            if callable(growth):
                # If a function is provided, use it
                baseline_series = [growth(baseline, year, 'baseline') for year in years]
                alternative_series = [growth(alternative, year, 'alternative') for year in years]
            else:
                # If a scalar growth rate is provided
                baseline_series = [baseline * (1 + growth)**year for year in years]
                alternative_series = [alternative * (1 + growth)**year for year in years]
        else:
            # Default: simple linear interpolation between baseline and 
            # a value 20% higher/lower after years_ahead
            # This is just a placeholder and should be replaced with actual projection logic
            if baseline > 0:
                baseline_end = baseline * 1.2
            else:
                baseline_end = baseline * 0.8
                
            if alternative > 0:
                alternative_end = alternative * 1.2
            else:
                alternative_end = alternative * 0.8
                
            baseline_series = np.linspace(baseline, baseline_end, years_ahead + 1)
            alternative_series = np.linspace(alternative, alternative_end, years_ahead + 1)
        
        # Add to results
        results[f"{var}_baseline"] = baseline_series
        results[f"{var}_alternative"] = alternative_series
        
    # Convert to DataFrame
    return pd.DataFrame(results)


def visualize_projections(projections_df, output_folder='plots/projections', 
                          variables=None, highlight_years=None):
    """
    Create visualizations for the time series projections.
    
    Parameters:
    -----------
    projections_df : pandas.DataFrame
        DataFrame containing the time series projections
    output_folder : str
        Folder to save the visualizations
    variables : list
        List of variables to visualize (if None, all variables will be visualized)
    highlight_years : list
        List of years to highlight on the charts
    """
    # Ensure output folder exists
    os.makedirs(output_folder, exist_ok=True)
    
    # Set style
    sns.set(style="whitegrid")
    plt.rcParams['figure.figsize'] = (12, 8)
    plt.rcParams['font.size'] = 12
    
    # Get years
    years = projections_df['year'].values
    
    # If variables not specified, get all variables
    if variables is None:
        # Extract all variable names by removing _baseline and _alternative suffixes
        all_cols = projections_df.columns.tolist()
        var_cols = [col for col in all_cols if '_baseline' in col]
        variables = [col.split('_baseline')[0] for col in var_cols]
    
    # Create a separate plot for each variable
    for var in variables:
        plt.figure(figsize=(14, 8))
        
        baseline_col = f"{var}_baseline"
        alternative_col = f"{var}_alternative"
        
        # Skip if variable not in dataframe
        if baseline_col not in projections_df.columns or alternative_col not in projections_df.columns:
            print(f"Variable {var} not found in projections dataframe")
            continue
        
        # Create line plots
        plt.plot(years, projections_df[baseline_col], 'b-', linewidth=2, label='Baseline Projection')
        plt.plot(years, projections_df[alternative_col], 'r-', linewidth=2, label='Alternative Projection')
        
        # Add shaded area between curves to highlight the difference
        plt.fill_between(years, 
                         projections_df[baseline_col], 
                         projections_df[alternative_col], 
                         color='gray', alpha=0.2)
        
        # Highlight specific years if requested
        if highlight_years:
            for year in highlight_years:
                if year in years:
                    year_idx = years.tolist().index(year)
                    baseline_val = projections_df[baseline_col].iloc[year_idx]
                    alternative_val = projections_df[alternative_col].iloc[year_idx]
                    
                    # Draw vertical line at highlighted year
                    plt.axvline(x=year, color='gray', linestyle='--')
                    
                    # Add markers at the values
                    plt.plot(year, baseline_val, 'bo', markersize=8)
                    plt.plot(year, alternative_val, 'ro', markersize=8)
                    
                    # Add text labels with values
                    plt.text(year, baseline_val, f' {baseline_val:.4f}', 
                             verticalalignment='bottom')
                    plt.text(year, alternative_val, f' {alternative_val:.4f}', 
                             verticalalignment='top')
        
        # Add chart elements
        plt.title(f'Projected Trends for {var} (Next {len(years)-1} Years)', fontsize=16)
        plt.xlabel('Years from Present', fontsize=14)
        plt.ylabel('Value', fontsize=14)
        plt.grid(True, alpha=0.3)
        plt.legend()
        
        # Add annotations
        plt.annotate('Projection based on simulation results', 
                    xy=(0.5, -0.15), 
                    xycoords='axes fraction', 
                    ha='center', 
                    fontsize=10,
                    color='gray')
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_folder, f'{var}_projection.png'))
        plt.close()
    
    # Create a summary chart with relative changes over time
    plt.figure(figsize=(14, 10))
    
    # Calculate percentage differences for all variables
    for i, var in enumerate(variables):
        baseline_col = f"{var}_baseline"
        alternative_col = f"{var}_alternative"
        
        if baseline_col in projections_df.columns and alternative_col in projections_df.columns:
            # Calculate percentage difference
            pct_diff = ((projections_df[alternative_col] - projections_df[baseline_col]) / 
                         projections_df[baseline_col] * 100)
            
            plt.plot(years, pct_diff, linewidth=2, label=var)
    
    plt.title('Projected Relative Changes Over Time (All Variables)', fontsize=16)
    plt.xlabel('Years from Present', fontsize=14)
    plt.ylabel('Relative Difference (%)', fontsize=14)
    plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    plt.grid(True, alpha=0.3)
    plt.legend(loc='best')
    
    # Format y-axis as percentage
    plt.gca().yaxis.set_major_formatter(FuncFormatter(lambda x, _: f'{x:.1f}%'))
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, 'all_variables_relative_change.png'))
    plt.close()
    
    print(f"Projection visualizations saved to {output_folder}")


def run_time_series_analysis(summary_file='Output.xlsx', output_folder='plots/projections',
                            years_ahead=30, variables=None, growth_patterns=None, highlight_years=None):
    """
    Run the complete time series analysis workflow.
    
    Parameters:
    -----------
    summary_file : str
        Path to the summary Excel file
    output_folder : str
        Folder to save the visualizations
    years_ahead : int
        Number of years to project into the future
    variables : list
        List of variables to visualize (if None, all variables will be visualized)
    growth_patterns : dict
        A dictionary mapping variable names to annual growth rates or growth functions
    highlight_years : list
        List of years to highlight on the charts
    """
    print(f"Running time series projection for {years_ahead} years ahead...")
    
    # Load summary results
    summary_df = pd.read_excel(summary_file)
    
    # Generate projections
    projections_df = project_time_series(summary_df, years_ahead, growth_patterns)
    
    # Create visualizations
    visualize_projections(projections_df, output_folder, variables, highlight_years)
    
    # Save projections to Excel
    projections_file = os.path.join(output_folder, 'projections.xlsx')
    projections_df.to_excel(projections_file, index=False)
    print(f"Projections saved to {projections_file}")
    
    return projections_df


if __name__ == "__main__":
    # Example usage
    run_time_series_analysis(
        summary_file='Output.xlsx',
        output_folder='plots/projections',
        years_ahead=30,
        highlight_years=[5, 10, 20, 30]
    )
