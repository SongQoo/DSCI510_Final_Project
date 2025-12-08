# **Analyzing the Interplay of Energy Costs, Inflation, and Labor Market Shocks (2016-2025)**
### **(Energy Costs $\rightarrow$ Inflation $\rightarrow$ Labor Market $\rightarrow$ Media Sentiment)**

This project investigates the lead-lag relationships and causal chains between supply-side energy shocks, consumer inflation, labor market contractions, and public media sentiment over the last decade (2016–2025).

As described in the final report, this study integrates multi-source data to visualize how supply shocks translate into consumer pain and eventually reflect in public sentiment.

---

## **0. Name & Team Members**


---

1.  **Name:** Junhyeon Song
2.  **USC Email:** songjunh@usc.edu
3.  **USC ID:** 8467-4177-80
4.  **GitHub Repository:** https://github.com/SongQoo/DSCI510_Final_Project
---

## **1. Installation**

To set up the environment for this project, please follow these steps:

1.  **Clone the repository** to your local machine.
2.  **Install the required Python packages.** This project relies on standard data science libraries and web scraping tools.

```bash
pip install pandas numpy scipy matplotlib seaborn requests beautifulsoup4
```

> **Note:** The project was developed using Python 3.9+.

---

## **2. Project Structure**

The project is organized into modular directories to separate source code, raw data, and final visualizations.

```bash
├── data/
│   ├── raw/                                 # Raw Data collected via `get_data.py`
│   │   ├── source_a_cpi_detailed_raw.json        # BLS API: CPI metrics (Food, Energy, Shelter)
│   │   ├── source_b_energy_gasoline_raw.json     # EIA Scraping: Weekly Gasoline Prices
│   │   ├── source_b_energy_diesel_raw.json       # EIA Scraping: Weekly Diesel Prices
│   │   ├── source_b_energy_crude_wti_raw.json    # EIA Scraping: Weekly WTI Crude Oil Prices
│   │   ├── source_c_unemployment_total_raw.csv   # BLS Scraping: Total Unemployment Rate
│   │   ├── source_c_unemployment_men_raw.csv     # BLS Scraping: Men's Unemployment Rate
│   │   ├── source_c_unemployment_women_raw.csv   # BLS Scraping: Women's Unemployment Rate
│   │   ├── source_d_nyt_text_raw.zip             # NYT Archive: Historical Data (>100MB, Unzip or use .zip-the code will unzip automatically)
│   │   └── source_d_nyt_recent_raw.json          # NYT Search: Recent Data (3-Day Batch Sampling)
│   │
│   └── processed/                           # Final Data generated via `clean_data.py`
│   │   ├── clean_cpi.csv                    # CPI metrics (Food, Energy, Shelter)
│   │   ├── clean_energy.csv                 # Energy metrics (Gas, Diesel, Oil)
│   │   ├── clean_unemployment.csv           # Unemployment metrics (Total, Men, Women)
│   │   ├── clean_news_sentiment.csv         # News sentiment metrics (Counting of pre-defined keywords)
│       └── final_dataset.csv                # Unified Time-Series Dataset (Master File)
│
├── results/
│   ├── visualization.ipynb  # Main Jupyter Notebook for generating plots
│   ├── final_report.pdf
│   └── ...                  # Saved figures (e.g., .png files)
│
├── src/
│   ├── get_data.py          # Data collection script (APIs & Scraping)
│   ├── clean_data.py        # Data cleaning & Feature engineering script
│   ├── run_analysis.py      # Statistical & Causal analysis logic
│   └── visualize_results.py # Visualization functions library (imported by Notebook)
│
├── requirements.txt         # Python dependencies list
└── README.md                # Project documentation
└── project_proposal.pdf     # Project Proposal
```

### **Critical Note on Visualization**
* **`src/visualize_results.py`**: This file contains the *definitions* of all plotting functions. It is a library, not a standalone script.
* **`results/visualization.ipynb`**: This is the *execution* file. It imports the functions from `src` and renders the charts interactively. **You must run this notebook to view the visual results.**

---

## **3. How to Get Data**

To collect the raw data from scratch, execute the following script:

```bash
python src/get_data.py
```

This script aggregates data from four distinct sources as detailed in the final report:

