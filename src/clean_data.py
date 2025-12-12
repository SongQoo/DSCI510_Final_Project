import pandas as pd
import json
import os
import glob
import zipfile
import re

# ==========================================
# [Setup] Path Configuration & Constants
# ==========================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw')
PROCESSED_DIR = os.path.join(BASE_DIR, 'data', 'processed')

# Analysis Period
START_DATE = '2016-01-01'
END_DATE = '2025-12-31' 

# Create output directory if it doesn't exist
if not os.path.exists(PROCESSED_DIR):
    os.makedirs(PROCESSED_DIR)

# ==========================================
# 1. Source A: CPI Data Cleaning
# ==========================================
def clean_cpi_data():
    """
    Cleans [Source A] CPI JSON data: Flattens structure, renames columns, and calculates YoY(Year-Over-Year) inflation.
    - Assumes raw JSON structure from BLS API.
    - Outputs a DataFrame with CPI levels and YoY inflation rates.
    """
    print("\n[Cleaning] Source A: CPI Data...")
    
    # 1. Load JSON file
    file_path = os.path.join(RAW_DIR, 'source_a_cpi_detailed_raw.json')
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return None

    # 2. Parse Data & Count Raw Records
    all_records = []
    raw_total_count = 0  # Counter for raw data points
    
    # Series ID Map
    series_map = {
        "CUUR0000SA0": "CPI_Total",
        "CUUR0000SAF1": "CPI_Food",
        "CUUR0000SA0E": "CPI_Energy",
        "CUUR0000SAH1": "CPI_Shelter"
    }

    if 'Results' not in raw_data or 'series' not in raw_data['Results']:
        print("Error: Invalid JSON structure.")
        return None

    for series in raw_data['Results']['series']:
        series_id = series['seriesID']
        col_name = series_map.get(series_id, series_id)
        
        # Add the number of data points in this series to the total count
        raw_total_count += len(series['data'])
        
        for item in series['data']:
            year = item['year']
            period = item['period'] 
            value = item['value']
            
            # Filter: Valid months (M01-M12)
            if 'M01' <= period <= 'M12':
                month = period[1:] 
                date_str = f"{year}-{month}-01"
                
                all_records.append({
                    "date": date_str,
                    "type": col_name,
                    "value": float(value)
                })

    # 3. DataFrame Conversion
    df = pd.DataFrame(all_records)
    
    # Pivot
    df_pivot = df.pivot(index='date', columns='type', values='value')
    
    # 4. Index Processing
    df_pivot.index = pd.to_datetime(df_pivot.index)
    df_pivot.sort_index(inplace=True)
    
    # 5. Feature Engineering (YoY %)
    for col in df_pivot.columns:
        df_pivot[f"{col}_YoY"] = df_pivot[col].pct_change(periods=12) * 100

    # 6. Save & Print Stats
    save_path = os.path.join(PROCESSED_DIR, 'clean_cpi.csv')
    df_pivot.to_csv(save_path)
    
    # Print Statistics for Report
    print(f"  -> Raw Data Points Scanned: {raw_total_count}")
    print(f"  -> Processed Dimensions: {df_pivot.shape[0]} Rows x {df_pivot.shape[1]} Columns")
    print(f"  -> Saved cleaned CPI data to {save_path}")
    
    return df_pivot

