"""
Generates publication charts for AgentTeams README and BENCHMARK.
100% DYNAMIC: All data is computed on-the-fly from the benchmark simulation engine.
NO HARDCODED RESULTS.
"""

import os
import json
import matplotlib.pyplot as plt
import numpy as np
from extended_benchmarks import run_dynamic_three_way_comparison

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 10.5,
    "axes.edgecolor": "#d0d7de",
    "axes.linewidth": 1.0,
    "grid.color": "#eaeef2",
    "grid.linestyle": "--",
    "grid.linewidth": 0.8,
})


def generate_charts():
    # 1. Run the dynamic simulation
    print("Running dynamic simulation with tiktoken...")
    sim_data = run_dynamic_three_way_comparison()
    sweep = sim_data["turn_sweep"]
    financials = sim_data["financial_comparison_20_turns"]

    # -------------------------------------------------------------
    # Chart 1: Token Scaling Curve (3 to 50 Turns)
    # -------------------------------------------------------------
    turns = [row["turns"] for row in sweep]
    mono_k = [row["monolithic_tokens"] / 1000 for row in sweep]
    std_k = [row["standard_teamwork_tokens"] / 1000 for row in sweep]
    teams_k = [row["agent_teams_tokens"] / 1000 for row in sweep]

    fig, ax = plt.subplots(figsize=(9.5, 5.2), dpi=300, facecolor="#ffffff")
    ax.set_facecolor("#ffffff")

    ax.plot(turns, mono_k, marker="o", markersize=6, linewidth=2.3, color="#cf222e", label="1. Monolithic Agent ($O(N^2)$ Context Explosion)")
    ax.plot(turns, std_k, marker="^", markersize=6, linewidth=2.3, color="#d97706", linestyle="-.", label="2. Standard Antigravity Teamwork (Chatty Handoffs & Re-reads)")
    ax.plot(turns, teams_k, marker="s", markersize=6, linewidth=2.5, color="#1a7f37", label="3. AgentTeams Protocol (DAG + Bounded Contracts)")

    ax.fill_between(turns[2:], teams_k[2:], std_k[2:], color="#1a7f37", alpha=0.10, label="AgentTeams Savings vs. Standard Teamwork")

    # Annotations dynamically derived from sweep
    crossover_turn = None
    for row in sweep:
        if row["agent_teams_tokens"] < row["monolithic_tokens"]:
            crossover_turn = row["turns"]
            break

    if crossover_turn:
        ax.annotate(
            f"Crossover (~{crossover_turn} Turns)\nAgentTeams saves tokens",
            xy=(crossover_turn, teams_k[turns.index(crossover_turn)]),
            xytext=(crossover_turn + 3, teams_k[turns.index(crossover_turn)] + 400),
            arrowprops=dict(facecolor="#57606a", shrink=0.08, width=1.2, headwidth=6),
            fontsize=9,
            fontweight="bold",
            color="#24292f",
            bbox=dict(boxstyle="round,pad=0.35", fc="#f6f8fa", ec="#d0d7de", lw=1)
        )

    last_row = sweep[-1]
    saved_vs_mono_pct = last_row["savings_vs_monolithic_percent"]
    saved_vs_std_pct = last_row["savings_vs_standard_percent"]
    ax.annotate(
        f"At {last_row['turns']} turns:\n• Saves {saved_vs_mono_pct}% vs. Monolith\n• Saves {saved_vs_std_pct}% vs. Teamwork",
        xy=(last_row["turns"], teams_k[-1]),
        xytext=(last_row["turns"] - 22, teams_k[-1] + 500),
        arrowprops=dict(facecolor="#1a7f37", shrink=0.08, width=1.2, headwidth=6),
        fontsize=9,
        fontweight="bold",
        color="#1a7f37",
        bbox=dict(boxstyle="round,pad=0.35", fc="#ddf4ff", ec="#54aeff", lw=1)
    )

    ax.set_title("Token Consumption Scaling: Monolithic vs. Standard Teamwork vs. AgentTeams", fontsize=12.5, fontweight="bold", pad=12, color="#1f2328")
    ax.set_xlabel("Conversation Turns", fontweight="bold", color="#24292f")
    ax.set_ylabel("Tokens (Thousands)", fontweight="bold", color="#24292f")
    ax.set_xlim(1, max(turns) + 3)
    ax.set_ylim(0, max(mono_k) * 1.1)
    ax.grid(True)
    ax.legend(loc="upper left", frameon=True, facecolor="#ffffff", edgecolor="#d0d7de", fontsize=9)

    chart_1_path = os.path.join(ASSETS_DIR, "chart_token_scaling.png")
    plt.tight_layout()
    plt.savefig(chart_1_path, dpi=300)
    plt.close()
    print(f"Generated dynamic chart: {chart_1_path}")

    # -------------------------------------------------------------
    # Chart 2: Gemini 3.8 Flash Financial Cost
    # -------------------------------------------------------------
    categories = [
        f"{d['thinking_effort']}\n({d['thinking_tokens_per_turn']} tok/turn)"
        for d in financials.values()
    ]
    mono_costs = [d["monolithic"]["cost_usd"] for d in financials.values()]
    std_costs = [d["standard_teamwork"]["cost_usd"] for d in financials.values()]
    teams_costs = [d["agent_teams"]["cost_usd"] for d in financials.values()]
    savings_vs_std = [d["savings_vs_standard_teamwork"]["percent_saved"] for d in financials.values()]

    x = np.arange(len(categories))
    width = 0.24

    fig, ax = plt.subplots(figsize=(9, 4.8), dpi=300, facecolor="#ffffff")
    ax.set_facecolor("#ffffff")

    rects1 = ax.bar(x - width, mono_costs, width, label="1. Monolithic Agent", color="#cf222e", alpha=0.85, edgecolor="#af1924")
    rects2 = ax.bar(x, std_costs, width, label="2. Standard Teamwork", color="#d97706", alpha=0.85, edgecolor="#b45309")
    rects3 = ax.bar(x + width, teams_costs, width, label="3. AgentTeams Protocol", color="#1a7f37", alpha=0.9, edgecolor="#116329")

    # Dynamic labels
    for i, rect in enumerate(rects3):
        h = rect.get_height()
        ax.annotate(
            f"${h:.4f}\n(-{savings_vs_std[i]}%)",
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
    ax.set_xlabel("Thinking Effort Level", fontweight="bold", color="#24292f")
    ax.set_ylabel("Cost per Run ($)", fontweight="bold", color="#24292f")
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.set_ylim(0, max(mono_costs) * 1.25)
    ax.grid(True, axis="y")
    ax.legend(loc="upper left", frameon=True, facecolor="#ffffff", edgecolor="#d0d7de", fontsize=9.5)

    chart_2_path = os.path.join(ASSETS_DIR, "chart_gemini_flash_financial.png")
    plt.tight_layout()
    plt.savefig(chart_2_path, dpi=300)
    plt.close()
    print(f"Generated dynamic chart: {chart_2_path}")


if __name__ == "__main__":
    generate_charts()
