"""
Setup script for the demographic simulation tool.
This script installs required dependencies and prepares the environment.
"""

import subprocess
import sys
import os
import platform


def check_python_version():
    """Check that Python version is 3.7 or higher."""
    if sys.version_info < (3, 7):
        print("Python 3.7 or higher is required.")
        print(f"Current Python version: {platform.python_version()}")
        return False
    return True


def install_dependencies():
    """Install required dependencies."""
    print("Installing required packages...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=True)
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        return False


def create_directories():
    """Create necessary directories."""
    directories = ["plots", "plots/projections", "plots/multivariate", "data_cache", "backups"]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")


def check_config():
    """Check if config file exists, create default if not."""
    if not os.path.exists("config.json"):
        import json
        default_config = {
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
            },
            "visualization": {
                "output_folder": "plots",
                "create_summary_plots": True,
                "create_detailed_plots": True,
                "plot_format": "png",
                "color_scheme": "RdBu_r"
            }
        }
        
        with open("config.json", "w") as f:
            json.dump(default_config, f, indent=4)
            
        print("Created default config.json file")


def run_tests():
    """Run the test suite."""
    print("Running tests...")
    try:
        result = subprocess.run([sys.executable, "-m", "pytest", "test_simulation.py", "-v"], check=False)
        if result.returncode == 0:
            print("All tests passed!")
            return True
        else:
            print("Some tests failed. Please review the test output.")
            return False
    except Exception as e:
        print(f"Error running tests: {e}")
        return False


def create_test_input():
    """Create a small test input file if none exists."""
    if not os.path.exists("Test_Input.xlsx"):
        try:
            import pandas as pd
            import numpy as np
            
            # Create a simple test dataset
            data_df = pd.DataFrame({
                'year': [2024] * 8,
                'age': ['20-24', '25-29', '20-24', '25-29'] * 2,
                'sex': ['M', 'M', 'K', 'K'] * 2,
                'population': [100, 150, 120, 180] * 2,
                's1': [0.2, 0.3, 0.25, 0.35] * 2,
                's2': [0.5, 0.4, 0.45, 0.35] * 2,
                's3': [0.3, 0.3, 0.3, 0.3] * 2,
                'var1': [10, 15, 12, 18, 11, 16, 13, 19],
                'var2': [5, 6, 7, 8, 6, 7, 8, 9]
            })
            
            # Create simple parameters
            params_df = pd.DataFrame({
                'variable': ['var1', 'var2'],
                's_n_men': [1.2, 0.8],
                's_n_women': [0.9, 1.1],
                'w_s_men': [1.1, 0.9],
                'w_s_women': [0.95, 1.05],
                'age_1': ['20-24', '20-24'],
                'age_2': ['25-29', '25-29']
            })
            
            # Save to Excel
            with pd.ExcelWriter("Test_Input.xlsx", engine='openpyxl') as writer:
                data_df.to_excel(writer, sheet_name='data_2024', index=False)
                params_df.to_excel(writer, sheet_name='parameters', index=False)
                
            print("Created test input file: Test_Input.xlsx")
            return True
            
        except Exception as e:
            print(f"Error creating test input file: {e}")
            return False
    
    return True


def print_success_message():
    """Print success message with instructions."""
    print("\n" + "="*80)
    print("SETUP COMPLETED SUCCESSFULLY")
    print("="*80)
    print("\nYou can now run the simulation using:")
    print("  python simulation2.py")
    print("\nTo visualize results:")
    print("  python visualize_results.py")
    print("\nTo run both simulation and visualization:")
    print("  python run_analysis.py")
    print("\nTo start the web interface:")
    print("  cd web && streamlit run app.py")
    print("\nTo run time series projections:")
    print("  python time_series_projection.py")
    print("\nTo run multivariate analysis:")
    print("  python multivariate_analysis.py")
    print("\nTo download external data:")
    print("  python external_data_integration.py")
    print("\nHappy analyzing!")
    print("="*80)


def main():
    """Main setup function."""
    print("\n" + "="*80)
    print("SETTING UP DEMOGRAPHIC SIMULATION TOOL")
    print("="*80 + "\n")
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("Failed to install dependencies. Setup cannot continue.")
        sys.exit(1)
    
    # Create directories
    create_directories()
    
    # Check config
    check_config()
    
    # Create test input
    create_test_input()
    
    # Run tests
    run_tests()
    
    # Print success message
    print_success_message()


if __name__ == "__main__":
    main()
