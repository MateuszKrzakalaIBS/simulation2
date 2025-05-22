"""
Test suite for simulation2.py.
This module provides comprehensive testing for the demographic simulation functionality.
"""

import unittest
import pandas as pd
import numpy as np
import os
import shutil
import tempfile
import json
from simulation2 import run_simulation, load_config

class SimulationTestCase(unittest.TestCase):
    """Test cases for the simulation functionality."""
    
    @classmethod
    def setUpClass(cls):
        """Create a temporary directory and sample data for testing."""
        cls.test_dir = tempfile.mkdtemp()
        
        # Create a simple test dataset
        cls.data_df = pd.DataFrame({
            'year': [2024, 2024, 2024, 2024],
            'age': ['20-24', '25-29', '30-34', '35-39'],
            'sex': ['M', 'M', 'K', 'K'],
            'population': [100, 150, 120, 180],
            's1': [0.2, 0.3, 0.25, 0.35],
            's2': [0.5, 0.4, 0.45, 0.35],
            's3': [0.3, 0.3, 0.3, 0.3],
            'var1': [10, 15, 12, 18],
            'var2': [5, 6, 7, 8]
        })
        
        # Create simple parameters
        cls.params_df = pd.DataFrame({
            'variable': ['var1', 'var2'],
            's_n_men': [1.2, 0.8],
            's_n_women': [0.9, 1.1],
            'w_s_men': [1.1, 0.9],
            'w_s_women': [0.95, 1.05],
            'age_1': ['20-24', '20-24'],
            'age_2': ['25-29', '25-29'],
            'age_3': ['30-34', '30-34'],
            'age_4': ['35-39', '35-39']
        })
        
        # Create test input file
        cls.input_file = os.path.join(cls.test_dir, 'test_input.xlsx')
        with pd.ExcelWriter(cls.input_file, engine='openpyxl') as writer:
            cls.data_df.to_excel(writer, sheet_name='data_2024', index=False)
            cls.params_df.to_excel(writer, sheet_name='parameters', index=False)
        
        # Create test config
        cls.config = {
            "simulation": {
                "input_file": cls.input_file,
                "output_file": os.path.join(cls.test_dir, "test_output.xlsx"),
                "detailed_output_file": os.path.join(cls.test_dir, "test_detailed.xlsx"),
                "shock_scenario": {
                    "s1_change": -0.1,
                    "s2_change": 0.1,
                    "s3_change": 0.0
                },
                "variables_to_exclude": []
            }
        }
        
        # Write config to file
        cls.config_file = os.path.join(cls.test_dir, 'test_config.json')
        with open(cls.config_file, 'w') as f:
            json.dump(cls.config, f)
    
    @classmethod
    def tearDownClass(cls):
        """Clean up temporary test directory."""
        shutil.rmtree(cls.test_dir)
    
    def test_load_config(self):
        """Test that config loading works correctly."""
        config = load_config(self.config_file)
        self.assertEqual(config['simulation']['input_file'], self.input_file)
        self.assertEqual(config['simulation']['shock_scenario']['s1_change'], -0.1)
    
    def test_run_simulation(self):
        """Test that simulation runs and produces expected outputs."""
        summary_df, detailed_df = run_simulation(self.config)
        
        # Check that output files were created
        self.assertTrue(os.path.exists(self.config['simulation']['output_file']))
        self.assertTrue(os.path.exists(self.config['simulation']['detailed_output_file']))
        
        # Test that summary has expected shape and columns
        self.assertEqual(len(summary_df), 2)  # 2 variables
        self.assertTrue(all(col in summary_df.columns for col in 
                           ['variable', 'result_bs', 'result_as', 'absolute_change', 'relative_change_pct']))
        
        # Test that detailed_df has expected columns
        for var in ['var1', 'var2']:
            expected_cols = [f'{var}_denominator', f'{var}_s1', f'{var}_s2', f'{var}_s3', f'{var}_bs', f'{var}_as']
            self.assertTrue(all(col in detailed_df.columns for col in expected_cols))
    
    def test_shock_scenario(self):
        """Test that shock scenario is correctly applied."""
        _, detailed_df = run_simulation(self.config)
        
        # Check that shock values are correctly applied 
        for i, row in detailed_df.iterrows():
            self.assertAlmostEqual(row['s1_as'], row['s1'] - 0.1)
            self.assertAlmostEqual(row['s2_as'], row['s2'] + 0.1)
            self.assertAlmostEqual(row['s3_as'], row['s3'])  # No change
    
    def test_variable_exclusion(self):
        """Test that variable exclusion works."""
        # Create config that excludes var2
        exclude_config = self.config.copy()
        exclude_config['simulation']['variables_to_exclude'] = ['var2']
        
        summary_df, _ = run_simulation(exclude_config)
        
        # Check that only var1 is in the summary
        self.assertEqual(len(summary_df), 1)
        self.assertEqual(summary_df['variable'].iloc[0], 'var1')


if __name__ == '__main__':
    unittest.main()
