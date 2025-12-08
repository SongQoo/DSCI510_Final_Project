import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

# ==========================================
# [Setup] Style Settings
# ==========================================
sns.set_theme(style="whitegrid")
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['axes.titlesize'] = 16
plt.rcParams['axes.titleweight'] = 'bold'

# ==========================================
# [Analysis 1] Basic Statistics & Characteristics
# ==========================================
def plot_analysis1_dashboard(df: pd.DataFrame) -> plt.Figure:
    """[Analysis 1-1] Comprehensive Dashboard."""
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    plt.suptitle("Analysis 1: Statistical Characteristics Overview", fontsize=20, fontweight='bold')

    # (A) Volatility
    if 'CPI_Energy_YoY' in df.columns and 'CPI_Shelter_YoY' in df.columns:
        sns.lineplot(data=df, x=df.index, y='CPI_Energy_YoY', ax=axes[0], color='tab:red', alpha=0.5, label='Energy (High Volatility)')
        sns.lineplot(data=df, x=df.index, y='CPI_Shelter_YoY', ax=axes[0], color='tab:blue', linewidth=3, label='Shelter (Sticky)')
        axes[0].set_title("(A) Volatility: Flexible vs Sticky", fontsize=14, fontweight='bold')
        axes[0].set_ylabel("YoY Inflation (%)")
        axes[0].legend()

    # (B) Asymmetry
    if 'Unemp_Men' in df.columns and 'Unemp_Women' in df.columns:
        sns.kdeplot(data=df, x='Unemp_Men', ax=axes[1], fill=True, color='tab:blue', label='Men', alpha=0.3)
        sns.kdeplot(data=df, x='Unemp_Women', ax=axes[1], fill=True, color='tab:pink', label='Women', alpha=0.3)
        axes[1].set_title("(B) Asymmetry: Gender Gap Distribution", fontsize=14, fontweight='bold')
        axes[1].set_xlabel("Unemployment Rate (%)")
        axes[1].set_ylabel("Density (Frequency)")
        
        if not df['Unemp_Women'].isnull().all():
            max_women = df['Unemp_Women'].max()
            axes[1].annotate(f'Extreme Spike: {max_women}%', 
                             xy=(max_women, 0.05), xytext=(max_women-5, 0.15),
                             arrowprops=dict(facecolor='black', shrink=0.05))

    # (C) Reactivity
    if 'News_Total_Counting' in df.columns:
        sns.histplot(data=df, x='News_Total_Counting', ax=axes[2], bins=30, color='gray', kde=True)
        axes[2].set_title("(C) Reactivity: Media Fear 'Bursts'", fontsize=14, fontweight='bold')
        axes[2].set_xlabel("Monthly News Mention Count")
        axes[2].set_ylabel("Frequency (Months)")
        axes[2].text(0.5, 0.8, "Positive Skew\n(Long Tail)", transform=axes[2].transAxes, 
                     ha='center', color='red', fontweight='bold')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95]) 
    return fig

def plot_analysis1_sticky_inflation(df: pd.DataFrame) -> plt.Figure:
    """[Analysis 1-2] Detailed View of Sticky vs Flexible Inflation."""
    fig, ax = plt.subplots()
    ax.set_title("Analysis 1-2: Sticky vs Flexible Inflation (Time Series)", fontsize=16, fontweight='bold')
    
    if 'CPI_Shelter_YoY' in df.columns:
        sns.lineplot(data=df, x=df.index, y='CPI_Shelter_YoY', ax=ax, color='tab:blue', linewidth=3, label='Shelter (Sticky)')
    if 'CPI_Energy_YoY' in df.columns:
        sns.lineplot(data=df, x=df.index, y='CPI_Energy_YoY', ax=ax, color='tab:red', linewidth=1.5, linestyle=':', label='Energy (Volatile)')
    if 'CPI_Total_YoY' in df.columns:
        sns.lineplot(data=df, x=df.index, y='CPI_Total_YoY', ax=ax, color='black', linewidth=1, alpha=0.5, label='Total CPI')
    
    ax.set_ylabel('YoY Inflation (%)')
    ax.legend()
    return fig

