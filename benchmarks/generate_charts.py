"""
Generates high-resolution publication charts for AgentTeams README and BENCHMARK:
1. Token Scaling Curve: Monolithic O(N^2) vs AgentTeams O(N) over 3 to 50 turns.
2. Gemini 3.8 Flash Financial Cost: Monolithic vs. Standard Teamwork vs. AgentTeams across Low, Medium, High thinking.
"""

import os
import matplotlib.pyplot as plt
import numpy as np

# Output directory
ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)

# Set clean styling
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 11,
    "axes.titlesize": 14,
    "axes.titleweight": "bold",
    "axes.labelsize": 12,
    "axes.labelweight": "bold",
    "figure.titlesize": 16,
    "figure.titleweight": "bold",
})


def generate_token_scaling_chart():
    turns = [3, 5, 10, 15, 20, 30, 50]
    mono_tokens = [75300, 114500, 219000, 358500, 503000, 867000, 1835000]
    teams_tokens = [135000, 135000, 135000, 181400, 282000, 393000, 716000]

    mono_k = [x / 1000 for x in mono_tokens]
    teams_k = [x / 1000 for x in teams_tokens]

    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)

    # Plot curves
    ax.plot(turns, mono_k, marker="o", linewidth=2.8, color="#e63946", label="Monolithic Single Agent (Quadratic O(N²))")
    ax.plot(turns, teams_k, marker="s", linewidth=2.8, color="#2a9d8f", label="AgentTeams Protocol (Modular O(N))")

    # Fill difference area after crossover
    ax.fill_between(turns[2:], teams_k[2:], mono_k[2:], color="#2a9d8f", alpha=0.15, label="Token Savings Area (Up to 61%)")

    # Annotate Crossover Point
    ax.annotate(
        "Crossover Point (~8 Turns)\nAgentTeams becomes more efficient",
        xy=(8, 175),
        xytext=(12, 500),
        arrowprops=dict(facecolor="#333333", shrink=0.08, width=1.5, headwidth=7),
        fontsize=10,
        fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.4", fc="#f1faee", ec="#2a9d8f", lw=1.5)
    )

    # Annotate 50-turn endpoint
    ax.annotate(
        "1.1M Tokens Saved!\n(-60.98%)",
        xy=(50, 716),
        xytext=(36, 1200),
        arrowprops=dict(facecolor="#2a9d8f", shrink=0.08, width=1.5, headwidth=7),
        fontsize=10,
        fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.4", fc="#e8f5e9", ec="#2e7d32", lw=1.5)
    )

    ax.set_title("Token Consumption Scaling: Monolithic vs. AgentTeams", pad=15)
    ax.set_xlabel("Number of Conversation Turns (N)")
    ax.set_ylabel("Cumulative Billed Tokens (in Thousands)")
    ax.set_xlim(1, 53)
    ax.set_ylim(0, 2000)
    ax.legend(loc="upper left", frameon=True, facecolor="white", edgecolor="#cccccc")

    chart_path = os.path.join(ASSETS_DIR, "token_scaling_chart.png")
    plt.tight_layout()
    plt.savefig(chart_path, dpi=300)
    plt.close()
    print(f"Created: {chart_path}")


def generate_gemini_flash_financial_chart():
    categories = ["Low\n(~350 tok/turn)", "Medium\n(~1,400 tok/turn)", "High\n(~3,800 tok/turn)"]
    mono_costs = [0.0656, 0.0719, 0.0863]
    std_costs = [0.0487, 0.0575, 0.0777]
    teams_costs = [0.0345, 0.0421, 0.0594]

    x = np.arange(len(categories))
    width = 0.25

    fig, ax = plt.subplots(figsize=(10.5, 6), dpi=300)

    rects1 = ax.bar(x - width, mono_costs, width, label="1. Monolithic Single Agent", color="#e76f51", edgecolor="#333333", alpha=0.9)
    rects2 = ax.bar(x, std_costs, width, label="2. Standard Antigravity Teamwork", color="#f4a261", edgecolor="#333333", alpha=0.9)
    rects3 = ax.bar(x + width, teams_costs, width, label="3. AgentTeams Protocol (DAG + Contracts)", color="#2a9d8f", edgecolor="#333333", alpha=0.9)

    # Add cost labels
    for rect in rects1:
        h = rect.get_height()
        ax.annotate(f"${h:.4f}", xy=(rect.get_x() + rect.get_width()/2, h), xytext=(0, 3),
                    textcoords="offset points", ha="center", va="bottom", fontsize=8.5, color="#555555")

    for rect in rects2:
        h = rect.get_height()
        ax.annotate(f"${h:.4f}", xy=(rect.get_x() + rect.get_width()/2, h), xytext=(0, 3),
                    textcoords="offset points", ha="center", va="bottom", fontsize=8.5, color="#555555")

    # Add savings labels on AgentTeams
    savings_vs_std = [29.2, 26.9, 23.6]
    for i, rect in enumerate(rects3):
        h = rect.get_height()
        ax.annotate(
            f"${h:.4f}\n(-{savings_vs_std[i]}% vs Std)",
            xy=(rect.get_x() + rect.get_width()/2, h),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center", va="bottom",
            fontsize=8.5,
            fontweight="bold",
            color="#1b4332"
        )

    ax.set_title("Financial Cost: Monolithic vs. Standard Teamwork vs. AgentTeams\n(Gemini 3.8 Flash across Thinking Effort Tiers)", pad=15)
    ax.set_xlabel("Gemini 3.8 Flash Thinking Effort Tier")
    ax.set_ylabel("API Cost per Task Run (USD $)")
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.set_ylim(0, 0.11)
    ax.legend(loc="upper left", frameon=True, facecolor="white", edgecolor="#cccccc")

    chart_path = os.path.join(ASSETS_DIR, "gemini_flash_financial_chart.png")
    plt.tight_layout()
    plt.savefig(chart_path, dpi=300)
    plt.close()
    print(f"Created: {chart_path}")


if __name__ == "__main__":
    generate_token_scaling_chart()
    generate_gemini_flash_financial_chart()
