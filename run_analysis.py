# Run both simulation and visualization
import os
import sys
import time
import subprocess
import datetime

def run_command(command, description):
    """Run a command and display its output in real-time."""
    print(f"\n{'-'*80}")
    print(f"RUNNING: {description}")
    print(f"{'-'*80}\n")
    
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            shell=True
        )
        
        for line in process.stdout:
            print(line, end='')
        
        process.wait()
        return process.returncode
    except Exception as e:
        print(f"Error running command: {e}")
        return 1

def main():
    """Run the complete simulation and visualization workflow."""
    start_time = time.time()
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print(f"\n{'='*80}")
    print(f"DEMOGRAPHIC COUNTERFACTUAL SIMULATION - {timestamp}")
    print(f"{'='*80}\n")
    
    print(f"Working directory: {os.getcwd()}")
    
    # Create backup of previous results if they exist
    if os.path.exists("Output.xlsx"):
        backup_dir = "backups"
        os.makedirs(backup_dir, exist_ok=True)
        
        try:
            os.rename("Output.xlsx", f"{backup_dir}/Output_{timestamp}.xlsx")
            print(f"Created backup: {backup_dir}/Output_{timestamp}.xlsx")
        except Exception as e:
            print(f"Could not create backup of previous Output.xlsx: {str(e)}")
    
    print("Running simulation script...")
    # Run simulation
    simulation_code = run_command("python simulation2.py", "Simulation")
    print(f"Simulation finished with return code: {simulation_code}")
    
    if simulation_code != 0:
        print("Simulation failed. Exiting.")
        return simulation_code
    
    print("Running visualization script...")
    # Run visualization
    visualization_code = run_command("python visualize_results.py", "Visualization")
    print(f"Visualization finished with return code: {visualization_code}")
    
    if visualization_code != 0:
        print("Visualization failed, but simulation completed successfully.")
    
    # Calculate total runtime
    total_time = time.time() - start_time
    
    print(f"\n{'='*80}")
    print(f"WORKFLOW COMPLETED - Total execution time: {total_time:.2f} seconds")
    print(f"{'='*80}\n")
    
    # List generated files
    print("Generated files:")
    print("- Output.xlsx (Summary results)")
    print("- DetailedOutput.xlsx (Detailed results)")
    print("- plots/ (Visualizations)")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