# ==========================================
# 2. Source B: Energy Data Cleaning
# ==========================================
def clean_energy_data():
    """
    Cleans [Source B] Energy JSON data (List of Lists): Flattens raw table data and resamples to monthly mean.
    - Assumes raw JSON structure as list of lists.
    - Outputs a DataFrame with monthly average prices for Gas, Diesel, and Oil.
    """
    print("\n[Cleaning] Source B: Energy Data...")
    
    files = {
        "Gas_Price": "source_b_energy_gasoline_raw.json",
        "Diesel_Price": "source_b_energy_diesel_raw.json",
        "Oil_Price": "source_b_energy_crude_wti_raw.json"
    }
    
    combined_df = pd.DataFrame()

    for col_name, filename in files.items():
        file_path = os.path.join(RAW_DIR, filename)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_list = json.load(f)
            
            # Check dimensions for reporting
            raw_rows = len(raw_list)
            raw_cols = max([len(row) for row in raw_list]) if raw_list else 0
            print(f"  -> Loaded {filename}: {raw_rows} rows, Max {raw_cols} columns.")
            
        except FileNotFoundError:
            print(f"  -> [Skip] {filename} not found.")
            continue
        except json.JSONDecodeError:
            print(f"  -> [Error] Invalid JSON format in {filename}.")
            continue

        # Parsing raw list of lists
        parsed_data = []
        for row in raw_list:
            if not row or not isinstance(row, list): continue
            
            # Extract Year from the first element (Header)
            header_date = row[0]
            try:
                year_str = str(pd.to_datetime(header_date, errors='coerce').year)
                if year_str == 'nan': continue
            except: continue 

            # Parse data pairs (Date, Price)
            data_pairs = row[1:]
            for i in range(0, len(data_pairs), 2):
                if i+1 >= len(data_pairs): break # Incomplete pair
                
                date_part = data_pairs[i] 
                price_str = data_pairs[i+1] 
                
                if not isinstance(date_part, str) or not isinstance(price_str, str): continue
                if not date_part.strip() or not price_str.strip(): continue
                
                # Construct full date string (YYYY-MM-DD)
                full_date_str = f"{year_str}-{date_part.replace('/', '-')}"
                
                try:
                    val = float(price_str)
                    parsed_data.append({
                        "date": pd.to_datetime(full_date_str, errors='coerce'),
                        col_name: val
                    })
                except ValueError:
                    continue

        df_temp = pd.DataFrame(parsed_data)
        
        if df_temp.empty:
            print(f"  -> [Warning] No valid data extracted for {col_name}.")
            continue
            
        df_temp.dropna(subset=['date'], inplace=True)
        df_temp.set_index('date', inplace=True)
        
        # Resample to Monthly Mean (MS: Month Start)
        df_monthly = df_temp.resample('MS').mean()
        
        print(f"  -> {col_name}: {len(df_monthly)} months extracted.")
        
        if combined_df.empty:
            combined_df = df_monthly
        else:
            combined_df = combined_df.join(df_monthly, how='outer')

    if combined_df.empty:
        print("  -> [Error] Combined Energy DataFrame is empty.")
        return pd.DataFrame()

    # Filter by date range
    combined_df = combined_df[START_DATE:END_DATE]
    combined_df.sort_index(inplace=True)

    # Save intermediate file
    save_path = os.path.join(PROCESSED_DIR, 'clean_energy.csv')
    combined_df.to_csv(save_path)
    print(f"  -> Saved cleaned Energy data to {save_path}")
    
    return combined_df

# ==========================================
# 3. Source C: Labor Data Cleaning
# ==========================================
def clean_labor_data():
    """
    Cleans [Source C] Unemployment CSV data: Melts matrix format (Year x Month) to time-series.
    """
    print("\n[Cleaning] Source C: Labor Market Data (Melting)...")
    
    files = {
        "Unemp_Total": "source_c_unemployment_total_raw.csv",
        "Unemp_Men": "source_c_unemployment_men_raw.csv",
        "Unemp_Women": "source_c_unemployment_women_raw.csv"
    }
    
    month_map = {
        "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04", "May": "05", "Jun": "06",
        "Jul": "07", "Aug": "08", "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"
    }
    
    combined_df = pd.DataFrame()
    raw_total_count = 0  # Counter for raw data points

    for col_name, filename in files.items():
        file_path = os.path.join(RAW_DIR, filename)
        try:
            df_raw = pd.read_csv(file_path)
            # Strip whitespace from column names
            df_raw.columns = [c.strip() for c in df_raw.columns]
            
            # Melt: Transform wide format (Year x Month) to long format (Date-Value)
            # This creates one row per month per year
            df_melted = df_raw.melt(id_vars=["Year"], var_name="Month_Name", value_name="Rate")
            
            # Count raw data points (Total months extracted from the file)
            raw_total_count += len(df_melted)
            
            # Filter valid month names
            df_melted = df_melted[df_melted['Month_Name'].isin(month_map.keys())]
            
            # Construct Date column
            df_melted['Month_Num'] = df_melted['Month_Name'].map(month_map)
            df_melted['date'] = pd.to_datetime(
                df_melted['Year'].astype(str) + "-" + df_melted['Month_Num'] + "-01"
            )
            
            # Select relevant columns and index
            df_clean = df_melted[['date', 'Rate']].sort_values('date').set_index('date')
            df_clean.rename(columns={'Rate': col_name}, inplace=True)
            
            # Convert numeric types
            df_clean[col_name] = pd.to_numeric(df_clean[col_name], errors='coerce')
            
            if combined_df.empty:
                combined_df = df_clean
            else:
                combined_df = combined_df.join(df_clean, how='outer')
                
        except FileNotFoundError:
            print(f"  -> [Skip] {filename} not found.")
            continue
        except Exception as e:
            print(f"  -> [Error] Processing {col_name}: {e}")
            continue

    # Filter by date range
    if not combined_df.empty:
        combined_df = combined_df[START_DATE:END_DATE]
        combined_df.sort_index(inplace=True)
    
        save_path = os.path.join(PROCESSED_DIR, 'clean_unemployment.csv')
        combined_df.to_csv(save_path)
        
        # Print Statistics for Report
        print(f"  -> Raw Data Points Scanned: {raw_total_count}")
        print(f"  -> Processed Dimensions: {combined_df.shape[0]} Rows x {combined_df.shape[1]} Columns")
        print(f"  -> Saved cleaned Labor data to {save_path}")
    else:
        print("  -> [Warning] No labor data extracted.")
    
    return combined_df