def plot_analysis1_misery_index(df: pd.DataFrame) -> plt.Figure:
    """[Analysis 1-3] Macro View: The Misery Index."""
    fig, ax1 = plt.subplots()
    ax1.set_title("Analysis 1-3: The Misery Index vs Public Fear", fontsize=16, fontweight='bold')
    
    if 'Unemp_Total' in df.columns and 'CPI_Total_YoY' in df.columns:
        misery_index = df['Unemp_Total'] + df['CPI_Total_YoY']
        ax1.fill_between(df.index, misery_index, color='tab:orange', alpha=0.4, label='Economic Misery Index (CPI+Unemp)')
        ax1.set_ylabel('Index Value', color='tab:orange')
        ax1.tick_params(axis='y', labelcolor='tab:orange')
    
    ax2 = ax1.twinx()
    if 'News_Total_Counting' in df.columns:
        sns.lineplot(x=df.index, y=df['News_Total_Counting'], ax=ax2, color='black', linewidth=2, label='Total Fear News Count')
        ax2.set_ylabel('Total News Volume', color='black')
        
    fig.legend(loc='upper left', bbox_to_anchor=(0.1, 0.9))
    return fig

# ==========================================
# [Analysis 2] Supply Chain Impact
# ==========================================
def plot_analysis2_supply_chain(df: pd.DataFrame) -> plt.Figure:
    """[Analysis 2] Diesel Price vs Food CPI."""
    fig, ax1 = plt.subplots()
    ax1.set_title("Analysis 2: Supply Chain Effect (Diesel -> Food Prices)", fontsize=16, fontweight='bold')
    
    ax1.set_ylabel('Diesel Price ($/gal)', color='black', fontsize=12)
    if 'Diesel_Price' in df.columns:
        sns.lineplot(data=df, x=df.index, y='Diesel_Price', ax=ax1, color='black', linewidth=2, label='Diesel (Transport Cost)')
    ax1.tick_params(axis='y', labelcolor='black')
    ax1.legend(loc='upper left')

    ax2 = ax1.twinx()
    ax2.set_ylabel('CPI Food YoY (%)', color='green', fontsize=12)
    if 'CPI_Food_YoY' in df.columns:
        sns.lineplot(data=df, x=df.index, y='CPI_Food_YoY', ax=ax2, color='green', linestyle='--', linewidth=2, label='Food Inflation')
    ax2.tick_params(axis='y', labelcolor='green')
    ax2.legend(loc='upper right')
    return fig

def plot_analysis3_labor_tradeoff(df: pd.DataFrame) -> plt.Figure:
    """
    [Analysis 3-1] Inflation vs Unemployment Trade-off (Split Regime).
    Separates Pre-2020 and Post-2020 to reveal distinct Phillips Curve patterns.
    """
    fig, ax = plt.subplots()
    ax.set_title("Analysis 3-1: Labor Market Trade-off", fontsize=16, fontweight='bold')
    
    if 'Unemp_Total' in df.columns and 'CPI_Total_YoY' in df.columns:
        # Split data into Pre/Post 2020
        pre_2020 = df[:'2019-12-31']
        post_2020 = df['2020-01-01':]
        
        # 1. Pre-2020 Period (Stable)
        sns.scatterplot(data=pre_2020, x='Unemp_Total', y='CPI_Total_YoY', 
                        color='tab:blue', s=80, alpha=0.7, ax=ax, label='Pre-2020 (Stable)')
        # Regression Line (Pre)
        if len(pre_2020) > 1:
            sns.regplot(data=pre_2020, x='Unemp_Total', y='CPI_Total_YoY', 
                        scatter=False, ax=ax, color='tab:blue', line_kws={'linestyle':'--', 'alpha':0.5})
        
        # 2. Post-2020 Period (Shock)
        sns.scatterplot(data=post_2020, x='Unemp_Total', y='CPI_Total_YoY', 
                        color='tab:red', s=80, alpha=0.7, ax=ax, label='Post-2020 (Shock)')
        # Regression Line (Post)
        if len(post_2020) > 1:
            sns.regplot(data=post_2020, x='Unemp_Total', y='CPI_Total_YoY', 
                        scatter=False, ax=ax, color='tab:red', line_kws={'linestyle':'--', 'alpha':0.5})
        
        ax.set_xlabel('Unemployment Rate (%)')
        ax.set_ylabel('CPI Inflation YoY (%)')
        ax.legend()
        
        # Add explanatory text
        ax.text(0.05, 0.95, "Compare slopes to see\nstructural changes", 
                transform=ax.transAxes, fontsize=10, verticalalignment='top',
                bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8))
        
    return fig

