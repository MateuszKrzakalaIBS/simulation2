# Import necessary libraries
import pandas as pd
import os
import numpy as np

# Set working directory to the folder where the Excel file is located
os.chdir(r'C:\Users\mkrzakala\OneDrive - IBS\BENEFIT PROJEKT\analiza\simulation')

# Load the input Excel file containing three sheets
parameters_df = pd.read_excel('Input.xlsx', sheet_name='parameters')
data_df = pd.read_excel('Input.xlsx', sheet_name='data_2024')

# Display the first few rows of each sheet to verify successful loading
print(parameters_df.head())
print(data_df.head())

# Alias for the data frame
df = data_df

# Create a new column: share of absence among the working population
df["absence_pc"] = df["absence"] / df["working"]

# Define age groups considered as working-age population (20–64)
age_groups_20_64 = [
    "20-24", "25-29", "30-34", "35-39", "40-44",
    "45-49", "50-54", "55-59", "60-64"
]

# Create a new column with population in the 20–64 range; 0 otherwise
df["population_20_64"] = df.apply(
    lambda row: row["population"] if row["age"] in age_groups_20_64 else 0,
    axis=1
)

# Print all variable names from the parameters table
for _, row in parameters_df.iterrows():
    print(row['variable'])

# Identify columns related to age groups in the parameters table
age_cols = [col for col in parameters_df.columns if col.startswith("age_")]

# Apply static (s_n) and dynamic (w_s) weights based on age and sex for each variable
for _, row in parameters_df.iterrows():
    variable = row["variable"]
    valid_ages = row[age_cols].dropna().tolist()
    col_s_n = f"{variable}_s_n"
    col_w_s = f"{variable}_w_s"
    df[col_s_n] = 1.0
    df[col_w_s] = 1.0
    df.loc[(df["sex"] == "M") & (df["age"].isin(valid_ages)), col_s_n] = row["s_n_men"]
    df.loc[(df["sex"] == "K") & (df["age"].isin(valid_ages)), col_s_n] = row["s_n_women"]
    df.loc[(df["sex"] == "M") & (df["age"].isin(valid_ages)), col_w_s] = row["w_s_men"]
    df.loc[(df["sex"] == "K") & (df["age"].isin(valid_ages)), col_w_s] = row["w_s_women"]

# Define an alternative shock scenario (s1 reduced by 0.1, s2 increased by 0.1)
df['s1_as'] = df['s1'] - 0.1
df['s2_as'] = df['s2'] + 0.1
df['s3_as'] = df['s3']

# List of variable names to calculate theoretical values for
var_list = ["mortality"]

# Calculate base and alternative scenario values for each variable
for i in var_list:
    df[i + "_denominator"] = df['s1'] + df['s2'] * df[i + "_s_n"] + df['s3'] * df[i + "_s_n"] * df[i + "_w_s"]
    df[i + "_s1"] = df[i] / df[i + "_denominator"]
    df[i + "_s2"] = df[i + "_s1"] * df[i + "_s_n"]
    df[i + "_s3"] = df[i + "_s2"] * df[i + "_w_s"]
    df[i + "_bs"] = df['s1'] * df[i + "_s1"] + df['s2'] * df[i + "_s2"] + df['s3'] * df[i + "_s3"]
    df[i + "_as"] = df['s1_as'] * df[i + "_s1"] + df['s2_as'] * df[i + "_s2"] + df['s3_as'] * df[i + "_s3"]

# Set up aggregation method for each variable
agg_data = {
    "name": ["mortality"],
    "type": ["average"],
    "weight": ["population"]
}

results = pd.DataFrame(agg_data)

# Calculate aggregated results under both baseline and alternative scenarios
for idx, row in results.iterrows():
    name = row["name"]
    agg_type = row["type"]
    weight_key = row["weight"]

    if agg_type == "sum":
        result_bs = df[name + '_bs'].sum()
        result_as = df[name + '_as'].sum()
    elif agg_type == "average" and weight_key != "na":
        w = df[weight_key]
        v_bs = df[name + '_bs']
        v_as = df[name + '_as']
        result_bs = np.average(v_bs, weights=w)
        result_as = np.average(v_as, weights=w)
    else:
        result_bs = result_as = "n/a"

    results.at[idx, "result_bs"] = result_bs
    results.at[idx, "result_as"] = result_as

# Export the results to an Excel file
results.to_excel("output.xlsx", index=False)
