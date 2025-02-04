#!/usr/bin/env python3

import os
import sys
from datetime import datetime
import subprocess
import re
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize



# Function to create subdir and run benchmarks
def run_benchmarks(cu_count, timestamp):
    os.makedirs(f"{timestamp}/{cu_count}CU", exist_ok=True)
    for unroll in [1, 2, 4, 6, 8]:
        output_file = f"{timestamp}/{cu_count}CU/a2a_64m_unroll{unroll}.csv"
        with open(output_file, "w") as f:
            subprocess.run(["./TransferBench", "a2a", "64m"], env={"OUTPUT_TO_CSV": "1", "NUM_SUB_EXEC": str(cu_count), "GFX_UNROLL": str(unroll)}, stdout=f)



# Function to extract the highest Aggregate bandwidth GPU timed from CSV files
def extract_highest_bandwidth(cu_count, timestamp):
    highest_bandwidth = {}
    for unroll in [1, 2, 4, 6, 8]:
        output_file = f"{timestamp}/{cu_count}CU/a2a_64m_unroll{unroll}.csv"
        try:
            with open(output_file, 'r') as file:
                for line in file:
                    if "Aggregate bandwidth (GPU Timed):" in line:
                        value = float(re.search(r"Aggregate bandwidth \(GPU Timed\):\s+(\d+\.\d+)", line).group(1))
                        highest_bandwidth[unroll] = value
                        break
        except Exception as e:
            print(f"Error reading {output_file}: {e}")
            highest_bandwidth[unroll] = None
    return highest_bandwidth




# Extract the minimum and maximum bandwidth for each CU count
def extract_min_max_bandwidth(cu_count, unroll, timestamp):
    output_file = f"{timestamp}/{cu_count}CU/a2a_64m_unroll{unroll}.csv"
    try:
        with open(output_file, 'r') as file:
            for line in file:
                if "RTotal" in line:
                    values = re.findall(r"\d+\.\d+", line)
                    min_bandwidth = float(values[-2])
                    max_bandwidth = float(values[-1])
                    return min_bandwidth, max_bandwidth
    except Exception as e:
        print(f"Error reading {output_file}: {e}")
        return None, None






def main():

    # Get the current date and time in the format HH-MM-SS_YYYY-mm-dd-heatmap-TB
    timestamp = datetime.now().strftime("%H-%M-%S_%Y-%m-%d-heatmap-TB")

    # Run benchmarks for 2, 4, 6, 8, and 10 CU
    for cu in [2, 4, 6, 8, 10]:
        run_benchmarks(cu, timestamp)


    # Create a dictionary to store the highest bandwidth for each CU and unroll combo
    data = {}
    for cu in [2, 4, 6, 8, 10]:
        data[cu] = extract_highest_bandwidth(cu, timestamp)

    # Convert the dictionary to a DataFrame and transpose it to flip rows and columns
    df = pd.DataFrame(data).transpose()

    # Convert all columns to numeric
    df = df.apply(pd.to_numeric, errors='coerce')

    # create a table with the best bandwidth and unroll per CU count
    best_bandwidth = df.idxmax(axis=1).to_frame(name='Best Unroll')
    best_bandwidth['Best Bandwidth (GB/s)'] = df.max(axis=1)

    min_max_bandwidth = {}
    for cu in best_bandwidth.index:
        best_unroll = best_bandwidth.loc[cu, 'Best Unroll']
        min_bandwidth, max_bandwidth = extract_min_max_bandwidth(cu, best_unroll, timestamp)
        min_max_bandwidth[cu] = (min_bandwidth, max_bandwidth)

    # Convert the dictionary to a DataFrame
    min_max_bandwidth_df = pd.DataFrame.from_dict(min_max_bandwidth, orient='index', columns=['Min Bandwidth (GB/s)', 'Max Bandwidth (GB/s)'])

    # Combine the two tables
    combined_df = best_bandwidth.join(min_max_bandwidth_df)

    # Print the combined table
    print(combined_df)

    # Adjust the color map to focus on the range between 2300 and 2700
    norm = Normalize(vmin=2300, vmax=2700)

    # Create a heatmap with red to green color gradient
    plt.figure(figsize=(10, 6))
    sns.heatmap(df, annot=True, cmap="RdYlGn", cbar_kws={'label': 'Bandwidth (GB/s)'}, mask=df.isnull(), fmt=".3f", norm=norm)
    plt.title('Highest Aggregate Bandwidth GPU Timed')
    plt.xlabel('Unroll')
    plt.ylabel('CU Count')
    plt.savefig("heatmap.png")


    # Save the combined table to a CSV file with a few empty rows before dumping the heatmap DataFrame
    with open("Bandwidth_per_cu.csv", 'w') as f:
        combined_df.to_csv(f, index_label='CU Count')
        f.write('\n\n\n')  # Add a few empty rows
        df.to_csv(f)

if __name__ == "__main__":
    main()