def plot_analysis3_gender_gap(df: pd.DataFrame) -> plt.Figure:
    """
    [Analysis 3-2] Gender Unemployment Asymmetry.
    (Formerly Analysis 3)
    """
    fig, ax = plt.subplots()
    ax.set_title("Analysis 3-2: Gender Asymmetry in Labor Market", fontsize=16, fontweight='bold')
    
    if 'Unemp_Men' in df.columns and 'Unemp_Women' in df.columns:
        sns.lineplot(data=df, x=df.index, y='Unemp_Men', ax=ax, color='tab:blue', label='Men')
        sns.lineplot(data=df, x=df.index, y='Unemp_Women', ax=ax, color='tab:pink', label='Women')
        
        ax.fill_between(df.index, df['Unemp_Men'], df['Unemp_Women'], 
                        where=(df['Unemp_Women'] > df['Unemp_Men']), color='tab:pink', alpha=0.3, label='Women > Men')
        ax.fill_between(df.index, df['Unemp_Men'], df['Unemp_Women'], 
                        where=(df['Unemp_Men'] > df['Unemp_Women']), color='tab:blue', alpha=0.3, label='Men > Women')
    
    ax.set_ylabel('Unemployment Rate (%)')
    ax.legend()
    return fig

# ==========================================
# [Analysis 4] Structural Change
# ==========================================
def plot_analysis4_structural_change(df: pd.DataFrame) -> plt.Figure:
    """[Analysis 4] Structural Change: Rolling Correlation."""
    fig, ax = plt.subplots()
    ax.set_title("Analysis 4: Structural Change (Gas Price vs CPI)", fontsize=16, fontweight='bold')
    
    if 'Gas_Price' in df.columns and 'CPI_Total_YoY' in df.columns:
        rolling_corr = df['Gas_Price'].rolling(window=12).corr(df['CPI_Total_YoY'])
        
        sns.lineplot(x=rolling_corr.index, y=rolling_corr, ax=ax, color='purple', linewidth=2.5)
        ax.axhline(0, color='gray', linestyle='--')
        ax.set_ylim(-1, 1)
        ax.set_ylabel('Correlation Coefficient')
        
        ax.fill_between(rolling_corr.index, 0, rolling_corr, 
                        where=(rolling_corr > 0.7), color='purple', alpha=0.2, label='High Correlation (>0.7)')
        ax.legend()
    return fig

# ==========================================
# [Analysis 5] Economic Sensitivity
# ==========================================
def plot_analysis5_sensitivity_scatter(df: pd.DataFrame) -> plt.Figure:
    """[Analysis 5] Economic Sensitivity: Scatter Plot."""
    fig, ax = plt.subplots()
    ax.set_title("Analysis 5: Economic Sensitivity (Oil Price vs Inflation)", fontsize=16, fontweight='bold')
    
    if 'Oil_Price' in df.columns and 'CPI_Total_YoY' in df.columns:
        sns.scatterplot(data=df, x='Oil_Price', y='CPI_Total_YoY', hue=df.index.year, palette='viridis', s=100, ax=ax)
        sns.regplot(data=df, x='Oil_Price', y='CPI_Total_YoY', scatter=False, ax=ax, color='red', line_kws={'linestyle':'--'})
        
        ax.set_xlabel('WTI Crude Oil Price ($/barrel)')
        ax.set_ylabel('CPI Inflation YoY (%)')
    return fig

