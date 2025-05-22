"""
Multivariate Analysis module for the demographic simulation.
This module provides functions to analyze relationships between variables
in the simulation results.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import scipy.stats as stats


def prepare_multivariate_data(detailed_file, baseline_suffix='_bs', alternative_suffix='_as'):
    """
    Prepare data for multivariate analysis from the detailed results.
    
    Parameters:
    -----------
    detailed_file : str
        Path to the detailed results Excel file
    baseline_suffix : str
        Suffix for baseline columns
    alternative_suffix : str
        Suffix for alternative scenario columns
        
    Returns:
    --------
    tuple
        (baseline_df, alternative_df, demo_df) containing the prepared data
    """
    print(f"Loading detailed results from {detailed_file}...")
    
    # Get the sheet names from the Excel file
    excel_file = pd.ExcelFile(detailed_file)
    sheet_names = excel_file.sheet_names
    
    # Skip the Summary sheet
    variable_sheets = [sheet for sheet in sheet_names if sheet != 'Summary']
    
    if not variable_sheets:
        raise ValueError("No variable sheets found in the detailed results file")
    
    # Create empty dictionaries to store baseline and alternative values
    baseline_data = {}
    alternative_data = {}
    
    # Demographic data (only need to get this once)
    demo_df = None
    
    # Process each variable sheet
    for sheet in variable_sheets:
        # Read the sheet
        df = pd.read_excel(detailed_file, sheet_name=sheet)
        
        # Get the variable name from the sheet name
        var_name = sheet
        
        # Extract baseline and alternative values
        if f"{var_name}{baseline_suffix}" in df.columns and f"{var_name}{alternative_suffix}" in df.columns:
            baseline_data[var_name] = df[f"{var_name}{baseline_suffix}"].values
            alternative_data[var_name] = df[f"{var_name}{alternative_suffix}"].values
            
            # Store demographic data if not already done
            if demo_df is None:
                demo_cols = ['year', 'age', 'sex', 'population']
                demo_df = df[demo_cols].copy()
    
    # Convert to DataFrames
    baseline_df = pd.DataFrame(baseline_data)
    alternative_df = pd.DataFrame(alternative_data)
    
    # Add demographic data to both DataFrames
    baseline_df = pd.concat([demo_df.reset_index(drop=True), baseline_df.reset_index(drop=True)], axis=1)
    alternative_df = pd.concat([demo_df.reset_index(drop=True), alternative_df.reset_index(drop=True)], axis=1)
    
    print(f"Prepared data for {len(baseline_data)} variables")
    return baseline_df, alternative_df, demo_df


def correlation_analysis(baseline_df, alternative_df, output_folder='plots/multivariate',
                         demographic_filter=None):
    """
    Perform correlation analysis on the variables.
    
    Parameters:
    -----------
    baseline_df : pandas.DataFrame
        DataFrame containing baseline values
    alternative_df : pandas.DataFrame
        DataFrame containing alternative scenario values
    output_folder : str
        Folder to save the visualizations
    demographic_filter : dict
        Dictionary with demographic filters (e.g., {'sex': 'M', 'age': '20-24'})
    """
    # Ensure output folder exists
    os.makedirs(output_folder, exist_ok=True)
    
    # Apply demographic filter if provided
    if demographic_filter:
        for key, value in demographic_filter.items():
            if key in baseline_df.columns:
                baseline_df = baseline_df[baseline_df[key] == value]
                alternative_df = alternative_df[alternative_df[key] == value]
        
        filter_str = '_'.join(f"{k}_{v}" for k, v in demographic_filter.items())
        filter_display = ', '.join(f"{k}={v}" for k, v in demographic_filter.items())
    else:
        filter_str = 'all'
        filter_display = 'All Demographics'
    
    # Exclude demographic columns for correlation analysis
    demo_cols = ['year', 'age', 'sex', 'population']
    baseline_corr = baseline_df.drop(columns=demo_cols).corr()
    alternative_corr = alternative_df.drop(columns=demo_cols).corr()
    
    # Plot baseline correlation matrix
    plt.figure(figsize=(14, 12))
    sns.heatmap(baseline_corr, annot=True, cmap='coolwarm', fmt='.2f', 
                linewidths=0.5, vmin=-1, vmax=1)
    plt.title(f'Baseline Correlation Matrix ({filter_display})', fontsize=16)
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, f'baseline_correlation_{filter_str}.png'))
    plt.close()
    
    # Plot alternative correlation matrix
    plt.figure(figsize=(14, 12))
    sns.heatmap(alternative_corr, annot=True, cmap='coolwarm', fmt='.2f', 
                linewidths=0.5, vmin=-1, vmax=1)
    plt.title(f'Alternative Scenario Correlation Matrix ({filter_display})', fontsize=16)
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, f'alternative_correlation_{filter_str}.png'))
    plt.close()
    
    # Plot correlation difference (alternative - baseline)
    diff_corr = alternative_corr - baseline_corr
    plt.figure(figsize=(14, 12))
    sns.heatmap(diff_corr, annot=True, cmap='RdBu_r', fmt='.2f', 
                linewidths=0.5, center=0, vmin=-0.5, vmax=0.5)
    plt.title(f'Change in Correlation Matrix (Alternative - Baseline) ({filter_display})', fontsize=16)
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, f'correlation_change_{filter_str}.png'))
    plt.close()
    
    # Save correlation matrices to Excel
    with pd.ExcelWriter(os.path.join(output_folder, f'correlation_matrices_{filter_str}.xlsx')) as writer:
        baseline_corr.to_excel(writer, sheet_name='Baseline')
        alternative_corr.to_excel(writer, sheet_name='Alternative')
        diff_corr.to_excel(writer, sheet_name='Difference')
    
    return baseline_corr, alternative_corr, diff_corr


def pca_analysis(baseline_df, alternative_df, output_folder='plots/multivariate'):
    """
    Perform Principal Component Analysis (PCA) on the variables.
    
    Parameters:
    -----------
    baseline_df : pandas.DataFrame
        DataFrame containing baseline values
    alternative_df : pandas.DataFrame
        DataFrame containing alternative scenario values
    output_folder : str
        Folder to save the visualizations
    """
    # Ensure output folder exists
    os.makedirs(output_folder, exist_ok=True)
    
    # Exclude demographic columns for PCA
    demo_cols = ['year', 'age', 'sex', 'population']
    baseline_vars = baseline_df.drop(columns=demo_cols)
    alternative_vars = alternative_df.drop(columns=demo_cols)
    
    # Handle missing values (replace with mean)
    baseline_vars = baseline_vars.fillna(baseline_vars.mean())
    alternative_vars = alternative_vars.fillna(alternative_vars.mean())
    
    # Scale the data
    scaler = StandardScaler()
    baseline_scaled = scaler.fit_transform(baseline_vars)
    alternative_scaled = scaler.transform(alternative_vars)  # Use the same scaling
    
    # Perform PCA
    pca = PCA()
    baseline_pca = pca.fit_transform(baseline_scaled)
    # Apply the same transformation to alternative scenario
    alternative_pca = pca.transform(alternative_scaled)
    
    # Get the explained variance ratios
    explained_variance = pca.explained_variance_ratio_
    
    # Plot explained variance
    plt.figure(figsize=(12, 8))
    plt.bar(range(1, len(explained_variance) + 1), explained_variance, alpha=0.7)
    plt.step(range(1, len(explained_variance) + 1), np.cumsum(explained_variance), where='mid', color='red')
    plt.axhline(y=0.8, color='k', linestyle='--', alpha=0.3)
    plt.title('Explained Variance by Principal Components', fontsize=16)
    plt.xlabel('Principal Component', fontsize=14)
    plt.ylabel('Explained Variance Ratio', fontsize=14)
    plt.savefig(os.path.join(output_folder, 'pca_explained_variance.png'))
    plt.close()
    
    # Plot PCA components (first two)
    plt.figure(figsize=(14, 10))
    
    # Plot baseline points
    plt.scatter(baseline_pca[:, 0], baseline_pca[:, 1], 
               alpha=0.5, label='Baseline', color='blue')
    
    # Plot alternative points
    plt.scatter(alternative_pca[:, 0], alternative_pca[:, 1], 
               alpha=0.5, label='Alternative', color='red')
    
    # Add connecting lines between corresponding points
    for i in range(len(baseline_pca)):
        plt.plot([baseline_pca[i, 0], alternative_pca[i, 0]], 
                [baseline_pca[i, 1], alternative_pca[i, 1]], 
                'k-', alpha=0.1)
    
    # Add labels and formatting
    plt.title('Principal Component Analysis: PC1 vs PC2', fontsize=16)
    plt.xlabel(f'Principal Component 1 ({explained_variance[0]:.2%} variance)', fontsize=14)
    plt.ylabel(f'Principal Component 2 ({explained_variance[1]:.2%} variance)', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=12)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, 'pca_components.png'))
    plt.close()
    
    # PCA loading plot
    plt.figure(figsize=(14, 12))
    feature_names = baseline_vars.columns
    
    # Create a DataFrame with loadings
    loadings = pd.DataFrame(
        pca.components_.T,
        columns=[f'PC{i+1}' for i in range(pca.n_components_)],
        index=feature_names
    )
    
    # Plot loadings for first two principal components
    plt.figure(figsize=(12, 10))
    
    # Plot the loading vectors
    for i, feature in enumerate(feature_names):
        plt.arrow(0, 0, pca.components_[0, i]*max(pca.explained_variance_ratio_), 
                 pca.components_[1, i]*max(pca.explained_variance_ratio_),
                 head_width=0.01, head_length=0.02, color='purple')
        plt.text(pca.components_[0, i]*max(pca.explained_variance_ratio_)*1.15, 
                pca.components_[1, i]*max(pca.explained_variance_ratio_)*1.15, 
                feature, fontsize=12)
    
    plt.xlim(-0.5, 0.5)
    plt.ylim(-0.5, 0.5)
    plt.grid(True)
    plt.axvline(x=0, color='grey', linestyle='--')
    plt.axhline(y=0, color='grey', linestyle='--')
    
    plt.title('PCA Loading Plot', fontsize=16)
    plt.xlabel(f'Principal Component 1 ({explained_variance[0]:.2%} variance)', fontsize=14)
    plt.ylabel(f'Principal Component 2 ({explained_variance[1]:.2%} variance)', fontsize=14)
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, 'pca_loadings.png'))
    plt.close()
    
    # Save PCA results to Excel
    pca_results = {
        'feature': feature_names,
        'loading_pc1': pca.components_[0, :],
        'loading_pc2': pca.components_[1, :],
    }
    pd.DataFrame(pca_results).to_excel(os.path.join(output_folder, 'pca_loadings.xlsx'), index=False)
    
    return pca, baseline_pca, alternative_pca


def run_multivariate_analysis(detailed_file='DetailedOutput.xlsx', 
                             output_folder='plots/multivariate',
                             demographic_filters=None):
    """
    Run the complete multivariate analysis workflow.
    
    Parameters:
    -----------
    detailed_file : str
        Path to the detailed results Excel file
    output_folder : str
        Folder to save the visualizations
    demographic_filters : list
        List of dictionaries with demographic filters
    """
    print(f"Running multivariate analysis on {detailed_file}...")
    
    # Prepare data
    baseline_df, alternative_df, demo_df = prepare_multivariate_data(detailed_file)
    
    # Ensure output folder exists
    os.makedirs(output_folder, exist_ok=True)
    
    # Run correlation analysis for each demographic filter
    print("Performing correlation analysis...")
    if demographic_filters:
        for filter_dict in demographic_filters:
            print(f"  Analyzing with filter: {filter_dict}")
            correlation_analysis(baseline_df, alternative_df, output_folder, filter_dict)
    else:
        # Run with no filter (all data)
        correlation_analysis(baseline_df, alternative_df, output_folder)
    
    # Run PCA analysis
    print("Performing principal component analysis...")
    pca_analysis(baseline_df, alternative_df, output_folder)
    
    print(f"Multivariate analysis complete. Results saved to {output_folder}")


if __name__ == "__main__":
    # Example usage
    run_multivariate_analysis(
        detailed_file='DetailedOutput.xlsx',
        output_folder='plots/multivariate',
        demographic_filters=[
            {'sex': 'M'},  # Male only
            {'sex': 'K'},  # Female only
            {'age': '20-24'},  # Specific age group
        ]
    )
