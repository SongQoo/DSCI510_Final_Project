import os
import time
import json
import requests
import pandas as pd
from bs4 import BeautifulSoup
from io import StringIO
import datetime

# ==========================================
# [Setup] File Storage Path
# ==========================================
# Set BASE_DIR for .py execution (Current file's parent of parent directory)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_RAW_DIR = os.path.join(BASE_DIR, 'data', 'raw')

# Create output directory if it doesn't exist
if not os.path.exists(DATA_RAW_DIR):
    os.makedirs(DATA_RAW_DIR)

# ==========================================
# Source A: Inflation Metrics (BLS API)
# ==========================================
def get_source_a_inflation():
    """
    [Source A] BLS API: Collect Detailed Inflation Indicators
    - All Items, Food, Energy, Shelter(Real Estate)
    - Saves raw JSON response for further processing in clean_data.py
    """
    print("\n[Source A] Fetching Detailed Inflation Data (BLS API)...")
    headers = {'Content-type': 'application/json'}
    series_ids = ["CUUR0000SA0", "CUUR0000SAF1", "CUUR0000SA0E", "CUUR0000SAH1"]
    
    payload = json.dumps({
        "seriesid": series_ids, 
        "startyear": "2016", 
        "endyear": "2025"
    })
    
    try:
        response = requests.post('https://api.bls.gov/publicAPI/v2/timeseries/data/', data=payload, headers=headers)
        response.raise_for_status()
        
        save_path = os.path.join(DATA_RAW_DIR, 'source_a_cpi_detailed_raw.json')
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(response.json(), f, indent=4)
        print(f" -> Saved detailed JSON to: {save_path}")
    except Exception as e:
        print(f" -> Error in Source A: {e}")

# ======================================================
# Source B: Energy Costs (Web Scraping - BeautifulSoup)
# ======================================================
def get_source_b_energy():
    """
    [Source B] EIA.gov Energy Prices
    - Scrapes all text data from the table as-is and saves it as JSON.
    (Structuring and averaging will be done in clean_data.py)
    - Collects Gasoline, Diesel, and Crude Oil (WTI) Weekly Prices
    """
    print("\n[Source B] Scraping Raw Energy Tables (EIA.gov)...")
    
    # 3 Indicators
    energy_urls = {
        "Gasoline": "https://www.eia.gov/dnav/pet/hist/LeafHandler.ashx?n=PET&s=EMM_EPMR_PTE_NUS_DPG&f=W",
        "Diesel":   "https://www.eia.gov/dnav/pet/hist/LeafHandler.ashx?n=PET&s=EMD_EPD2D_PTE_NUS_DPG&f=W",
        "Crude_WTI": "https://www.eia.gov/dnav/pet/hist/LeafHandler.ashx?n=PET&s=RWTC&f=W"
    }
    
    headers = {"User-Agent": "Mozilla/5.0"}

    for name, url in energy_urls.items():
        print(f" -> Fetching {name}...", end=" ")
        try:
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Find data table
            all_tables = soup.find_all("table")
            if not all_tables:
                print("No tables found.")
                continue
                
            # The table with the most rows is the data table
            target_table = max(all_tables, key=lambda t: len(t.find_all("tr")))
            rows = target_table.find_all("tr")
            
            # Save all cell text as-is (Raw List of Lists)
            raw_table_data = []
            for row in rows:
                cols = row.find_all("td")
                if not cols: continue # Skip header rows
                
                # Convert cell text to list (remove whitespace)
                # Example: ['Oct-2023', '10/02', '3.801', '10/09', '3.750', ...]
                col_texts = [c.text.strip() for c in cols if c.text.strip()]
                
                if col_texts:
                    raw_table_data.append(col_texts)
            
            # Save as JSON (Suitable for variable length data)
            filename = f"source_b_energy_{name.lower()}_raw.json"
            save_path = os.path.join(DATA_RAW_DIR, filename)
            
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(raw_table_data, f, indent=4)
                
            print(f"Saved {len(raw_table_data)} rows (Raw JSON).")
            
            time.sleep(1) # Prevent server overload
            
        except Exception as e:
            print(f"Error: {e}")

