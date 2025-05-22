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
                        "scenario_type": "Percentage Change", # Added default
                        "s1_change": -0.1,
                        "s2_change": 0.1,
                        "s3_change": 0.0,
                        "s1_reallocation_percentage": 0.5 # Added default
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
                    "scenario_type": "Percentage Change", # Added default
                    "s1_change": -0.1,
                    "s2_change": 0.1,
                    "s3_change": 0.0,
                    "s1_reallocation_percentage": 0.5 # Added default
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
    
    # Default shock_scenario if not fully present in config
    default_full_shock_scenario = {
        "scenario_type": "Percentage Change",
        "s1_change": -0.1,
        "s2_change": 0.1,
        "s3_change": 0.0,
        "s1_reallocation_percentage": 0.5  # Default 50%
    }
    shock_scenario = sim_config.get("shock_scenario", default_full_shock_scenario.copy())
    # Ensure all keys are present by merging with defaults
    for key, value in default_full_shock_scenario.items():
        shock_scenario.setdefault(key, value)
        
    variables_to_exclude = sim_config.get("variables_to_exclude", [])
    
    try:
        print(f"Loading data from {input_file}...")
        parameters_df = pd.read_excel(input_file, sheet_name='parameters')
        data_df = pd.read_excel(input_file, sheet_name='data_2024') # This is the main df for baseline

        data_2012_df = None
        if shock_scenario.get("scenario_type") == "use_2012_values":
            try:
                print("Loading data_2012 sheet for 'Use 2012 Values' scenario...")
                data_2012_df = pd.read_excel(input_file, sheet_name='data_2012')
                print(f"Successfully loaded 'data_2012' sheet. Columns: {data_2012_df.columns.tolist()}")
                print(f"data_2012_df head:\n{data_2012_df.head()}")
                required_cols_2012 = ['age', 'sex', 's1', 's2', 's3']
                if not all(col in data_2012_df.columns for col in required_cols_2012):
                    raise ValueError(f"data_2012 sheet is missing one of required columns: {required_cols_2012}")
            except FileNotFoundError:
                print(f"Error: Input file {input_file} not found when trying to load data_2012 sheet.")
                raise
            except Exception as e:
                print(f"Error loading or validating data_2012 sheet: {str(e)}")
                raise
        
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
        
        # Apply the shock scenario
        scenario_type = shock_scenario.get("scenario_type")
        print(f"Selected scenario type: {scenario_type}")

        if scenario_type == "use_2012_values":
            if data_2012_df is None:
                raise ValueError("data_2012_df not loaded, cannot proceed with 'Use 2012 Values' scenario.")
            print("Applying shock scenario: Using s1, s2, s3 values from data_2012 sheet.")
            print(f"df (data_2024) relevant columns head before merge:\n{df[['age', 'sex', 's1', 's2', 's3']].head()}")
            
            # Prepare the 2012 data with renamed columns for s-values
            data_2012_s_values_renamed = data_2012_df[['age', 'sex', 's1', 's2', 's3']].copy()
            data_2012_s_values_renamed.rename(columns={
                's1': 's1_from2012',
                's2': 's2_from2012',
                's3': 's3_from2012'
            }, inplace=True)
            # print(f"DEBUG: Renamed data_2012_s_values_renamed head:\n{data_2012_s_values_renamed.head()}")

            # Merge the prepared 2012 s-values into the main df
            # This adds s1_from2012, s2_from2012, s3_from2012 columns to df
            df = pd.merge(
                df,
                data_2012_s_values_renamed,
                on=['age', 'sex'],
                how='left'
            )
            # print(f"DEBUG: df after merge with 2012 values (should have sX_from2012 cols):\n{df[['age', 'sex', 's1', 's2', 's3', 's1_from2012', 's2_from2012', 's3_from2012']].head(7)}")

            # Check for unmatched rows from the 2012 data merge
            # This must be done on one of the sX_from2012 columns BEFORE fillna
            unmatched_count = df['s1_from2012'].isnull().sum() 
            if unmatched_count > 0:
                print(f"Warning: {unmatched_count} demographic groups in data_2024 found no s-value match in data_2012. Their s-values for the 'as' scenario will be their baseline data_2024 s-values.")

            # Assign to sX_as columns in the df.
            # If a group in 2024 data has no match in 2012 (sX_from2012 is NaN), use its original 2024 s-value.
            df['s1_as'] = df['s1_from2012'].fillna(df['s1'])
            df['s2_as'] = df['s2_from2012'].fillna(df['s2'])
            df['s3_as'] = df['s3_from2012'].fillna(df['s3'])
            
            # Drop the temporary sX_from2012 columns as they are no longer needed
            df.drop(columns=['s1_from2012', 's2_from2012', 's3_from2012'], inplace=True, errors='ignore') # errors='ignore' in case they weren't there for some reason
            
            print(f"df head after assigning sX_as from 2012 values:\n{df[['age', 'sex', 's1', 's2', 's3', 's1_as', 's2_as', 's3_as']].head()}")

        elif scenario_type == "s1_reallocated_to_s2":
            s1_reallocation_percentage = shock_scenario.get("s1_reallocation_percentage")
            print(f"Applying shock scenario: S1 reallocated to S2 by {s1_reallocation_percentage*100:.1f}%.")
            
            amount_reallocated = df['s1'] * s1_reallocation_percentage
            df['s1_as'] = df['s1'] - amount_reallocated
            df['s2_as'] = df['s2'] + amount_reallocated
            df['s3_as'] = df['s3'] # s3 is not changed by this scenario type, uses baseline s3 from data_2024
            
        else: # Default to "Percentage Change"
            s1_change = shock_scenario.get("s1_change")
            s2_change = shock_scenario.get("s2_change")
            s3_change = shock_scenario.get("s3_change")
            print(f"Applying shock scenario (Percentage Change): s1 {s1_change:+.2f}, s2 {s2_change:+.2f}, s3 {s3_change:+.2f}")
            df['s1_as'] = df['s1'] + s1_change
            df['s2_as'] = df['s2'] + s2_change
            df['s3_as'] = df['s3'] + s3_change
        
        # Ensure sX_as columns are not negative (or handle as per model's logic if they can be)
        # For now, let's assume they can be, as original sX + change could be negative.
        # If they must be non-negative:
        # df['s1_as'] = np.maximum(0, df['s1_as'])
        # df['s2_as'] = np.maximum(0, df['s2_as'])
        # df['s3_as'] = np.maximum(0, df['s3_as'])

        # The old way of creating shock_columns dictionary and concatenating is no longer needed
        # as sX_as are now directly part of the df.
        
        # Store all results
        results = []

        # --- Dynamically define variable types and friendly names ---
        rate_variables = []
        per_capita_variables = []
        prevalence_variables = []
        average_variables = []
        variable_friendly_names = {}

        if 'variable_type' in parameters_df.columns:
            print("Loading variable types from 'parameters' sheet.")
            for _, row in parameters_df.iterrows():
                var_name = row['variable']
                var_type = str(row['variable_type']).lower() if pd.notna(row['variable_type']) else ''
                
                if var_name not in baseline_vars: # Only consider variables being processed
                    continue

                if var_type == 'rate':
                    rate_variables.append(var_name)
                elif var_type == 'per_capita':
                    per_capita_variables.append(var_name)
                elif var_type == 'prevalence':
                    prevalence_variables.append(var_name)
                elif var_type == 'average':
                    average_variables.append(var_name)
                # else:
                #     print(f"Warning: Variable '{var_name}' has unknown or missing type '{row['variable_type']}' in 'parameters' sheet.")
        else:
            print("Warning: 'variable_type' column not found in 'parameters' sheet. Using hardcoded variable types.")
            # Fallback to hardcoded lists (ensure these are comprehensive or match your old defaults)
            default_rate_variables = ["employment"] 
            default_per_capita_variables = [
                "absence", "cancer", "diabetes", "hypertension", "mortality", 
                "heart_disease", "stroke", "colorectal_cancer", "breast_cancer", 
                "endometrial_cancer", "depression", "anxiety", "public_health_costs"
            ]
            default_prevalence_variables = ["body_fat_prc"]
            default_average_variables = ["earnings", "life_expectancy"]
            # Filter these lists to only include variables present in baseline_vars
            rate_variables = [v for v in default_rate_variables if v in baseline_vars]
            per_capita_variables = [v for v in default_per_capita_variables if v in baseline_vars]
            prevalence_variables = [v for v in default_prevalence_variables if v in baseline_vars]
            average_variables = [v for v in default_average_variables if v in baseline_vars]


        if 'friendly_name' in parameters_df.columns:
            print("Loading friendly names from 'parameters' sheet.")
            for _, row in parameters_df.iterrows():
                var_name = row['variable']
                if var_name not in baseline_vars: # Only consider variables being processed
                    continue
                if pd.notna(row['friendly_name']):
                    variable_friendly_names[var_name] = str(row['friendly_name'])
                else: # If friendly_name is blank in the sheet, use the variable name itself
                   variable_friendly_names[var_name] = var_name 
        else:
            print("Warning: 'friendly_name' column not found in 'parameters' sheet. Using hardcoded friendly names or variable names.")
            # Fallback to hardcoded dictionary
            default_friendly_names_map = {
                "employment": "Employment Rate", "absence": "Absence Days", "cancer": "Cancer Prevalence",
                "diabetes": "Diabetes Prevalence", "hypertension": "Hypertension Prevalence",
                "mortality": "Mortality Rate", "heart_disease": "Heart Disease Prevalence",
                "stroke": "Stroke Prevalence", "colorectal_cancer": "Colorectal Cancer Prevalence",
                "breast_cancer": "Breast Cancer Prevalence", "endometrial_cancer": "Endometrial Cancer Prevalence",
                "depression": "Depression Prevalence", "anxiety": "Anxiety Prevalence",
                "public_health_costs": "Public Health Costs", "body_fat_prc": "Body Fat Percentage",
                "earnings": "Earnings", "life_expectancy": "Life Expectancy"
            }
            for var_name in baseline_vars:
                variable_friendly_names[var_name] = default_friendly_names_map.get(var_name, var_name)
        
        # --- End of dynamic definitions ---

        # Initialize total population-level variables
        population_totals = {
            'total_population_bs': df['population'].sum(),
            'total_population_as': df['population'].sum(),  # Population is constant in this model
            'working_age_population_bs': df[df['age'].isin(age_groups_20_64)]['population'].sum(),
            'working_age_population_as': df[df['age'].isin(age_groups_20_64)]['population'].sum(),
        }
        
        print("Processing baseline variables...")
        # Process each baseline variable
        for i, var in enumerate(baseline_vars):
            # Create a dictionary of new columns for this variable
            var_columns = {}
            
            # Calculate the denominators and scenario-adjusted levels
            var_columns[var + "_denominator"] = df['s1'] + df['s2'] * df[var + "_s_n"] + df['s3'] * df[var + "_s_n"] * df[var + "_w_s"]
            var_columns[var + "_s1"] = df[var] / var_columns[var + "_denominator"]
            var_columns[var + "_s2"] = var_columns[var + "_s1"] * df[var + "_s_n"]
            var_columns[var + "_s3"] = var_columns[var + "_s2"] * df[var + "_w_s"]            # Baseline and alternative scenario value for each demographic group
            var_columns[var + "_bs"] = df['s1'] * var_columns[var + "_s1"] + df['s2'] * var_columns[var + "_s2"] + df['s3'] * var_columns[var + "_s3"]
            var_columns[var + "_as"] = df['s1_as'] * var_columns[var + "_s1"] + df['s2_as'] * var_columns[var + "_s2"] + df['s3_as'] * var_columns[var + "_s3"]
            
            # For variables representing rates, calculate absolute numbers
            if var in rate_variables or var in prevalence_variables:
                var_columns[var + "_absolute_bs"] = var_columns[var + "_bs"] * df['population']
                var_columns[var + "_absolute_as"] = var_columns[var + "_as"] * df['population']
                var_columns[var + "_absolute_diff"] = var_columns[var + "_absolute_as"] - var_columns[var + "_absolute_bs"]
            
            # For per capita variables, calculate total impact
            if var in per_capita_variables:
                var_columns[var + "_total_bs"] = var_columns[var + "_bs"] * df['population']
                var_columns[var + "_total_as"] = var_columns[var + "_as"] * df['population']
                var_columns[var + "_total_diff"] = var_columns[var + "_total_as"] - var_columns[var + "_total_bs"]
            
            # Add demographic contribution calculation (which groups contribute most to changes)
            var_columns[var + "_diff"] = var_columns[var + "_as"] - var_columns[var + "_bs"]
            var_columns[var + "_diff_pct"] = (var_columns[var + "_diff"] / var_columns[var + "_bs"]) * 100
            
            # Calculate weighted contribution to total change 
            var_columns[var + "_contribution"] = var_columns[var + "_diff"] * df['population']
            
            # Add these columns to the dataframe all at once
            df = pd.concat([df, pd.DataFrame(var_columns)], axis=1)
        
            # Store overall population-weighted averages
            try:
                result_bs = np.average(df[var + '_bs'], weights=df['population'])
                result_as = np.average(df[var + '_as'], weights=df['population'])
                
                # Additional metrics based on variable type
                result_dict = {
                    "variable": var,
                    "result_bs": result_bs,
                    "result_as": result_as,
                    "absolute_change": result_as - result_bs,
                    "relative_change_pct": ((result_as - result_bs) / result_bs * 100) if result_bs != 0 else np.nan
                }
                  # Add specialized metrics based on variable type
                if var in rate_variables:
                    # For employment: total employed population and employment breakdown
                    total_employed_bs = df[var + "_absolute_bs"].sum()
                    total_employed_as = df[var + "_absolute_as"].sum()
                    employed_change = total_employed_as - total_employed_bs
                    
                    # Calculate employment change by demographic group
                    emp_by_age = df.groupby('age')[var + '_absolute_diff'].sum().reset_index()
                    emp_by_age.columns = ['age', 'employment_change']
                    emp_by_age['contribution_pct'] = (emp_by_age['employment_change'] / abs(employed_change) * 100) if employed_change != 0 else 0
                    
                    emp_by_sex = df.groupby('sex')[var + '_absolute_diff'].sum().reset_index()
                    emp_by_sex.columns = ['sex', 'employment_change']
                    emp_by_sex['contribution_pct'] = (emp_by_sex['employment_change'] / abs(employed_change) * 100) if employed_change != 0 else 0
                    
                    # Get the top contributing age-sex groups
                    group_contributions = df.groupby(['age', 'sex'])[var + '_absolute_diff'].sum().reset_index()
                    group_contributions.columns = ['age', 'sex', 'employment_change']
                    top_groups = group_contributions.sort_values('employment_change', key=abs, ascending=False).head(5)
                    
                    result_dict.update({
                        "total_employed_bs": total_employed_bs,
                        "total_employed_as": total_employed_as,
                        "employed_change": employed_change,
                        "employed_change_pct": (employed_change / total_employed_bs * 100) if total_employed_bs != 0 else np.nan,
                        "employment_by_age": emp_by_age.to_dict('records'),
                        "employment_by_sex": emp_by_sex.to_dict('records'),
                        "top_contributing_groups": top_groups.to_dict('records')
                    })
                elif var in per_capita_variables:
                    # For absence, cancer, etc.: total impact across population
                    total_impact_bs = df[var + "_total_bs"].sum()
                    total_impact_as = df[var + "_total_as"].sum()
                    impact_change = total_impact_as - total_impact_bs
                    
                    # Calculate impact change by demographic group
                    impact_by_age = df.groupby('age')[var + '_total_diff'].sum().reset_index()
                    impact_by_age.columns = ['age', 'impact_change']
                    impact_by_age['contribution_pct'] = (impact_by_age['impact_change'] / abs(impact_change) * 100) if impact_change != 0 else 0
                    
                    impact_by_sex = df.groupby('sex')[var + '_total_diff'].sum().reset_index()
                    impact_by_sex.columns = ['sex', 'impact_change']
                    impact_by_sex['contribution_pct'] = (impact_by_sex['impact_change'] / abs(impact_change) * 100) if impact_change != 0 else 0
                    
                    # Get the top contributing age-sex groups
                    group_contributions = df.groupby(['age', 'sex'])[var + '_total_diff'].sum().reset_index()
                    group_contributions.columns = ['age', 'sex', 'impact_change']
                    top_groups = group_contributions.sort_values('impact_change', key=abs, ascending=False).head(5)
                    
                    result_dict.update({
                        "total_impact_bs": total_impact_bs,
                        "total_impact_as": total_impact_as,
                        "impact_change": impact_change,
                        "impact_change_pct": (impact_change / total_impact_bs * 100) if total_impact_bs != 0 else np.nan,
                        "impact_by_age": impact_by_age.to_dict('records'),
                        "impact_by_sex": impact_by_sex.to_dict('records'),
                        "top_contributing_groups": top_groups.to_dict('records')
                    })
                    
                    # For absence specifically, calculate working days lost
                    if var == "absence":
                        working_pop_bs = df[df['age'].isin(age_groups_20_64)]['population'].sum()
                        working_days_bs = df[df['age'].isin(age_groups_20_64)][var + "_total_bs"].sum()
                        working_days_as = df[df['age'].isin(age_groups_20_64)][var + "_total_as"].sum()
                        working_days_change = working_days_as - working_days_bs
                        
                        # Calculate per working-age person metrics
                        days_per_person_bs = working_days_bs / working_pop_bs if working_pop_bs > 0 else 0
                        days_per_person_as = working_days_as / working_pop_bs if working_pop_bs > 0 else 0
                        
                        # Calculate economic impact if available
                        daily_cost = 500  # Example daily cost of absence (could be parameterized in the future)
                        economic_impact_bs = working_days_bs * daily_cost
                        economic_impact_as = working_days_as * daily_cost
                        economic_impact_change = economic_impact_as - economic_impact_bs
                        
                        result_dict.update({
                            "working_population": working_pop_bs,
                            "total_days_lost_bs": working_days_bs,
                            "total_days_lost_as": working_days_as,
                            "days_lost_change": working_days_change,
                            "days_lost_change_pct": (working_days_change / working_days_bs * 100) if working_days_bs != 0 else np.nan,
                            "days_per_person_bs": days_per_person_bs,
                            "days_per_person_as": days_per_person_as,
                            "days_per_person_change": days_per_person_as - days_per_person_bs,
                            "estimated_economic_impact_bs": economic_impact_bs,
                            "estimated_economic_impact_as": economic_impact_as,
                            "economic_impact_change": economic_impact_change
                        })
                    
                    # For public_health_costs, calculate total costs and savings
                    if var == "public_health_costs":
                        cost_change = impact_change
                        cost_savings = abs(cost_change) if cost_change < 0 else 0
                        additional_costs = cost_change if cost_change > 0 else 0
                        
                        # Calculate per capita costs
                        total_population = df['population'].sum()
                        per_capita_costs_bs = total_impact_bs / total_population if total_population > 0 else 0
                        per_capita_costs_as = total_impact_as / total_population if total_population > 0 else 0
                        per_capita_change = per_capita_costs_as - per_capita_costs_bs
                        
                        # Calculate costs by demographic groups
                        costs_by_age = df.groupby('age')[[var + '_total_bs', var + '_total_as', var + '_total_diff']].sum().reset_index()
                        costs_by_age.columns = ['age', 'costs_bs', 'costs_as', 'cost_change']
                        
                        result_dict.update({
                            "total_costs_bs": total_impact_bs,
                            "total_costs_as": total_impact_as,
                            "cost_change": cost_change,
                            "cost_change_pct": (cost_change / total_impact_bs * 100) if total_impact_bs != 0 else np.nan,
                            "cost_savings": cost_savings,
                            "additional_costs": additional_costs,
                            "per_capita_costs_bs": per_capita_costs_bs,
                            "per_capita_costs_as": per_capita_costs_as,
                            "per_capita_cost_change": per_capita_change,
                            "costs_by_age": costs_by_age.to_dict('records')
                        })
                    
                    # For health indicators like diabetes, calculate prevalence in different ways
                    if var in ["diabetes", "hypertension", "cancer", "heart_disease", "stroke", 
                             "colorectal_cancer", "breast_cancer", "endometrial_cancer", 
                             "depression", "anxiety"]:
                        # Calculate total cases
                        total_cases_bs = total_impact_bs
                        total_cases_as = total_impact_as
                        cases_change = impact_change
                        
                        # Calculate prevalence rates
                        total_population = df['population'].sum()
                        prevalence_bs = total_cases_bs / total_population * 100 if total_population > 0 else 0
                        prevalence_as = total_cases_as / total_population * 100 if total_population > 0 else 0
                        prevalence_change = prevalence_as - prevalence_bs
                        
                        # Calculate cases by age group
                        cases_by_age = df.groupby('age')[[var + '_total_bs', var + '_total_as', var + '_total_diff']].sum().reset_index()
                        cases_by_age.columns = ['age', 'cases_bs', 'cases_as', 'cases_change']
                        
                        # Calculate prevalence by sex
                        prev_by_sex = []
                        for sex in df['sex'].unique():
                            sex_pop = df[df['sex'] == sex]['population'].sum()
                            sex_cases_bs = df[df['sex'] == sex][var + '_total_bs'].sum()
                            sex_cases_as = df[df['sex'] == sex][var + '_total_as'].sum()
                            prev_by_sex.append({
                                'sex': sex,
                                'population': sex_pop,
                                'cases_bs': sex_cases_bs,
                                'cases_as': sex_cases_as,
                                'prevalence_bs': sex_cases_bs / sex_pop * 100 if sex_pop > 0 else 0,
                                'prevalence_as': sex_cases_as / sex_pop * 100 if sex_pop > 0 else 0,
                                'prevalence_change': (sex_cases_as - sex_cases_bs) / sex_pop * 100 if sex_pop > 0 else 0
                            })
                        
                        result_dict.update({
                            "total_cases_bs": total_cases_bs,
                            "total_cases_as": total_cases_as,
                            "cases_change": cases_change,
                            "cases_change_pct": (cases_change / total_cases_bs * 100) if total_cases_bs != 0 else np.nan,
                            "prevalence_rate_bs": prevalence_bs,
                            "prevalence_rate_as": prevalence_as,
                            "prevalence_rate_change": prevalence_change,
                            "cases_by_age": cases_by_age.to_dict('records'),
                            "prevalence_by_sex": prev_by_sex
                        })
                elif var in prevalence_variables:
                    # For body_fat_prc: total affected individuals and more detailed breakdowns
                    total_affected_bs = df[var + "_absolute_bs"].sum()
                    total_affected_as = df[var + "_absolute_as"].sum()
                    affected_change = total_affected_as - total_affected_bs
                    
                    # Calculate detailed demographic breakdown
                    affected_by_age = df.groupby('age')[[var + '_absolute_bs', var + '_absolute_as', var + '_absolute_diff']].sum().reset_index()
                    affected_by_age.columns = ['age', 'affected_bs', 'affected_as', 'affected_change']
                    affected_by_age['contribution_pct'] = (affected_by_age['affected_change'] / abs(affected_change) * 100) if affected_change != 0 else 0
                    
                    affected_by_sex = df.groupby('sex')[[var + '_absolute_bs', var + '_absolute_as', var + '_absolute_diff']].sum().reset_index()
                    affected_by_sex.columns = ['sex', 'affected_bs', 'affected_as', 'affected_change']
                    affected_by_sex['contribution_pct'] = (affected_by_sex['affected_change'] / abs(affected_change) * 100) if affected_change != 0 else 0
                    
                    # Calculate prevalence rates within demographic groups
                    prev_by_age = []
                    for age in df['age'].unique():
                        age_pop = df[df['age'] == age]['population'].sum()
                        age_affected_bs = df[df['age'] == age][var + '_absolute_bs'].sum()
                        age_affected_as = df[df['age'] == age][var + '_absolute_as'].sum()
                        prev_by_age.append({
                            'age': age,
                            'population': age_pop,
                            'affected_bs': age_affected_bs,
                            'affected_as': age_affected_as,
                            'prevalence_bs': age_affected_bs / age_pop * 100 if age_pop > 0 else 0,
                            'prevalence_as': age_affected_as / age_pop * 100 if age_pop > 0 else 0,
                            'prevalence_change': (age_affected_as - age_affected_bs) / age_pop * 100 if age_pop > 0 else 0
                        })
                    
                    prev_by_sex = []
                    for sex in df['sex'].unique():
                        sex_pop = df[df['sex'] == sex]['population'].sum()
                        sex_affected_bs = df[df['sex'] == sex][var + '_absolute_bs'].sum()
                        sex_affected_as = df[df['sex'] == sex][var + '_absolute_as'].sum()
                        prev_by_sex.append({
                            'sex': sex,
                            'population': sex_pop,
                            'affected_bs': sex_affected_bs,
                            'affected_as': sex_affected_as,
                            'prevalence_bs': sex_affected_bs / sex_pop * 100 if sex_pop > 0 else 0,
                            'prevalence_as': sex_affected_as / sex_pop * 100 if sex_pop > 0 else 0,
                            'prevalence_change': (sex_affected_as - sex_affected_bs) / sex_pop * 100 if sex_pop > 0 else 0
                        })
                    
                    # Get the top contributing age-sex groups
                    group_contributions = df.groupby(['age', 'sex'])[var + '_absolute_diff'].sum().reset_index()
                    group_contributions.columns = ['age', 'sex', 'affected_change']
                    top_groups = group_contributions.sort_values('affected_change', key=abs, ascending=False).head(5)
                    
                    # Calculate total population metrics
                    total_population = df['population'].sum()
                    overall_prevalence_bs = total_affected_bs / total_population * 100 if total_population > 0 else 0
                    overall_prevalence_as = total_affected_as / total_population * 100 if total_population > 0 else 0
                    prevalence_change = overall_prevalence_as - overall_prevalence_bs
                    
                    # For body fat specifically, calculate distribution changes
                    distribution_changes = {}
                    if var == "body_fat_prc":
                        # Define body fat categories (example thresholds)
                        categories = [
                            {'name': 'Underweight', 'min': 0, 'max': 13},
                            {'name': 'Athletic', 'min': 13, 'max': 17},
                            {'name': 'Fitness', 'min': 17, 'max': 25},
                            {'name': 'Acceptable', 'min': 25, 'max': 32},
                            {'name': 'Overweight', 'min': 32, 'max': float('inf')}
                        ]
                        
                        for category in categories:
                            # Count people in this category for baseline and alternative
                            cat_mask_bs = (df[var + '_bs'] >= category['min']) & (df[var + '_bs'] < category['max'])
                            cat_mask_as = (df[var + '_as'] >= category['min']) & (df[var + '_as'] < category['max'])
                            
                            cat_count_bs = (df.loc[cat_mask_bs, 'population']).sum()
                            cat_count_as = (df.loc[cat_mask_as, 'population']).sum()
                            
                            distribution_changes[category['name']] = {
                                'count_bs': cat_count_bs,
                                'count_as': cat_count_as,
                                'count_change': cat_count_as - cat_count_bs,
                                'pct_bs': cat_count_bs / total_population * 100 if total_population > 0 else 0,
                                'pct_as': cat_count_as / total_population * 100 if total_population > 0 else 0,
                                'pct_change': (cat_count_as - cat_count_bs) / total_population * 100 if total_population > 0 else 0
                            }
                    
                    result_dict.update({
                        "total_affected_bs": total_affected_bs,
                        "total_affected_as": total_affected_as,
                        "affected_change": affected_change,
                        "affected_change_pct": (affected_change / total_affected_bs * 100) if total_affected_bs != 0 else np.nan,
                        "overall_prevalence_bs": overall_prevalence_bs,
                        "overall_prevalence_as": overall_prevalence_as,
                        "prevalence_change": prevalence_change,
                        "affected_by_age": affected_by_age.to_dict('records'),
                        "affected_by_sex": affected_by_sex.to_dict('records'),
                        "prevalence_by_age": prev_by_age,
                        "prevalence_by_sex": prev_by_sex,
                        "top_contributing_groups": top_groups.to_dict('records')
                    })
                    
                    # Add distribution changes if available
                    if distribution_changes:
                        result_dict["distribution_changes"] = distribution_changes
                  # Add the results to our collection
                results.append(result_dict)
                
                # Generate a specialized analysis report for each variable type
                # This includes demographic contribution analysis and detailed impact assessment
                report_dict = {
                    "variable": var,
                    "friendly_name": variable_friendly_names.get(var, var),
                    "overall_change": {
                        "relative_change_pct": result_dict.get("relative_change_pct", 0),
                        "absolute_change": result_dict.get("absolute_change", 0)
                    },
                    "top_contributors": result_dict.get("top_contributing_groups", []),
                    "demographic_impact": {}
                }
                
                # Calculate impact by age groups (aggregate across sexes)
                age_impact = df.groupby('age')[[var + '_diff', var + '_bs']].apply(
                    lambda x: pd.Series({
                        'change': (x[var + '_diff'] * df.loc[x.index, 'population']).sum(),
                        'baseline': (x[var + '_bs'] * df.loc[x.index, 'population']).sum(),
                        'population': df.loc[x.index, 'population'].sum()
                    })
                ).reset_index()
                
                # Calculate impact by sex (aggregate across age groups)
                sex_impact = df.groupby('sex')[[var + '_diff', var + '_bs']].apply(
                    lambda x: pd.Series({
                        'change': (x[var + '_diff'] * df.loc[x.index, 'population']).sum(),
                        'baseline': (x[var + '_bs'] * df.loc[x.index, 'population']).sum(),
                        'population': df.loc[x.index, 'population'].sum()
                    })
                ).reset_index()
                
                # Add demographic breakdowns to the report
                report_dict["demographic_impact"]["by_age"] = age_impact.to_dict('records')
                report_dict["demographic_impact"]["by_sex"] = sex_impact.to_dict('records')
                
                # Add variable-specific metrics
                if var in rate_variables:
                    # Employment metrics
                    report_dict["employment_metrics"] = {
                        "total_employed_bs": result_dict.get("total_employed_bs", 0),
                        "total_employed_as": result_dict.get("total_employed_as", 0),
                        "net_employment_change": result_dict.get("employed_change", 0),
                        "employment_change_pct": result_dict.get("employed_change_pct", 0),
                        "employment_change_by_sex": sex_impact.to_dict('records')
                    }
                
                elif var in per_capita_variables:
                    # Health metrics, absence, etc.
                    report_dict["impact_metrics"] = {
                        "total_impact_bs": result_dict.get("total_impact_bs", 0),
                        "total_impact_as": result_dict.get("total_impact_as", 0),
                        "net_impact_change": result_dict.get("impact_change", 0),
                        "impact_change_pct": result_dict.get("impact_change_pct", 0)
                    }
                    
                    # Special case for absence days
                    if var == "absence":
                        working_pop = df[df['age'].isin(age_groups_20_64)]['population'].sum()
                        report_dict["absence_metrics"] = {
                            "working_population": working_pop,
                            "days_lost_per_worker_bs": result_dict.get("total_days_lost_bs", 0) / working_pop if working_pop > 0 else 0,
                            "days_lost_per_worker_as": result_dict.get("total_days_lost_as", 0) / working_pop if working_pop > 0 else 0,
                            "total_days_lost_bs": result_dict.get("total_days_lost_bs", 0),
                            "total_days_lost_as": result_dict.get("total_days_lost_as", 0),
                            "days_lost_change": result_dict.get("days_lost_change", 0)
                        }
                    
                    # Special case for public health costs
                    if var == "public_health_costs":
                        report_dict["cost_metrics"] = {
                            "total_costs_bs": result_dict.get("total_costs_bs", 0),
                            "total_costs_as": result_dict.get("total_costs_as", 0),
                            "cost_savings": result_dict.get("costs_savings", 0),
                            "additional_costs": result_dict.get("additional_costs", 0),
                            "cost_change_pct": (result_dict.get("impact_change", 0) / result_dict.get("total_impact_bs", 1) * 100)
                        }
                
                elif var in prevalence_variables:
                    # Body fat % and other prevalence metrics
                    report_dict["prevalence_metrics"] = {
                        "total_affected_bs": result_dict.get("total_affected_bs", 0),
                        "total_affected_as": result_dict.get("total_affected_as", 0),
                        "affected_change": result_dict.get("affected_change", 0),
                        "affected_change_pct": result_dict.get("affected_change_pct", 0),
                        "prevalence_by_sex": sex_impact.to_dict('records')
                    }
                
                # Save the detailed report to a JSON file
                report_file = f"{var}_detailed_analysis.json"
                with open(report_file, 'w') as f:
                    json.dump(report_dict, f, indent=4)
                
            except ZeroDivisionError:
                result_bs = result_as = np.nan
                print(f"Warning: Zero division error when calculating weighted average for {var}")
                results.append({
                    "variable": var,
                    "result_bs": result_bs,
                    "result_as": result_as,
                    "absolute_change": np.nan,
                    "relative_change_pct": np.nan
                })
            
            # Show progress
            print_progress(i + 1, len(baseline_vars), prefix='Progress:', suffix='Complete', bar_length=50)
          # Convert result summary to DataFrame
        summary_df = pd.DataFrame(results)
        
        # Create a more detailed summary for export
        detailed_summary_rows = []
        
        for result in results:
            var = result.get("variable")
            
            # Base row with common metrics
            base_row = {
                "Variable": var,
                "Friendly Name": variable_friendly_names.get(var, var),
                "Baseline Value": result.get("result_bs"),
                "Alternative Value": result.get("result_as"),
                "Absolute Change": result.get("absolute_change"),
                "Relative Change (%)": result.get("relative_change_pct")
            }
            
            # Add variable-specific metrics
            if var in rate_variables:
                # Employment specific metrics
                base_row.update({
                    "Total in Baseline": result.get("total_employed_bs"),
                    "Total in Alternative": result.get("total_employed_as"),
                    "Total Change": result.get("employed_change"),
                    "Total Change (%)": result.get("employed_change_pct")
                })
            
            elif var in per_capita_variables:
                # Health indicators, absence, public health costs
                base_row.update({
                    "Total Impact Baseline": result.get("total_impact_bs"),
                    "Total Impact Alternative": result.get("total_impact_as"),
                    "Total Impact Change": result.get("impact_change"),
                    "Total Impact Change (%)": result.get("impact_change_pct")
                })
                
                # Additional metrics for specific variables
                if var == "absence":
                    base_row.update({
                        "Total Days Lost Baseline": result.get("total_days_lost_bs"),
                        "Total Days Lost Alternative": result.get("total_days_lost_as"),
                        "Days Lost Change": result.get("days_lost_change"),
                        "Days Lost Change (%)": result.get("days_lost_change_pct"),
                        "Economic Impact Baseline": result.get("estimated_economic_impact_bs"),
                        "Economic Impact Alternative": result.get("estimated_economic_impact_as"),
                        "Economic Impact Change": result.get("economic_impact_change")
                    })
                
                elif var == "public_health_costs":
                    base_row.update({
                        "Total Costs Baseline": result.get("total_costs_bs"),
                        "Total Costs Alternative": result.get("total_costs_as"),
                        "Cost Savings": result.get("cost_savings"),
                        "Additional Costs": result.get("additional_costs"),
                        "Per Capita Costs Baseline": result.get("per_capita_costs_bs"),
                        "Per Capita Costs Alternative": result.get("per_capita_costs_as")
                    })
                
                elif var in ["diabetes", "hypertension", "cancer", "heart_disease", "stroke", 
                           "colorectal_cancer", "breast_cancer", "endometrial_cancer", 
                           "depression", "anxiety"]:
                    base_row.update({
                        "Total Cases Baseline": result.get("total_cases_bs"),
                        "Total Cases Alternative": result.get("total_cases_as"),
                        "Cases Change": result.get("cases_change"),
                        "Prevalence Rate Baseline (%)": result.get("prevalence_rate_bs"),
                        "Prevalence Rate Alternative (%)": result.get("prevalence_rate_as"),
                        "Prevalence Rate Change (%)": result.get("prevalence_rate_change")
                    })
            
            elif var in prevalence_variables:
                # Body fat and other prevalence variables
                base_row.update({
                    "Total Affected Baseline": result.get("total_affected_bs"),
                    "Total Affected Alternative": result.get("total_affected_as"),
                    "Affected Change": result.get("affected_change"),
                    "Affected Change (%)": result.get("affected_change_pct"),
                    "Overall Prevalence Baseline (%)": result.get("overall_prevalence_bs"),
                    "Overall Prevalence Alternative (%)": result.get("overall_prevalence_as"),
                    "Prevalence Change (%)": result.get("prevalence_change")
                })
            
            detailed_summary_rows.append(base_row)
        
        # Convert to DataFrame
        detailed_summary_df = pd.DataFrame(detailed_summary_rows)
        
        # Print summary to console
        print("\nSimulation Results Summary:")
        print(summary_df)
        
        # Save results to Excel files
        print(f"Saving summary results to {output_file}...")
        detailed_summary_df.to_excel(output_file, index=False)
        
        print(f"Saving detailed results to {detailed_output_file}...")
        # Save the entire dataframe with all calculated columns
        with pd.ExcelWriter(detailed_output_file, engine='openpyxl') as writer:
            # Save the summary results
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Save the more readable detailed summary
            detailed_summary_df.to_excel(writer, sheet_name='DetailedSummary', index=False)
            
            # Save demographic contribution data
            demo_contributions = []
            for result in results:
                var = result.get("variable")
                
                # Get top contributing groups if available
                if "top_contributing_groups" in result:
                    for group in result.get("top_contributing_groups", []):
                        demo_contributions.append({
                            "Variable": var,
                            "Age Group": group.get("age"),
                            "Sex": group.get("sex"),
                            "Contribution": group.get("employment_change" if var in rate_variables else 
                                                     "impact_change" if var in per_capita_variables else
                                                     "affected_change" if var in prevalence_variables else None),
                            "Contribution (%)": group.get("contribution_pct", 0)
                        })
            
            # Convert to DataFrame and save
            if demo_contributions:
                demo_df = pd.DataFrame(demo_contributions)
                demo_df.to_excel(writer, sheet_name='DemographicContributions', index=False)
            
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