# ==========================================
# [Analysis 6] Causal Chain Verification
# ==========================================
def plot_analysis6_causal_heatmap(df: pd.DataFrame) -> plt.Figure:
    """[Analysis 6-1] Causal Chain Heatmap."""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    chain_pairs = {
        "1. Energy(Oil) -> Inflation(Total)": ('Oil_Price', 'CPI_Total_YoY'),
        "2. Energy(Diesel) -> Inflation(Food CPI)":  ('Diesel_Price', 'CPI_Food_YoY'),
        "3. Inflation -> Labor":  ('CPI_Total_YoY', 'Unemp_Total'),
        "4. Labor -> News Fear":  ('Unemp_Total', 'News_Total_Counting') 
    }
    
    lags = [0, 1, 2, 3, 4, 5, 6]
    heatmap_data = []
    valid_labels = []
    
    for label, (leader, follower) in chain_pairs.items():
        if leader in df.columns and follower in df.columns:
            corrs = []
            for lag in lags:
                c = df[leader].corr(df[follower].shift(-lag)) 
                corrs.append(c)
            heatmap_data.append(corrs)
            valid_labels.append(label)
    
    if heatmap_data:
        df_hm = pd.DataFrame(heatmap_data, index=valid_labels, columns=[f"Lag {i}m" for i in lags])
        sns.heatmap(df_hm, annot=True, cmap='RdBu_r', center=0, fmt=".2f", linewidths=1, ax=ax)
        ax.set_title("Analysis 6-1: Causal Chain Lag Heatmap", fontsize=16, fontweight='bold')
        ax.set_xlabel("Time Lag (Months after Shock)", fontsize=12)
        ax.set_ylabel("Causal Relationship Steps", fontsize=12)
        
    return fig

def plot_analysis6_news_lag(df: pd.DataFrame) -> plt.Figure:
    """[Analysis 6-2] News Lag (Job Fear)."""
    fig, ax1 = plt.subplots()
    ax1.set_title("Analysis 6-2: News Lag (Job Fear News vs Unemployment)", fontsize=16, fontweight='bold')
    
    news_cols = ['News_Total_Counting']
    valid_cols = [c for c in news_cols if c in df.columns]
    
    if valid_cols:
        job_fear_news = df[valid_cols].sum(axis=1)
        ax1.bar(df.index, job_fear_news, color='gray', alpha=0.3, label='News about Fears', width=20)
        ax1.set_ylabel('Combined News Count', color='gray', fontweight='bold')
        ax1.tick_params(axis='y', labelcolor='gray')
        ax1.legend(loc='upper left')
    
    if 'Unemp_Total' in df.columns:
        ax2 = ax1.twinx()
        sns.lineplot(data=df, x=df.index, y='Unemp_Total', ax=ax2, color='tab:red', linewidth=2.5, label='Unemployment Rate')
        ax2.set_ylabel('Unemployment Rate (%)', color='tab:red', fontweight='bold')
        ax2.tick_params(axis='y', labelcolor='tab:red')
        ax2.legend(loc='upper right')
    
    return fig

def plot_analysis6_news_evolution(df: pd.DataFrame) -> plt.Figure:
    """[Analysis 6-3] Fear Narrative Evolution."""
    fig, ax = plt.subplots()
    ax.set_title("Analysis 6-3: Evolution of Fear Narratives", fontsize=16, fontweight='bold')
    
    keywords = ['News_Count_Inflation', 'News_Count_Recession', 'News_Count_Layoff', 'News_Count_High_Price']
    labels = [k.replace('News_Count_', '') for k in keywords]
    colors = sns.color_palette("flare", n_colors=len(keywords))
    
    valid_keys = [k for k in keywords if k in df.columns]
    
    if valid_keys:
        ax.stackplot(df.index, [df[k] for k in valid_keys], labels=labels, colors=colors, alpha=0.8)
        ax.set_ylabel('Monthly Mention Count')
        ax.legend(loc='upper left')
        
    return fig