# ==========================================================
# Source C: Labor Market (Web Scraping - BeautifulSoup Fixed)
# ==========================================================
def get_source_c_labor():
    """
    [Source C] BLS Data Viewer: Collect Unemployment Rates
    - Fixed: Correctly identifies headers by looking only at the first row.
    - Fixed: Handles row validation more robustly (ignores footnotes like '(p)').
    """
    print("\n[Source C] Scraping Detailed Labor Market Data (BLS HTML)...")
    
    urls = {
        "Total": "https://data.bls.gov/timeseries/LNS14000000",
        "Men":   "https://data.bls.gov/timeseries/LNS14000001",
        "Women": "https://data.bls.gov/timeseries/LNS14000002"
    }
    
    headers = {"User-Agent": "Mozilla/5.0"}
    
    for category, url in urls.items():
        try:
            print(f" -> Scraping {category} Unemployment...", end=" ")
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Find the correct table (contains 'Year' and 'Jan')
            target_table = None
            all_tables = soup.find_all("table")
            
            for table in all_tables:
                # Check just the first row or thead for headers
                first_row = table.find("tr")
                if not first_row: continue
                
                # Extract text from first row to check signature
                first_row_text = [c.get_text().strip().lower() for c in first_row.find_all(["th", "td"])]
                
                if 'year' in first_row_text and 'jan' in first_row_text:
                    target_table = table
                    break
            
            if target_table:
                # 1. Parse Headers (Only from the first row)
                # Use the first row we found above
                headers_row = target_table.find("tr")
                headers_list = [c.get_text().strip() for c in headers_row.find_all(["th", "td"]) if c.get_text().strip()]
                
                # 2. Parse Rows
                rows_data = []
                # Skip the first row (headers) and iterate the rest
                for tr in target_table.find_all("tr")[1:]:
                    cells = tr.find_all(["td", "th"])
                    row_text = [cell.get_text().strip() for cell in cells]
                    
                    # Validate row:
                    # - Must have data
                    # - First column must look like a year (start with 4 digits)
                    # - Length should be reasonably close to header length (allow small mismatch due to hidden cols)
                    if row_text and len(row_text) >= 12 and row_text[0][:4].isdigit():
                        # Truncate or pad to match header length if necessary, or just take what we have
                        # Usually BLS has Year + 12 Months + Annual (14 cols)
                        rows_data.append(row_text)
                
                # 3. Convert to DataFrame & Save
                if rows_data:
                    # Ensure columns align. Use headers_list, but if rows have fewer cols, slice headers.
                    max_cols = max(len(r) for r in rows_data)
                    final_headers = headers_list[:max_cols]
                    
                    # Create DF with normalized columns
                    df = pd.DataFrame([r[:max_cols] for r in rows_data], columns=final_headers)
                    
                    filename = f'source_c_unemployment_{category.lower()}_raw.csv'
                    save_path = os.path.join(DATA_RAW_DIR, filename)
                    df.to_csv(save_path, index=False)
                    print(f"Saved {len(df)} years of data.")
                else:
                    print("Empty data extracted (Rows validation failed).")
            else:
                print("Target table not found.")
            
            time.sleep(1)
            
        except Exception as e:
            print(f"Error: {e}")
            

# ==========================================
# Source D: Public Sentiment (NYT API)
# ==========================================
def get_source_d_sentiment(api_key):
    """
    [Source D] NYT API: Collect Raw Text
    - Uses Archive API (2016-Present).
    """
    print("\n[Source D] Fetching Public Sentiment Data (NYT API)...")
    
    if not api_key or api_key == "MY_KEY":
        print(" -> [Error] API Key missing.")
        return

    base_url = "https://api.nytimes.com/svc/archive/v1/{}/{}.json"
    all_articles = []
    
    headers = {"User-Agent": "Mozilla/5.0"}

    now = datetime.datetime.now()
    current_year = now.year
    current_month = now.month

    for year in range(2016, current_year + 1):
        for month in range(1, 13):
            if year > current_year or (year == current_year and month > current_month):
                print(f" -> Reached future date ({year}-{month:02d}). Stopping.")
                return # Stop entire function if future reached

            # Keep trying the CURRENT month until success or fatal error
            while True:
                print(f" -> Fetching {year}-{month:02d}...", end=" ")
                
                url = base_url.format(year, month)
                params = {'api-key': api_key}
                
                try:
                    resp = requests.get(url, params=params, headers=headers)
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        docs = data.get('response', {}).get('docs', [])
                        for doc in docs:
                            all_articles.append({
                                "date": doc.get("pub_date"),
                                "headline": doc.get("headline", {}).get("main"),
                                "snippet": doc.get("snippet"),
                                "lead_paragraph": doc.get("lead_paragraph")
                            })
                        print(f"OK ({len(docs)} docs)")
                        time.sleep(6) 
                        break # Success: Exit while loop, move to next month
                        
                    elif resp.status_code == 429:
                        print("\n    [Wait] Rate limit hit. Sleeping 30s...", end=" ")
                        time.sleep(30)
                        print("Retrying...")
                        continue # Retry the SAME month
                        
                    elif resp.status_code == 403:
                        print(f"\n    [Stop] 403 Forbidden. Assuming end of archive.")
                        # Save what I have and exit
                        if all_articles:
                            save_path = os.path.join(DATA_RAW_DIR, 'source_d_nyt_text_raw.json')
                            with open(save_path, 'w', encoding='utf-8') as f:
                                json.dump(all_articles, f, indent=4)
                            print(f" -> Saved {len(all_articles)} articles.")
                        return # Exit function completely
                        
                    else:
                        print(f"Failed ({resp.status_code})")
                        break # Skip this month on unknown error
                
                except Exception as e:
                    print(f"Error: {e}")
                    time.sleep(5)
                    break # Skip month on connection error

    # Final Save
    if all_articles:
        save_path = os.path.join(DATA_RAW_DIR, 'source_d_nyt_text_raw.json')
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(all_articles, f, indent=4)
        print(f"\n -> Saved {len(all_articles)} raw articles to: {save_path}")

