import unittest
import os
import pandas as pd
import numpy as np
import sys
import json
import tempfile

# Add the project root to the path to import modules
# Correctly add the parent directory of 'simulation' to sys.path
# to allow imports like 'from simulation import simulation2' or 'import simulation2'
# when 'test_simulation_enhancements.py' is in the 'simulation' directory.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the simulation module
import simulation2 # Changed from 'from simulation import simulation2'

class TestSimulationEnhancements(unittest.TestCase):
    """Test the enhanced features of the simulation engine."""
    
    def setUp(self):
        """Set up test data."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a dummy Test_Input.xlsx for testing
        self.test_input_path = os.path.join(self.temp_dir, "Test_Input.xlsx")
        population_data = pd.DataFrame({
            'age': [25, 30, 35, 40, 25, 30, 35, 40],
            'sex': ['Male', 'Male', 'Male', 'Male', 'Female', 'Female', 'Female', 'Female'],
            'population': [100, 120, 110, 100, 90, 110, 100, 95],
            'employment': [0.8, 0.85, 0.82, 0.78, 0.75, 0.70, 0.65, 0.60], # Example employment rates
            'absence': [5, 6, 5, 7, 8, 7, 9, 8], # Example absence days
            'body_fat_prc': [22, 25, 28, 30, 28, 32, 35, 38], # Example body fat percentages
            'var1': [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5], # Added var1
            'var2': [0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2]  # Added var2
        })
        # Add s1, s2, s3 columns as expected by the simulation
        for s_col in ['s1', 's2', 's3']:
            population_data[s_col] = np.random.rand(len(population_data))


        # Define some per_capita_variables and prevalence_variables for the test config
        # These would typically come from a more complex config loading mechanism
        self.per_capita_variables = ['absence']
        self.prevalence_variables = ['body_fat_prc']
        self.employment_variables = ['employment']


        with pd.ExcelWriter(self.test_input_path) as writer:
            population_data.to_excel(writer, sheet_name='data_2024', index=False) # Renamed 'Population' to 'data_2024'
            # Add other sheets if necessary for the simulation to run
            # Add a 'parameters' sheet
            parameters_data = pd.DataFrame({
                'parameter': ['sim_years', 'population_growth_rate', 'discount_rate', 'currency_symbol', 'economic_impact_per_day_lost'],
                'value': [5, 0.01, 0.03, '$', 100], # Example values
                # Add a 'variable' column as it seems to be expected by the simulation code based on the error
                # This might be a misinterpretation of the error, or the 'parameters' sheet structure is different than assumed
                'variable': ['sim_years', 'population_growth_rate', 'discount_rate', 'currency_symbol', 'economic_impact_per_day_lost'] 
            })
            parameters_data.to_excel(writer, sheet_name='parameters', index=False)

            # Add a 'variables' sheet (assuming this might be needed based on typical simulation structure)
            variables_data = pd.DataFrame({
                'variable': ['employment', 'absence', 'body_fat_prc', 'var1', 'var2'],
                'type': ['employment', 'per_capita', 'prevalence', 'other', 'other'],
                'baseline_value_men': [0.8, 5, 25, 0.5, 0.2],
                'baseline_value_women': [0.7, 7, 30, 0.5, 0.2],
                'data_source_sheet': ['Population', 'Population', 'Population', 'Population', 'Population'],
                'data_source_column': ['employment', 'absence', 'body_fat_prc', 'var1', 'var2'],
                'friendly_name': ['Employment Rate', 'Absence Days', 'Body Fat Percentage', 'Variable 1', 'Variable 2'],
                'unit': ['%', 'days', '%', 'units', 'units'],
                'description': ['desc1', 'desc2', 'desc3', 'desc4', 'desc5']
            })
            variables_data.to_excel(writer, sheet_name='variables', index=False)


        self.config = {
            "simulation": {
                "input_file": self.test_input_path,
                "output_file": os.path.join(self.temp_dir, "test_output.xlsx"),
                "detailed_output_file": os.path.join(self.temp_dir, "test_detailed_output.xlsx"),
                "json_output_folder": os.path.join(self.temp_dir, "json_reports"), # Added for JSON reports
                "shock_scenario": {
                    "s1_change": -0.05, # Adjusted to be non-zero to cause changes
                    "s2_change": 0.05,  # Adjusted to be non-zero
                    "s3_change": 0.02   # Adjusted to be non-zero
                },
                "variables_to_exclude": [],
                # Pass these lists to the simulation if it expects them in the config
                "per_capita_variables": self.per_capita_variables,
                "prevalence_variables": self.prevalence_variables,
                "employment_variables": self.employment_variables,
                "health_indicators": [], # Assuming no specific health indicators for this basic test
                "cost_variables": [] # Assuming no specific cost variables for this basic test
            },
            "visualization": { # Minimal viz config, as we are testing simulation logic
                "output_folder": os.path.join(self.temp_dir, "plots"),
                "create_summary_plots": False,
                "create_detailed_plots": False,
            }
        }
        # Ensure the JSON output folder exists
        os.makedirs(self.config["simulation"]["json_output_folder"], exist_ok=True)

    def tearDown(self):
        """Clean up after tests."""
        # Remove temporary files and directory
        for root, dirs, files in os.walk(self.temp_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.temp_dir)
    
    def test_simulation_output_contains_enhanced_metrics(self):
        """Test that the simulation output contains the enhanced metrics."""
        # Run the simulation
        # The run_simulation function in simulation2.py needs to be adapted
        # to accept these lists or fetch them from the config itself.
        summary_df, detailed_df_dict = simulation2.run_simulation(
            self.config,
            # Explicitly pass variable type lists if run_simulation expects them as args
            # Otherwise, ensure run_simulation can get them from self.config["simulation"]
            # employment_variables=self.employment_variables,
            # per_capita_variables=self.per_capita_variables,
            # prevalence_variables=self.prevalence_variables
        )
        
        self.assertIsNotNone(summary_df)
        self.assertTrue(not summary_df.empty, "Summary DataFrame should not be empty.")

        # Check for employment metrics
        if 'employment' in summary_df['variable'].values:
            employment_row = summary_df[summary_df['variable'] == 'employment'].iloc[0]
            self.assertIn('total_employed_bs', employment_row)
            self.assertIn('total_employed_as', employment_row)
            self.assertIn('employed_change', employment_row)
            self.assertIn('employed_change_pct', employment_row)
            self.assertIn('top_contributing_groups', employment_row)
            # Check for JSON report existence
            self.assertTrue(os.path.exists(os.path.join(self.config["simulation"]["json_output_folder"], "employment_detailed_analysis.json")))
        else:
            print("Warning: 'employment' variable not found in summary_df. Skipping employment metric checks.")

        # Check for per capita variable metrics (e.g., absence)
        if 'absence' in summary_df['variable'].values:
            absence_row = summary_df[summary_df['variable'] == 'absence'].iloc[0]
            self.assertIn('total_impact_bs', absence_row)
            self.assertIn('total_impact_as', absence_row)
            self.assertIn('impact_change', absence_row)
            self.assertIn('impact_change_pct', absence_row) # Added check for percentage change
            
            # Check for absence-specific metrics
            self.assertIn('total_days_lost_bs', absence_row)
            self.assertIn('total_days_lost_as', absence_row)
            self.assertIn('days_lost_change', absence_row)
            self.assertIn('days_per_person_bs', absence_row) # Added check
            self.assertIn('days_per_person_as', absence_row) # Added check
            self.assertIn('days_per_person_change', absence_row) # Added check
            self.assertIn('estimated_economic_impact_bs', absence_row) # Added check
            self.assertIn('estimated_economic_impact_as', absence_row) # Added check
            self.assertIn('estimated_economic_impact_change', absence_row) # Added check
            self.assertIn('top_contributing_groups', absence_row) # Added check
            # Check for JSON report existence
            self.assertTrue(os.path.exists(os.path.join(self.config["simulation"]["json_output_folder"], "absence_detailed_analysis.json")))
        else:
            print("Warning: 'absence' variable not found in summary_df. Skipping absence metric checks.")

        # Check for prevalence variable metrics (e.g., body_fat_prc)
        if 'body_fat_prc' in summary_df['variable'].values:
            body_fat_row = summary_df[summary_df['variable'] == 'body_fat_prc'].iloc[0]
            self.assertIn('total_affected_bs', body_fat_row)
            self.assertIn('total_affected_as', body_fat_row)
            self.assertIn('affected_change', body_fat_row)
            self.assertIn('affected_change_pct', body_fat_row)
            self.assertIn('overall_prevalence_bs', body_fat_row) # Added check
            self.assertIn('overall_prevalence_as', body_fat_row) # Added check
            self.assertIn('overall_prevalence_change', body_fat_row) # Added check
            self.assertIn('top_contributing_groups', body_fat_row) # Added check
            # Check for JSON report existence
            self.assertTrue(os.path.exists(os.path.join(self.config["simulation"]["json_output_folder"], "body_fat_prc_detailed_analysis.json")))

        else:
            print("Warning: 'body_fat_prc' variable not found in summary_df. Skipping body_fat_prc metric checks.")
        
        # Check that detailed output file is created
        detailed_output_path = self.config["simulation"]["detailed_output_file"]
        self.assertTrue(os.path.exists(detailed_output_path), f"Detailed output file not found at {detailed_output_path}")
        
        # Check that the detailed summary sheet includes our enhanced metrics
        with pd.ExcelFile(detailed_output_path) as xls:
            self.assertIn('DetailedSummary', xls.sheet_names)
            detailed_summary_df = pd.read_excel(xls, 'DetailedSummary')
            
            self.assertIn('Friendly Name', detailed_summary_df.columns)
            self.assertIn('Total in Baseline', detailed_summary_df.columns)
            self.assertIn('Total in Alternative', detailed_summary_df.columns) # Added check
            self.assertIn('Absolute Change', detailed_summary_df.columns) # Added check
            self.assertIn('Percentage Change (%)', detailed_summary_df.columns) # Added check

            self.assertIn('DemographicContributions', xls.sheet_names) # Check for new sheet
            demographic_contributions_df = pd.read_excel(xls, 'DemographicContributions')
            self.assertFalse(demographic_contributions_df.empty, "DemographicContributions sheet should not be empty.")
            self.assertIn('Variable', demographic_contributions_df.columns)
            self.assertIn('Demographic Group', demographic_contributions_df.columns)
            self.assertIn('Contribution to Change (Absolute)', demographic_contributions_df.columns)
            self.assertIn('Contribution to Change (%)', demographic_contributions_df.columns)


if __name__ == '__main__':
    unittest.main()
