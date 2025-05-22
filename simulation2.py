# Re-import libraries due to execution state reset
import pandas as pd
import numpy as np
import os
import time
import sys
import json
import argparse

def print_progress(iteration, total, prefix='', suffix='', decimals=1, bar_length=50):
    """
    Call in a loop to create a progress bar in the console.
    """
    str_format = "{0:." + str(decimals) + "f}"
    percents = str_format.format(100 * (iteration / float(total)))
    filled_length = int(round(bar_length * iteration / float(total)))
    # Use simple ASCII characters instead of Unicode for wider compatibility
    bar = '#' * filled_length + '-' * (bar_length - filled_length)
    sys.stdout.write('\r%s |%s| %s%s %s' % (prefix, bar, percents, '%', suffix))
    sys.stdout.flush()
    if iteration == total:
        sys.stdout.write('\n')

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
            print(f"Loaded configuration from {config_path}")
            return config
        else:
            print(f"Configuration file {config_path} not found. Using default settings.")
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
        print(f"Error loading configuration: {str(e)}. Using default settings.")
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

def run_simulation(config=None):
    """
    Run the simulation with error handling and progress indicators.
    
    Parameters:
    -----------
    config : dict
        Configuration dictionary
    
    Returns:
    --------
    pandas.DataFrame, pandas.DataFrame
        summary_df, df (detailed results)
    """
    # Load config if not provided
    if config is None:
        config = load_config()
    
    # Extract simulation settings
    sim_config = config.get("simulation", {})
    input_file = sim_config.get("input_file", "Input.xlsx")
    output_file = sim_config.get("output_file", "Output.xlsx")
    detailed_output_file = sim_config.get("detailed_output_file", "DetailedOutput.xlsx")
    shock_scenario = sim_config.get("shock_scenario", {"s1_change": -0.1, "s2_change": 0.1, "s3_change": 0.0})
    variables_to_exclude = sim_config.get("variables_to_exclude", [])
    
    try:
        print(f"Loading data from {input_file}...")
        # Load the Excel file with the updated structure
        parameters_df = pd.read_excel(input_file, sheet_name='parameters')
        data_df = pd.read_excel(input_file, sheet_name='data_2024')
        
        # Create a working copy of the data
        df = data_df.copy()
        
        # Identify the columns that are NOT baseline variables
        non_baseline_cols = {"year", "age", "sex", "s1", "s2", "s3", "population"}
        
        # Only use baseline variables that also exist in the parameters sheet
        parameter_vars = parameters_df['variable'].tolist()
        baseline_vars = [col for col in df.columns if col not in non_baseline_cols and col in parameter_vars]
        
        # Apply exclusions from config
        if variables_to_exclude:
            baseline_vars = [var for var in baseline_vars if var not in variables_to_exclude]
            print(f"Excluding variables: {', '.join(variables_to_exclude)}")
        
        print(f"Processing {len(baseline_vars)} baseline variables: {', '.join(baseline_vars)}")
        
        # Check if any of the required baseline variables are missing
        missing_vars = [var for var in parameters_df['variable'] if var not in df.columns]
        if missing_vars:
            raise ValueError(f"Missing baseline variables in data_2024 sheet: {missing_vars}")
        
        # Calculate working-age population (optional: could be used for weighting)
        age_groups_20_64 = [
            "20-24", "25-29", "30-34", "35-39", "40-44",
            "45-49", "50-54", "55-59", "60-64"
        ]
        
        # Create a dictionary to store all new columns, which we'll add to the dataframe at once
        new_columns = {}
        new_columns["population_20_64"] = df.apply(
            lambda row: row["population"] if row["age"] in age_groups_20_64 else 0,
            axis=1
        )
        
        # Identify age-related columns in parameters
        age_cols = [col for col in parameters_df.columns if col.startswith("age_")]
        
        print("Applying demographic ratios...")
        # Process ratios per age and sex (prepare all columns at once)
        for i, (_, row) in enumerate(parameters_df.iterrows()):
            variable = row["variable"]
            # Skip if this variable is not in our baseline_vars
            if variable not in baseline_vars:
                continue
                
            valid_ages = row[age_cols].dropna().tolist()
            col_s_n = f"{variable}_s_n"
            col_w_s = f"{variable}_w_s"
            
            # Default values
            new_columns[col_s_n] = pd.Series(1.0, index=df.index)
            new_columns[col_w_s] = pd.Series(1.0, index=df.index)
            
            # Set values for specific demographics
            men_mask = (df["sex"] == "M") & (df["age"].isin(valid_ages))
            women_mask = (df["sex"] == "K") & (df["age"].isin(valid_ages))
            
            # Update values based on masks
            new_columns[col_s_n].loc[men_mask] = row["s_n_men"]
            new_columns[col_s_n].loc[women_mask] = row["s_n_women"]
            new_columns[col_w_s].loc[men_mask] = row["w_s_men"]
            new_columns[col_w_s].loc[women_mask] = row["w_s_women"]
            
            # Show progress
            print_progress(i + 1, len(parameters_df), prefix='Progress:', suffix='Complete', bar_length=50)
        
        # Add all new columns to the dataframe at once
        print("\nAdding demographic factors to dataframe...")
        df = pd.concat([df, pd.DataFrame(new_columns)], axis=1)
        
        # Get shock values from config
        s1_change = shock_scenario.get("s1_change", -0.1)
        s2_change = shock_scenario.get("s2_change", 0.1)
        s3_change = shock_scenario.get("s3_change", 0.0)
        
        # Apply the shock scenario
        print(f"Applying shock scenario: s1 {s1_change:+.1f}, s2 {s2_change:+.1f}, s3 {s3_change:+.1f}")
        shock_columns = {
            's1_as': df['s1'] + s1_change,
            's2_as': df['s2'] + s2_change,
            's3_as': df['s3'] + s3_change
        }
        df = pd.concat([df, pd.DataFrame(shock_columns)], axis=1)
          # Store all results
        results = []
        
        print("Processing baseline variables...")
        # Process each baseline variable
        for i, var in enumerate(baseline_vars):
            # Create a dictionary of new columns for this variable
            var_columns = {}
            
            # Calculate the denominators and scenario-adjusted levels
            var_columns[var + "_denominator"] = df['s1'] + df['s2'] * df[var + "_s_n"] + df['s3'] * df[var + "_s_n"] * df[var + "_w_s"]
            var_columns[var + "_s1"] = df[var] / var_columns[var + "_denominator"]
            var_columns[var + "_s2"] = var_columns[var + "_s1"] * df[var + "_s_n"]
            var_columns[var + "_s3"] = var_columns[var + "_s2"] * df[var + "_w_s"]
        
            # Baseline and alternative scenario value for each demographic group
            var_columns[var + "_bs"] = df['s1'] * var_columns[var + "_s1"] + df['s2'] * var_columns[var + "_s2"] + df['s3'] * var_columns[var + "_s3"]
            var_columns[var + "_as"] = df['s1_as'] * var_columns[var + "_s1"] + df['s2_as'] * var_columns[var + "_s2"] + df['s3_as'] * var_columns[var + "_s3"]
            
            # Add these columns to the dataframe all at once
            df = pd.concat([df, pd.DataFrame(var_columns)], axis=1)
        
            # Store overall population-weighted averages
            try:
                result_bs = np.average(df[var + '_bs'], weights=df['population'])
                result_as = np.average(df[var + '_as'], weights=df['population'])
            except ZeroDivisionError:
                result_bs = result_as = np.nan
                print(f"Warning: Zero division error when calculating weighted average for {var}")
        
            results.append({
                "variable": var,
                "result_bs": result_bs,
                "result_as": result_as,
                "absolute_change": result_as - result_bs,
                "relative_change_pct": ((result_as - result_bs) / result_bs * 100) if result_bs != 0 else np.nan
            })
            
            # Show progress
            print_progress(i + 1, len(baseline_vars), prefix='Progress:', suffix='Complete', bar_length=50)
        
        # Convert result summary to DataFrame
        summary_df = pd.DataFrame(results)
        
        # Print summary to console
        print("\nSimulation Results Summary:")
        print(summary_df)
        
        # Save results to Excel files
        print(f"Saving summary results to {output_file}...")
        summary_df.to_excel(output_file, index=False)
        
        print(f"Saving detailed results to {detailed_output_file}...")
        # Save the entire dataframe with all calculated columns
        with pd.ExcelWriter(detailed_output_file, engine='openpyxl') as writer:
            # Save the summary results
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Save the detailed results
            # Select demographic columns and results
            demo_cols = ['year', 'age', 'sex', 'population', 's1', 's2', 's3', 's1_as', 's2_as', 's3_as']
            
            # For each variable, save a separate sheet with relevant columns
            for var in baseline_vars:
                var_cols = [col for col in df.columns if var in col and col != var] + [var]
                cols_to_save = demo_cols + var_cols
                df[cols_to_save].to_excel(writer, sheet_name=var[:30], index=False)  # Truncate sheet name if too long
        
        print("\nSimulation completed successfully!")
        return summary_df, df
        
    except Exception as e:
        print(f"\nError during simulation: {str(e)}")
        raise


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Run demographic counterfactual simulation.')
    parser.add_argument('--config', type=str, default='config.json', help='Path to config file')
    parser.add_argument('--s1', type=float, help='Shock to s1 (override config)')
    parser.add_argument('--s2', type=float, help='Shock to s2 (override config)')
    parser.add_argument('--s3', type=float, help='Shock to s3 (override config)')
    parser.add_argument('--input', type=str, help='Input file (override config)')
    parser.add_argument('--output', type=str, help='Output file (override config)')
    parser.add_argument('--detailed-output', type=str, help='Detailed output file (override config)')
    return parser.parse_args()


if __name__ == "__main__":
    start_time = time.time()
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Load configuration
    config = load_config(args.config)
    
    # Override config with command line arguments if provided
    sim_config = config.get("simulation", {})
    
    if args.s1 is not None:
        sim_config["shock_scenario"]["s1_change"] = args.s1
    if args.s2 is not None:
        sim_config["shock_scenario"]["s2_change"] = args.s2
    if args.s3 is not None:
        sim_config["shock_scenario"]["s3_change"] = args.s3
    if args.input is not None:
        sim_config["input_file"] = args.input
    if args.output is not None:
        sim_config["output_file"] = args.output
    if args.detailed_output is not None:
        sim_config["detailed_output_file"] = args.detailed_output
    
    try:
        summary_df, detailed_df = run_simulation(config)
        elapsed_time = time.time() - start_time
        print(f"Total execution time: {elapsed_time:.2f} seconds")
    except Exception as e:
        print(f"Simulation failed: {str(e)}")
        sys.exit(1)