# ==========================================
# [Source D - Extension] Recent Data (High Volume + Retry Logic)
# ==========================================
def get_source_d_sentiment_recent(api_key, start_str="20250601", end_str="20251201"):
    """
    [Source D - Extension] NYT API: Recent Data Collection
    - Strategy: 3-Day Batch + Pagination (Top 20 articles).
    - Mode: Raw Mode (No filters) to ensure data retrieval.
    """
    print(f"\n[Source D-Extension] Fetching Recent Data ({start_str}-{end_str}) [Top 20/Batch]...")
    
    base_url = "https://api.nytimes.com/svc/search/v2/articlesearch.json"
    headers = {"User-Agent": "Mozilla/5.0"}
    all_articles = []

    start_date = datetime.datetime.strptime(start_str, "%Y%m%d")
    end_date = datetime.datetime.strptime(end_str, "%Y%m%d")
    
    current_date = start_date
    BATCH_SIZE = 3 
    MAX_PAGES = 2  # Fetch Page 0 and Page 1 (Total 20 articles per batch)

    while current_date <= end_date:
        # Define 3-day window
        batch_end = current_date + datetime.timedelta(days=BATCH_SIZE - 1)
        if batch_end > end_date:
            batch_end = end_date
            
        d_start = current_date.strftime("%Y%m%d")
        d_end = batch_end.strftime("%Y%m%d")
        
        print(f" -> Fetching {d_start}~{d_end}...", end=" ")
        
        # Loop through pages (0, 1)
        for page in range(MAX_PAGES): 
            # Retry Loop: Keep trying this specific page if Rate Limited
            while True:
                params = {
                    'api-key': api_key,
                    'begin_date': d_start,
                    'end_date': d_end,
                    'page': page,
                    'sort': 'relevance'
                    # No 'q' or 'fq' filters to guarantee data retrieval
                }
                
                try:
                    resp = requests.get(base_url, params=params, headers=headers)
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        docs = data.get('response', {}).get('docs', [])
                        
                        if docs:
                            for doc in docs:
                                all_articles.append({
                                    "date": doc.get("pub_date"),
                                    "headline": doc.get("headline", {}).get("main"),
                                    "snippet": doc.get("snippet"),
                                    "lead_paragraph": doc.get("lead_paragraph"),
                                    "section_name": doc.get("section_name") # Saved for filtering later
                                })
                            print(f"[P{page}: {len(docs)}]", end=" ")
                        else:
                            print(f"[P{page}: Empty]", end=" ")
                        
                        time.sleep(6)
                        break 
                        
                    elif resp.status_code == 429:
                        print(" [Rate Limit! Wait 30s...]", end="")
                        time.sleep(30)
                        continue 
                    
                    else:
                        print(f" [Err {resp.status_code}] ", end="")
                        # For other errors (400, 500), break retry to avoid infinite loop
                        break
                        
                except Exception as e:
                    print(f" [Ex: {e}] ", end="")
                    time.sleep(5)
                    break # Break retry on connection error
        
        print("Done.")
        current_date += datetime.timedelta(days=BATCH_SIZE)

    # Final Save
    if all_articles:
        save_path = os.path.join(DATA_RAW_DIR, 'source_d_nyt_recent_raw.json')
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(all_articles, f, indent=4)
        print(f"\n -> Saved {len(all_articles)} articles to: {save_path}")
    else:
        print("\n -> No articles collected.")

# ==========================================
# Main Execution
# ==========================================
if __name__ == "__main__":
    print("=== Starting Multi-Source Data Collection ===")
    
    # API Key Input for NYT
    MY_NYT_KEY = "6Ho7p6hQd2AnJHZQnddUyWGR3pCX8mAt"
    
    # 1. CPI (All, Food, Energy, Shelter)
    get_source_a_inflation()
    
    # 2. Energy (Gasoline, Diesel, Crude Oil)
    get_source_b_energy()
    
    # 3. Unemployment (Total, Men, Women)
    get_source_c_labor()
    
    # 4. News Text (Original Text)
    get_source_d_sentiment(MY_NYT_KEY)
    get_source_d_sentiment_recent(MY_NYT_KEY)
    
    print("\n=== Data Collection Complete ===")