# ==========================================
# 4. Source D: News Sentiment Cleaning
# ==========================================
def clean_news_data():
    """
    Cleans [Source D] NYT JSON data: Handles ZIP extraction, text processing, keyword counting, and aggregation.
    - Supports both JSON and ZIP formats.
    - Outputs a DataFrame with monthly keyword counts and total counts.
    """
    print("\n[Cleaning] Source D: News Sentiment (Text Mining)...")
    
    # Locate files (support both JSON and ZIP)
    json_pattern = os.path.join(RAW_DIR, 'source_d_*.json')
    zip_path = os.path.join(RAW_DIR, 'source_d_nyt_text_raw.zip')
    
    json_files = glob.glob(json_pattern)
    
    # Auto-extract ZIP if JSON is missing
    if not json_files:
        if os.path.exists(zip_path):
            print(f"  -> JSON not found, but ZIP exists. Extracting {zip_path}...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(RAW_DIR)
            print("  -> Extraction complete.")
            json_files = glob.glob(json_pattern)
        else:
            print("  -> [Warning] Neither JSON nor ZIP file found for Source D.")
            return pd.DataFrame()
    
    # Load all JSON chunks
    all_articles = []
    for filepath in json_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    all_articles.extend(data)
        except Exception as e:
            print(f"  -> Error reading {filepath}: {e}")
            continue
            
    if not all_articles:
        print("  -> [Warning] News data list is empty.")
        return pd.DataFrame()
    
    df = pd.DataFrame(all_articles)
    
    # Print Raw Dimensions
    print(f"  [Data Check] Raw Dataset Dimensions: {df.shape[0]:,} rows, {len(df.columns)} columns")

    # Date Handling: Check 'pub_date' or 'date'
    df['date'] = pd.to_datetime(df.get('date', df.get('pub_date')), errors='coerce')
    
    # Remove Timezone info for consistency
    if df['date'].dt.tz is not None:
        df['date'] = df['date'].dt.tz_localize(None)

    df.dropna(subset=['date'], inplace=True)
    
    # Filter by analysis period
    df = df[(df['date'] >= START_DATE) & (df['date'] <= END_DATE)]
    
    # Text Cleaning: Combine Headline + Snippet
    df['full_text'] = (
        df['headline'].fillna('') + " " + df['snippet'].fillna('')
    ).str.lower()

    # Keyword Counting
    keywords = ['inflation', 'recession', 'crisis', 'high price', 'layoff', 'unemployment']
    print(f"  -> Counting keywords: {keywords}...")
    
    for kw in keywords:
        col_name = f"News_Count_{kw.title().replace(' ', '_')}"
        df[col_name] = df['full_text'].str.contains(kw, case=False, regex=False).astype(int)

    # Aggregation: Resample to Monthly Sum
    df.set_index('date', inplace=True)
    news_cols = [col for col in df.columns if 'News_' in col]
    df_monthly = df[news_cols].resample('MS').sum()
    
    # Add Total Counting Column
    df_monthly['News_Total_Counting'] = df_monthly.sum(axis=1)
    
    # Save processed data
    save_path = os.path.join(PROCESSED_DIR, 'clean_news_sentiment.csv')
    df_monthly.to_csv(save_path)
    
    print(f"  -> Saved cleaned Sentiment data to {save_path}")
    print(f"  -> Processed News Data Shape: {df_monthly.shape}")
    return df_monthly

# ==========================================
# 5. Final Integration (Merge All)
# ==========================================
def merge_all_data():
    """
    Integrates all cleaned datasets (CPI, Energy, Labor, News) into a single master CSV.
    - Performs outer joins on Date index.
    - Handles missing values via linear interpolation.
    - Saves final dataset to processed directory.
    """
    print("\n" + "="*50)
    print("[Merging] Integrating All Datasets...")
    print("="*50)
    
    # Execute cleaning functions
    df1 = clean_cpi_data()
    df2 = clean_energy_data()
    df3 = clean_labor_data()
    df4 = clean_news_data()
    
    # Collect non-empty DataFrames
    dfs_to_merge = [d for d in [df1, df2, df3, df4] if not d.empty]
    
    if not dfs_to_merge:
        print("Error: No data available to merge.")
        return

    # Outer Join all datasets based on Date index
    final_df = dfs_to_merge[0]
    for df in dfs_to_merge[1:]:
        final_df = final_df.join(df, how='outer')
    
    # Final Period Filtering
    final_df = final_df[START_DATE:END_DATE]
    
    # Handling Missing Values (Linear Interpolation for time-series)
    final_df.interpolate(method='linear', limit_direction='both', inplace=True)
    
    # Save Final Dataset
    save_path = os.path.join(PROCESSED_DIR, 'final_dataset.csv')
    final_df.to_csv(save_path)
    
    print(f"\n[Success] Final Dataset Saved: {save_path}")
    print(f" - Shape: {final_df.shape}")
    print(f" - Time Range: {final_df.index.min().date()} to {final_df.index.max().date()}")
    print("\n[Preview]")
    print(final_df.tail())

# ==========================================
# Main Execution Flow
# ==========================================
if __name__ == "__main__":
    merge_all_data()