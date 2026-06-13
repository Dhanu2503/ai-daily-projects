=# Project X Data Processor

## Overview

Project X Data Processor is a versatile command-line tool designed to streamline the process of loading, cleaning, analyzing, and visualizing data from various sources, primarily CSV files. It aims to provide a quick and automated way to generate insights and reports, making data exploration more efficient for analysts, researchers, and developers.

## Features

*   **Data Loading:** Efficiently loads data from CSV files into a structured format for processing.
*   **Data Cleaning:**
    *   Handles missing values (e.g., imputation with mean/median, row/column removal).
    *   Identifies and removes duplicate records.
    *   Supports basic data type conversions.
*   **Statistical Analysis:**
    *   Generates descriptive statistics (mean, median, mode, standard deviation, variance, quartiles).
    *   Calculates correlations between numerical features.
*   **Data Visualization:**
    *   Creates common plots such as histograms, box plots, scatter plots, and bar charts.
    *   Allows customization of plot types and features.
*   **Report Generation:**
    *   Compiles analysis results and visualizations into comprehensive PDF reports.
    *   Includes summary statistics, key findings, and generated plots.
*   **Extensible Architecture:** Designed to be easily extendable with new data sources, cleaning methods, and analysis techniques.

## Installation

To get Project X Data Processor up and running, follow these steps:

1.  **Prerequisites:**
    *   Python 3.8+
    *   `pip` (Python package installer)

2.  **Clone the Repository:**
    ```bash
    git clone https://github.com/your-username/project-x-data-processor.git
    cd project-x-data-processor
    ```

3.  **Create a Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: .\venv\Scripts\activate
    ```

4.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

    The `requirements.txt` file typically contains:
    ```
    pandas>=1.3.0
    numpy>=1.21.0
    matplotlib>=3.4.0
    seaborn>=0.11.0
    fpdf2>=2.5.0 # For PDF report generation
    ```

## Usage

The Project X Data Processor is operated via a command-line interface.

### Basic Analysis

To perform a basic analysis and generate a report from a CSV file:

```bash
python src/main.py analyze <input_csv_file> --output <output_report_name.pdf>
```

**Example:**

```bash
python src/main.py analyze data/sample_data.csv --output reports/sample_analysis_report.pdf
```

### Options

*   `-i`, `--input`: Path to the input CSV file. (Required)
*   `-o`, `--output`: Path and filename for the output PDF report. (Optional, defaults to `report.pdf`)
*   `--clean-strategy`: Strategy for handling missing values. Options: `remove-rows`, `mean-impute`, `median-impute`. (Default: `remove-rows`)
*   `--no-duplicates`: Flag to remove duplicate rows. (Optional)
*   `--plot`: Specify types of plots to include. Options: `histograms`, `scatterplots`, `boxplots`. Can be comma-separated. (Default: all numerical plots)
*   `--target-column`: Specify a column to use as a target for specific analyses (e.g., scatter plots against target). (Optional)

**More Advanced Example:**

Analyze `sales_data.csv`, impute missing values with the median, remove duplicates, generate histograms and scatter plots, and save the report as `sales_report.pdf`.

```bash
python src/main.py analyze data/sales_data.csv \
    --output reports/sales_report.pdf \
    --clean-strategy median-impute \
    --no-duplicates \
    --plot histograms,scatterplots \
    --target-column Revenue
```

### Help

To view the full list of commands and options:

```bash
python src/main.py --help
python src/main.py analyze --help
```

## Output

The primary output of Project X Data Processor is a comprehensive PDF report.

**The report typically includes:**

1.  **Project Title and Date:** Identifying information for the report.
2.  **Overview of Input Data:** Basic information like number of rows, columns, and data types.
3.  **Data Cleaning Summary:** Details on how missing values were handled and if duplicates were removed.
4.  **Descriptive Statistics:** A table showing summary statistics (mean, median, std dev, min, max, quartiles) for all numerical columns.
5.  **Correlation Matrix:** A heatmap or table illustrating the correlation between numerical features.
6.  **Visualizations:**
    *   **Histograms:** For numerical columns to show data distribution.
    *   **Box Plots:** For numerical columns to identify outliers and distribution spread.
    *   **Scatter Plots:** For pairs of numerical columns (or against a target column if specified) to show relationships.
7.  **Key Findings/Insights:** (Automated or space for manual notes if extended)

**Example Snippet from a Report:**

```
--------------------------------------------------
Project X Data Analysis Report
Date: 2023-10-27
Input File: sample_data.csv
--------------------------------------------------

1. Data Overview
   - Rows: 1000
   - Columns: 5
   - Features: ['ID', 'Age', 'Income', 'Product_Category', 'Purchase_Amount']

2. Data Cleaning Summary
   - Missing values handled using 'median-impute' strategy.
   - Duplicates removed: 5 records.

3. Descriptive Statistics (Numerical Columns)

| Column          | Count | Mean     | Std Dev  | Min   | 25%   | 50%    | 75%   | Max     |
|-----------------|-------|----------|----------|-------|-------|--------|-------|---------|
| Age             | 1000  | 35.2     | 10.5     | 18.0  | 27.0  | 34.0   | 43.0  | 60.0    |
| Income          | 1000  | 75000.50 | 20000.75 | 30000 | 60000 | 75000  | 90000 | 120000  |
| Purchase_Amount | 1000  | 150.75   | 50.20    | 20.0  | 110.0 | 155.0  | 190.0 | 250.0   |

... (Visualizations follow) ...
```

## Future Improvements

*   **Support for Additional File Formats:** Extend data loading capabilities to include Excel (`.xlsx`), JSON (`.json`), and SQL databases.
*   **Advanced Analytics:** Integrate more sophisticated statistical tests (e.g., t-tests, ANOVA), clustering algorithms (k-means), and regression models.
*   **Interactive Web Interface:** Develop a user-friendly web application (e.g., using Flask/Django or Streamlit) for easier interaction and real-time visualization.
*   **Customizable Plotting:** Allow users to define custom plot aesthetics, titles, and labels directly via command-line arguments or configuration files.
*   **Machine Learning Integration:** Add functionalities for basic feature engineering, model training (e.g., scikit-learn), and performance evaluation.
*   **Automated Anomaly Detection:** Implement algorithms to automatically flag unusual data points or patterns.
*   **Configuration Files:** Allow users to save analysis preferences and plotting options in `.yaml` or `.json` configuration files for reproducible runs.