import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# --- CONFIG & STYLING ---
RESULTS_CSV = "results/pilot_100_results.csv"
CHARTS_DIR = "charts"
os.makedirs(CHARTS_DIR, exist_ok=True)

plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams["font.sans-serif"] = "DejaVu Sans"
plt.rcParams["axes.edgecolor"] = "#cccccc"
plt.rcParams["axes.linewidth"] = 0.8

def generate_charts():
    df = pd.read_csv(RESULTS_CSV)
    
    # Filter for successful evaluation rows
    df_succ = df[df["status"] == "success"].copy()
    
    # Convert boolean string columns to actual booleans
    df_succ["search_triggered"] = df_succ["search_triggered"].astype(str).str.lower() == "true"
    df_succ["initial_correct"] = df_succ["initial_correct"].astype(str).str.lower() == "true"
    df_succ["final_correct"] = df_succ["final_correct"].astype(str).str.lower() == "true"
    df_succ["difficulty"] = df_succ["difficulty"].astype(str)

    # -------------------------------------------------------------
    # CHART 1: Overall Accuracy (Initial vs Escalated 5-vote)
    # -------------------------------------------------------------
    init_acc = df_succ["initial_correct"].mean() * 100
    final_acc = df_succ["final_correct"].mean() * 100
    
    fig, ax = plt.subplots(figsize=(6.5, 5), dpi=300)
    bars = ax.bar(["Initial Pass", "Escalated 5-Vote"], [init_acc, final_acc], 
                  color=["#4C72B0", "#55A868"], width=0.45, edgecolor="none")
    
    ax.set_ylabel("Accuracy (%)", fontsize=12, labelpad=10)
    ax.set_title("Overall Accuracy: Initial Pass vs. Escalated 5-Vote", fontsize=13, fontweight="bold", pad=15)
    ax.set_ylim(0, 100)
    ax.grid(axis="y", linestyle="--", alpha=0.7)
    
    for bar in bars:
        height = bar.get_height()
        ax.annotate(f"{height:.1f}%",
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 5),
                    textcoords="offset points",
                    ha="center", va="bottom", fontsize=11, fontweight="bold")
        
    plt.tight_layout()
    overall_path = os.path.join(CHARTS_DIR, "overall_accuracy.png")
    plt.savefig(overall_path, dpi=300)
    plt.close()
    print(f"Created: {overall_path}")

    # -------------------------------------------------------------
    # CHART 2: Accuracy by Difficulty Level (Grouped Bar Chart)
    # -------------------------------------------------------------
    level_stats = df_succ.groupby("difficulty").agg(
        total=("difficulty", "count"),
        init_acc=("initial_correct", lambda x: x.mean() * 100),
        final_acc=("final_correct", lambda x: x.mean() * 100)
    ).sort_index()
    
    levels = [f"Level {lvl}" for lvl in level_stats.index]
    x = np.arange(len(levels))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(9, 5.5), dpi=300)
    rects1 = ax.bar(x - width/2, level_stats["init_acc"], width, label="Initial Pass", color="#4C72B0")
    rects2 = ax.bar(x + width/2, level_stats["final_acc"], width, label="Escalated 5-Vote", color="#55A868")
    
    ax.set_ylabel("Accuracy (%)", fontsize=12, labelpad=10)
    ax.set_title("Initial vs Escalated Accuracy by MATH-500 Difficulty Level", fontsize=14, fontweight="bold", pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(levels, fontsize=11)
    ax.legend(frameon=True, facecolor="white", edgecolor="#cccccc", fontsize=11)
    ax.set_ylim(0, 100)
    ax.grid(axis="y", linestyle="--", alpha=0.7)
    
    for rect in rects1:
        h = rect.get_height()
        ax.annotate(f"{h:.1f}%", xy=(rect.get_x() + rect.get_width() / 2, h),
                    xytext=(0, 4), textcoords="offset points", ha="center", va="bottom", fontsize=9)
    for rect in rects2:
        h = rect.get_height()
        ax.annotate(f"{h:.1f}%", xy=(rect.get_x() + rect.get_width() / 2, h),
                    xytext=(0, 4), textcoords="offset points", ha="center", va="bottom", fontsize=9)

    plt.tight_layout()
    by_level_path = os.path.join(CHARTS_DIR, "accuracy_by_level.png")
    plt.savefig(by_level_path, dpi=300)
    plt.close()
    print(f"Created: {by_level_path}")

    # -------------------------------------------------------------
    # CHART 3: Search Trigger Rate (Bar Chart: Search Triggered vs No Search)
    # -------------------------------------------------------------
    searched_count = df_succ["search_triggered"].sum()
    no_search_count = len(df_succ) - searched_count
    total_count = len(df_succ)
    
    searched_pct = (searched_count / total_count) * 100 if total_count > 0 else 0
    no_search_pct = (no_search_count / total_count) * 100 if total_count > 0 else 0

    fig, ax = plt.subplots(figsize=(6.5, 5), dpi=300)
    bars = ax.bar(["Search Triggered", "No Search"], [searched_count, no_search_count], 
                  color=["#C44E52", "#8172B0"], width=0.45, edgecolor="none")
    
    ax.set_ylabel("Number of Problems", fontsize=12, labelpad=10)
    ax.set_title(f"Search Trigger Distribution (n={total_count})", fontsize=13, fontweight="bold", pad=15)
    ax.set_ylim(0, max(searched_count + 15, 10))
    ax.grid(axis="y", linestyle="--", alpha=0.7)
    
    # Annotate count and percentage on top of bars
    for bar, pct in zip(bars, [searched_pct, no_search_pct]):
        height = bar.get_height()
        ax.annotate(f"{int(height)} ({pct:.1f}%)",
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 5),
                    textcoords="offset points",
                    ha="center", va="bottom", fontsize=11, fontweight="bold")
                    
    plt.tight_layout()
    search_path = os.path.join(CHARTS_DIR, "search_trigger_rate.png")
    plt.savefig(search_path, dpi=300)
    plt.close()
    print(f"Created: {search_path}")

if __name__ == "__main__":
    generate_charts()
