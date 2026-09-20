"""
Generates sleek, minimalist, high-resolution charts for GitHub:
1. Token Scaling Curve: Monolithic vs. AgentTeams (3 to 50 turns).
2. Gemini 3.8 Flash Financial Cost: Monolithic vs. Standard Teamwork vs. AgentTeams.
"""

import os
import matplotlib.pyplot as plt
import numpy as np

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)

# Modern clean styling
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 10.5,
    "axes.edgecolor": "#d0d7de",
    "axes.linewidth": 1.0,
    "grid.color": "#eaeef2",
    "grid.linestyle": "--",
    "grid.linewidth": 0.8,
})


def generate_token_scaling_chart():
    turns = [3, 5, 10, 15, 20, 30, 50]
    mono_tokens = [75.3, 114.5, 219.0, 358.5, 503.0, 867.0, 1835.0]  # in thousands
    teams_tokens = [135.0, 135.0, 135.0, 181.4, 282.0, 393.0, 716.0]

    fig, ax = plt.subplots(figsize=(9, 4.8), dpi=300, facecolor="#ffffff")
    ax.set_facecolor("#ffffff")

    # Plot
    ax.plot(turns, mono_tokens, marker="o", markersize=6, linewidth=2.4, color="#cf222e", label="Monolithic Agent ($O(N^2)$ Context Explosion)")
    ax.plot(turns, teams_tokens, marker="s", markersize=6, linewidth=2.4, color="#0969da", label="AgentTeams Protocol (Modular $O(N)$)")
    ax.fill_between(turns[2:], teams_tokens[2:], mono_tokens[2:], color="#0969da", alpha=0.10)

    # Clean Crossover Label
    ax.annotate(
        "Crossover (~8 Turns)\nAgentTeams saves tokens",
        xy=(8, 175),
        xytext=(13, 550),
        arrowprops=dict(facecolor="#57606a", shrink=0.08, width=1.2, headwidth=6),
        fontsize=9,
        fontweight="600",
        color="#24292f",
        bbox=dict(boxstyle="round,pad=0.35", fc="#f6f8fa", ec="#d0d7de", lw=1)
    )

    # Endpoint savings
    ax.annotate(
        "1.1M Tokens Saved (-61%)",
        xy=(50, 716),
        xytext=(32, 1150),
        arrowprops=dict(facecolor="#0969da", shrink=0.08, width=1.2, headwidth=6),
        fontsize=9.5,
        fontweight="bold",
        color="#0969da",
        bbox=dict(boxstyle="round,pad=0.35", fc="#ddf4ff", ec="#54aeff", lw=1)
    )

    ax.set_title("Cumulative Token Consumption (3 to 50 Turns)", fontsize=13, fontweight="bold", pad=12, color="#1f2328")
    ax.set_xlabel("Conversation Turns", fontweight="600", color="#24292f")
    ax.set_ylabel("Tokens (Thousands)", fontweight="600", color="#24292f")
    ax.set_xlim(1, 53)
    ax.set_ylim(0, 2000)
    ax.grid(True)
    ax.legend(loc="upper left", frameon=True, facecolor="#ffffff", edgecolor="#d0d7de", fontsize=9.5)

    chart_path = os.path.join(ASSETS_DIR, "token_scaling_chart.png")
    plt.tight_layout()
    plt.savefig(chart_path, dpi=300)
    plt.close()
    print(f"Generated: {chart_path}")


def generate_gemini_flash_financial_chart():
    categories = ["Low\n(350 tok/turn)", "Medium\n(1.4k tok/turn)", "High\n(3.8k tok/turn)"]
    mono_costs = [0.0656, 0.0719, 0.0863]
    std_costs = [0.0487, 0.0575, 0.0777]
    teams_costs = [0.0345, 0.0421, 0.0594]

    x = np.arange(len(categories))
    width = 0.24

    fig, ax = plt.subplots(figsize=(9, 4.8), dpi=300, facecolor="#ffffff")
    ax.set_facecolor("#ffffff")

    rects1 = ax.bar(x - width, mono_costs, width, label="Monolithic Agent", color="#cf222e", alpha=0.85, edgecolor="#af1924")
    rects2 = ax.bar(x, std_costs, width, label="Standard Teamwork", color="#9a6700", alpha=0.85, edgecolor="#7d5300")
    rects3 = ax.bar(x + width, teams_costs, width, label="AgentTeams Protocol", color="#1a7f37", alpha=0.9, edgecolor="#116329")

    # Clean top labels
    savings = ["-29.2%", "-26.9%", "-23.6%"]
    for i, rect in enumerate(rects3):
        h = rect.get_height()
        ax.annotate(
            f"${h:.4f}\n({savings[i]})",
            xy=(rect.get_x() + rect.get_width()/2, h),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center", va="bottom",
            fontsize=8.5,
            fontweight="bold",
            color="#116329"
        )

    for rect in rects1:
        h = rect.get_height()
        ax.annotate(f"${h:.4f}", xy=(rect.get_x() + rect.get_width()/2, h), xytext=(0, 3),
                    textcoords="offset points", ha="center", va="bottom", fontsize=8, color="#57606a")

    for rect in rects2:
        h = rect.get_height()
        ax.annotate(f"${h:.4f}", xy=(rect.get_x() + rect.get_width()/2, h), xytext=(0, 3),
                    textcoords="offset points", ha="center", va="bottom", fontsize=8, color="#57606a")

    ax.set_title("Gemini 3.8 Flash Cost per 20-Turn Task (USD $)", fontsize=13, fontweight="bold", pad=12, color="#1f2328")
    ax.set_xlabel("Thinking Effort Level", fontweight="600", color="#24292f")
    ax.set_ylabel("Cost per Run ($)", fontweight="600", color="#24292f")
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.set_ylim(0, 0.105)
    ax.grid(True, axis="y")
    ax.legend(loc="upper left", frameon=True, facecolor="#ffffff", edgecolor="#d0d7de", fontsize=9.5)

    chart_path = os.path.join(ASSETS_DIR, "gemini_flash_financial_chart.png")
    plt.tight_layout()
    plt.savefig(chart_path, dpi=300)
    plt.close()
    print(f"Generated: {chart_path}")


if __name__ == "__main__":
    generate_token_scaling_chart()
    generate_gemini_flash_financial_chart()