1.  **Source A (BLS API):** Fetches detailed CPI metrics (All Items, Food, Energy, Shelter) via JSON parsing.
2.  **Source B (EIA Scraping):**
    * **Source:** U.S. Energy Information Administration (EIA).
    * **Method:** Scrapes HTML tables using `BeautifulSoup`. The raw data consists of **weekly** price lists (Gasoline, Diesel, WTI). The script parses these tables and performs **temporal resampling** (Weekly $\rightarrow$ Monthly) to align with other economic indicators.
3.  **Source C (Labor Market Scraping):**
    * **Source:** BLS Data Viewer.
    * **Method:** Scrapes HTML tables using `BeautifulSoup`. Since the raw data exists in a **"Wide Matrix"** format (Years × Months), the script scrapes these tables and saves them for reshaping (melting) in the cleaning phase.
4.  **Source D (NYT Public Sentiment):**
    * **Method:** Implements a **Hybrid Approach** to overcome API limitations.
        * **Archive API:** Used for historical data (2016–May 2025). *Note: The raw file is provided as a ZIP due to size (>100MB).*
        * **Article Search API:** Used for recent data (June 2025–Dec 2025) with a **"3-Day Batch Sampling"** strategy (Top 20 relevant articles per batch) to adhere to rate limits while maintaining trend accuracy.

> **Execution Warning:** Due to API rate limiting (6s delay per request) and the hybrid sampling strategy, full data collection may take **20–30 minutes**. Please be patient.

---

## **4. How to Clean Data**

After collecting the raw data, run the cleaning script to process it into a unified time-series format:

```bash
python src/clean_data.py
```

**Key Processing Steps:**
* **Standardization:** Converts weekly (Energy) and daily (News) data into a uniform monthly frequency.
* **Reshaping:** Performs **Melting** on Source C (Labor) data to transform wide-format tables into clean time-series data.
* **Feature Engineering:** Calculates Year-over-Year (YoY) percentage changes for all CPI metrics.
* **Text Mining (Fear Index):** Parses NYT articles to count the frequency of specific economic fear keywords identified in the report:
    * *Keywords:* `'Inflation'`, `'Recession'`, `'Crisis'`, `'High price'`, `'Layoff'`, `'Unemployment'`.
* **Integration:** Merges all sources into a single master file: `data/processed/final_dataset.csv`.

---

## **5. How to Run Analysis**

To perform the statistical tests and verify the hypotheses presented in the report, run:

```bash
python src/run_analysis.py
```

This script outputs the following insights to the console:
* **Descriptive Statistics:** Volatility (CV) and Skewness of key indicators.
* **Lead-Lag Analysis:** Correlation coefficients at different time lags (0–6 months) to trace the shock transmission.
* **Structural Break Test:** Compares correlations Pre-2020 vs. Post-2020 to identify regime shifts.
* **Labor Market Analysis:** Calculates the "Gender Gap" and validates the Inflation-Unemployment Trade-off.

---

## **6. How to Produce Visualizations**

The final visualizations included in the report are generated using a Jupyter Notebook.

1.  Navigate to the `results/` directory.
2.  Open **`visualization.ipynb`**.
3.  Run all cells sequentially.

The notebook calls functions from `src/visualize_results.py` to generate the following figures:
* **[Analysis 1] Economic Dashboard:** Visualizes Volatility (Sticky vs. Flexible) and Asymmetry.
* **[Analysis 2] Supply Chain Impact:** Dual-Axis Plot showing the link between Diesel Prices and Food CPI.
* **[Analysis 3] Labor Market Analysis:**
    * **Inflation vs. Unemployment:** Scatter plot showing the Inflation-Unemployment trade-off.
    * **Gender Gap:** Time-series highlighting the Gender Gap (Female vs. Male unemployment).
* **[Analysis 4] Structural Change:** Rolling correlation analysis between Energy Prices and CPI Inflation to detect regime shifts (Pre-2020 vs. Post-2020).
* **[Analysis 5] Economic Sensitivity:** Regression analysis (Oil Price vs. Inflation).
* **[Analysis 6] Causal Chain:** Heatmap & Lead-Lag analysis proving Media Sentiment is a coincident indicator.

> **Note:** Ensure that `final_dataset.csv` exists in the `data/processed/` folder before running the notebook.