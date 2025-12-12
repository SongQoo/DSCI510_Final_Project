import pandas as pd
import numpy as np
import os
from scipy import stats

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED_DIR = os.path.join(BASE_DIR, 'data', 'processed')

def load_data():
    """
    Load the final merged dataset (final_dataset.csv).
    Returns: DataFrame or None if file not found.
    """
    file_path = os.path.join(PROCESSED_DIR, 'final_dataset.csv')
    if not os.path.exists(file_path):
        print(f"[Error] File not found: {file_path}")
        print("-> Please run 'src/clean_data.py' to generate the dataset.")
        return None
    
    print(f"Loading data from: {file_path}")
    return pd.read_csv(file_path, index_col='date', parse_dates=True)

# ==========================================
# [Analysis 1] Basic & Advanced Statistics
# ==========================================
def analyze_basic_stats(df):
    """
    Generate descriptive statistics including advanced metrics (Skewness, CV(Coefficient of Variation)).
    """
    print("\n" + "="*80)
    print("[1. Basic & Advanced Statistics] Comprehensive Overview")
    print("="*80)
    
    # Define target columns (Ensure they exist in df)
    target_cols = [
        'Gas_Price', 'Diesel_Price', 'Oil_Price',
        'CPI_Total_YoY', 'CPI_Food_YoY', 'CPI_Energy_YoY', 'CPI_Shelter_YoY',
        'Unemp_Total', 'Unemp_Men', 'Unemp_Women',
        'News_Total_Counting', 'News_Count_Recession', 'News_Count_Layoff', 'News_Count_Crisis', 'News_Count_HighPrice', 'News_Count_Unemployment'
    ]
    cols = [c for c in target_cols if c in df.columns]
    
    if not cols:
        print("No target columns found in the dataset.")
        return

    # Basic stats
    stats_df = df[cols].describe().T
    
    # Advanced metrics
    stats_df['skew'] = df[cols].skew()
    stats_df['Volatility (CV)'] = stats_df['std'] / stats_df['mean']
    
    # Formatting
    stats_df.rename(columns={'50%': 'median'}, inplace=True)
    display_cols = ['mean', 'median', 'min', 'max', 'std', 'skew', 'Volatility (CV)']
    
    print(stats_df[display_cols].round(3))
    return stats_df

# ===================================================================================
# [Analysis 2] Sector Impact (Supply Chain: Energy(Diesel) - Inflation(Food Prices))
# ===================================================================================
def analyze_supply_chain_impact(df):
    """
    Analyze correlation and lag effects between Diesel Prices and Food CPI.
    """
    print("\n" + "="*80)
    print("[2. Supply Chain Analysis] Diesel Cost vs Food Prices")
    print("="*80)
    
    if 'Diesel_Price' in df.columns and 'CPI_Food_YoY' in df.columns:
        corr = df['Diesel_Price'].corr(df['CPI_Food_YoY'])
        print(f"Correlation (Diesel Price <-> Food CPI YoY): {corr:.4f}")
        
        print("-> Checking Lag Effects (Diesel leads Food CPI):")
        for lag in [1, 2, 3]:
            # Leader(t) vs Follower(t+lag) -> Shift follower backwards
            # Or Shift leader forward (Diesel_t vs Food_t+lag)
            # Correct logic: df[Leader].shift(lag).corr(df[Follower])
            lag_corr = df['Diesel_Price'].shift(lag).corr(df['CPI_Food_YoY'])
            print(f"   - Lag {lag} month(s): {lag_corr:.4f}")
    else:
        print("Missing columns for Supply Chain Analysis.")

# ==============================================
# [Analysis 3] Labor Market (Labor - Inflation)
# ==============================================
def analyze_labor_market(df):
    """
    Analyze the trade-off between Unemployment and Inflation.
    """
    print("\n" + "="*80)
    print("[3-1. Laber Market] Inflation vs Unemployment")
    print("="*80)
    
    if 'Unemp_Total' in df.columns and 'CPI_Total_YoY' in df.columns:
        # Calculate correlation
        corr = df['Unemp_Total'].corr(df['CPI_Total_YoY'])
        print(f"Correlation (Unemployment <-> Inflation): {corr:.4f}")
        
        if corr < -0.3:
            print("-> Conclusion: Validates Negative Trade-off.")
        else:
            print("-> Conclusion: Weak or No relationship observed.")
    else:
        print("Missing columns for Analysis.")
        
def analyze_gender_gap(df):
    """
    Analyze gender asymmetry in unemployment rates.
    """
    print("\n" + "="*80)
    print("[3-2. Labor Market Asymmetry] Gender Gap (Women - Men)")
    print("="*80)
    
    if 'Unemp_Women' in df.columns and 'Unemp_Men' in df.columns:
        df['Gender_Gap'] = df['Unemp_Women'] - df['Unemp_Men']
        
        mean_gap = df['Gender_Gap'].mean()
        max_gap = df['Gender_Gap'].max()
        max_date = df['Gender_Gap'].idxmax().date()
        
        print(f"Average Gap (2016-2025): {mean_gap:.3f}%p")
        print(f"Max Gap (Women > Men): {max_gap:.3f}%p occurred on {max_date}")
        
        # COVID Peak Check
        if pd.Timestamp('2020-04-01') in df.index:
            covid_gap = df.loc['2020-04-01', 'Gender_Gap']
            print(f"Gap during COVID Peak (Apr 2020): {covid_gap:.3f}%p")
    else:
        print("Gender unemployment data missing.")

