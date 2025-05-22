# Demographic Counterfactual Simulation

This project contains a comprehensive simulation and analysis system for evaluating counterfactual demographic scenarios and their impact on various socioeconomic and health variables.

## Overview

The system consists of the following components:

1. **Input Data**: Excel file with demographic and variable parameters
2. **Simulation Engine**: Python script to run counterfactual scenarios
3. **Visualization Tools**: Scripts to generate various charts and plots of results
4. **Advanced Analysis**: Time series projections and multivariate analysis
5. **Integration Tools**: External data integration from Eurostat and World Bank
6. **Web Interface**: User-friendly UI for non-technical users
7. **Testing Framework**: Comprehensive tests to ensure reliability

## Installation

### Method 1: Easy Deployment (Recommended)

1. Run the deployment script:
   - Windows Command Prompt: Double-click `deploy_simulation.bat`
   - PowerShell: Right-click `deploy_simulation.ps1` and select "Run with PowerShell"

   This will create a virtual environment, install all required dependencies, and provide you with launch options.

### Method 2: Manual Installation

1. Make sure you have Python 3.8 or higher installed
2. Run the setup script:
   ```
   python setup.py
   ```
   This will install all required dependencies, create necessary directories, and set up a default configuration.

3. Alternatively, install dependencies manually:
   ```
   pip install -r requirements.txt
   ```

## Files

- `simulation2.py`: Main simulation script
- `visualize_results.py`: Basic visualization of simulation results
- `interactive_visualizations.py`: Enhanced interactive visualizations with Plotly
- `time_series_projection.py`: Future projections of simulation results
- `multivariate_analysis.py`: Correlation and PCA analysis of variables
- `external_data_integration.py`: Integration with Eurostat and World Bank data
- `run_analysis.py`: Convenience script to run both simulation and visualization
- `setup.py`: Installation and setup script
- `test_simulation.py`: Test suite for simulation functionality
- `web/app.py`: Standard Streamlit-based web interface
- `web/interactive_app.py`: Enhanced interactive web interface with Plotly visualizations
- `Input.xlsx`: Input parameters and data
- `Output.xlsx`: Summary results from simulation
- `DetailedOutput.xlsx`: Detailed results including demographic breakdowns
- `config.json`: Configuration settings
- `plots/`: Folder containing all visualizations

## Running the Simulation

### Method 1: Using the Deployment Script (Recommended)

Run the deployment script and select from the options menu:
```
deploy_simulation.bat  # For Command Prompt
```
or
```
.\deploy_simulation.ps1  # For PowerShell
```

### Method 2: Running Individual Components

1. Basic simulation:
   ```
   python simulation2.py
   ```

2. Generate visualizations:
   ```
   python visualize_results.py
   ```

3. Run both simulation and visualization:
   ```
   python run_analysis.py
   ```

4. Standard web interface:
   ```
   cd web
   streamlit run app.py
   ```
   
5. Interactive web interface (recommended):
   ```
   cd web
   streamlit run interactive_app.py
   ```

6. Time series projections:
   ```
   python time_series_projection.py
   ```

7. Multivariate analysis:
   ```
   python multivariate_analysis.py
   ```

8. External data integration:
   ```
   python external_data_integration.py --country PL --year 2022 --output External_Input.xlsx
   ```

## Command-Line Options

The simulation script supports various command-line options:

```
python simulation2.py --config config.json --s1 -0.1 --s2 0.1 --s3 0.0 --input Input.xlsx --output Output.xlsx --detailed-output DetailedOutput.xlsx
```

Where:
- `--config`: Path to configuration file
- `--s1`, `--s2`, `--s3`: Override shock scenario values
- `--input`: Input file path
- `--output`: Output file path
- `--detailed-output`: Detailed output file path

## Configuration

The simulation is configured through `config.json`:

```json
{
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
        "create_summary_plots": true,
        "create_detailed_plots": true,
        "plot_format": "png",
        "color_scheme": "RdBu_r"
    }
}
```

## Input Format

The `Input.xlsx` file should contain at least the following sheets:

- `parameters`: Contains variable names and demographic ratios
- `data_2024`: Contains baseline population data and values

## Output Format

The simulation generates two main output files:

1. `Output.xlsx`: Summary of results for each variable, including:
   - Baseline values
   - Alternative scenario values
   - Absolute and relative changes

2. `DetailedOutput.xlsx`: Detailed demographic breakdown of results, with a sheet for each variable.

## Visualizations

Running `visualize_results.py` generates various charts:

1. **Summary visualizations**:
   - Relative changes across all variables
   - Before/after comparison
   - Absolute changes

2. **Detailed visualizations** for each variable:
   - Demographic heatmaps (values by age and sex)
   - Age group comparisons between baseline and alternative scenarios
   - Absolute and percentage differences by age group

## Advanced Analysis

### Time Series Projections

The `time_series_projection.py` module provides:

- Projection of simulation results into the future (configurable number of years)
- Visualization of projected trends for each variable
- Comparison of baseline and alternative scenarios over time
- Highlight specific milestone years

### Multivariate Analysis

The `multivariate_analysis.py` module provides:

- Correlation analysis between variables in both baseline and alternative scenarios
- Principal Component Analysis (PCA) to identify relationships and patterns
- Demographic filtering to analyze relationships for specific subgroups
- Visualization of correlation matrices and PCA components

### External Data Integration

The `external_data_integration.py` module provides:

- Integration with Eurostat demographic data
- Integration with World Bank health and socioeconomic indicators
- Data caching to avoid repeated downloads
- Automatic formatting of external data to match input requirements

## Web Interface

The Streamlit-based web interface (`web/app.py`) provides:

- User-friendly configuration of simulation parameters
- Interactive visualization of results
- Advanced analysis capabilities
- Easy sharing of results

## Testing

Run the test suite:
```
python -m pytest test_simulation.py -v
```

## How the Simulation Works

1. **Data Loading**: Load parameters and baseline data
2. **Parameter Application**: Apply demographic factors by age and sex
3. **Scenario Creation**: Apply shock scenario (e.g., -0.1 to s1, +0.1 to s2)
4. **Variable Processing**: Calculate adjusted values for each variable
5. **Result Calculation**: Calculate population-weighted averages for both scenarios
6. **Output Generation**: Create summary and detailed results
7. **Visualization**: Generate charts and plots
8. **Advanced Analysis**: Perform time series projections and multivariate analysis

## Performance Considerations

The simulation has been optimized to:
- Minimize DataFrame fragmentation
- Efficiently process data in batches
- Provide progress indicators for long-running operations
- Cache external data to avoid repeated downloads

For large datasets, consider:
- Running on a machine with sufficient memory
- Reducing the number of variables or demographic groups
- Using the batch processing capabilities

## Troubleshooting

1. **Missing dependencies**:
   ```
   pip install -r requirements.txt
   ```

2. **Configuration issues**:
   Check `config.json` for correct paths and parameters

3. **Input file format**:
   Ensure `Input.xlsx` has the required sheets and columns

4. **Memory errors**:
   Reduce the number of variables or use a machine with more RAM

## License

Copyright © 2025 IBS