# ====================================================
# [Analysis 4] Structural Change (Energy(Gas) - Inflation)
# ====================================================
def analyze_structural_change(df):
    """
    Detect structural breaks in correlation (Pre vs Post COVID).
    """
    print("\n" + "="*80)
    print("[4. Structural Change] Correlation Shift (Energy vs Inflation)")
    print("="*80)
    
    # Ensure date index is datetime
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)

    pre_covid = df[:'2019-12-31']
    post_covid = df['2020-01-01':]
    
    if not pre_covid.empty and not post_covid.empty and 'Gas_Price' in df.columns:
        corr_pre = pre_covid['Gas_Price'].corr(pre_covid['CPI_Total_YoY'])
        corr_post = post_covid['Gas_Price'].corr(post_covid['CPI_Total_YoY'])
        
        print(f"Correlation (Pre-COVID, 2016-2019): {corr_pre:.4f}")
        print(f"Correlation (Post-COVID, 2020-2025): {corr_post:.4f}")
        
        if abs(corr_post - corr_pre) > 0.3:
            print("-> Conclusion: Significant structural regime shift detected.")
        else:
            print("-> Conclusion: Relationship remains stable.")
    else:
        print("Insufficient data for structural change analysis.")

# ===========================================================
# [Analysis 5] Economic Sensitivity (Energy(Oil) - Inflation)
# ===========================================================
def analyze_sensitivity(df):
    """
    Perform linear regression to find sensitivity of Inflation to Oil Prices.
    """
    print("\n" + "="*80)
    print("[5. Economic Sensitivity] Oil Price Impact on Inflation")
    print("="*80)
    
    if 'Oil_Price' in df.columns and 'CPI_Total_YoY' in df.columns:
        # Clean data for regression (remove NaNs and Infs)
        clean_df = df[['Oil_Price', 'CPI_Total_YoY']].replace([np.inf, -np.inf], np.nan).dropna()
        
        if len(clean_df) > 10:
            slope, intercept, r_value, p_value, std_err = stats.linregress(clean_df['Oil_Price'], clean_df['CPI_Total_YoY'])
            
            print(f"Slope (Beta): {slope:.4f}")
            print(f"R-squared: {r_value**2:.4f}")
            print(f"Interpretation: For every $1 increase in WTI Crude Oil, CPI increases by {slope:.2f}%p.")
        else:
            print("Not enough valid data points for regression.")
    else:
        print("Data missing for regression analysis.")

# ===========================================================================
# [Analysis 6] Causal Chain Verification (Energy -> Inflation -> Labor -> News)
# ===========================================================================
def analyze_causal_chain(df):
    """
    Verify the chain: Energy -> Inflation -> Labor -> News.
    """
    print("\n" + "="*80)
    print("[6. Causal Chain Verification] Lag Correlation Analysis")
    print("Hypothesis: Energy -> Inflation -> Labor -> News Fear")
    print("="*80)
    
    chains = [
        ("Energy -> Inflation", "Gas_Price", "CPI_Total_YoY"),
        ("Inflation -> Labor", "CPI_Total_YoY", "Unemp_Total"),
        ("Labor -> News Fear", "Unemp_Total", "News_Total_Counting")
    ]
    
    for name, leader, follower in chains:
        if leader in df.columns and follower in df.columns:
            print(f"\n[Link: {name}]")
            best_lag = 0
            best_corr = 0
            
            for lag in range(0, 7):
                # Corr(Leader_t, Follower_t+lag)
                # To calculate this, shift Follower BACKWARDS by lag
                # e.g., Leader(Jan) vs Follower(Feb) -> Shift Follower(-1) to align Feb with Jan
                corr = df[leader].corr(df[follower].shift(-lag))
                print(f"  - Lag {lag} month(s): {corr:.4f}")
                
                if abs(corr) > abs(best_corr):
                    best_corr = corr
                    best_lag = lag
                    
            print(f"  => Strongest Correlation at Lag {best_lag} (Corr: {best_corr:.4f})")
        else:
            print(f"Skipping {name}: Columns missing.")

# ==========================================
# Main Execution
# ==========================================
if __name__ == "__main__":
    df = load_data()
    
    if df is not None:
        analyze_basic_stats(df)
        analyze_supply_chain_impact(df)
        analyze_labor_market(df)
        analyze_gender_gap(df)
        analyze_structural_change(df)
        analyze_sensitivity(df)
        analyze_causal_chain(df)
        
        print("\n" + "="*80)
        print("Analysis Complete. Results printed to console.")
        print("="*80)