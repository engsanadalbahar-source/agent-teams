"""
Generates high-resolution publication chart comparing CaveAgents v1 vs CaveAgents v2 vs Baselines.
Saves to assets/chart_agent_teams_caveman.png
"""

import json
import os
import matplotlib.pyplot as plt
import numpy as np

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)

# Publication styling
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["SF Pro Display", "Helvetica Neue", "Arial", "DejaVu Sans"],
    "font.size": 10,
    "axes.edgecolor": "#d0d7de",
    "axes.linewidth": 1.2,
    "axes.labelsize": 10.5,
    "axes.labelweight": "bold",
    "axes.titlesize": 12,
    "axes.titleweight": "bold",
    "xtick.labelsize": 9.5,
    "ytick.labelsize": 9.5,
    "grid.color": "#e1e4e8",
    "grid.linestyle": "--",
    "grid.linewidth": 0.8,
    "figure.titlesize": 14,
    "figure.titleweight": "bold",
})


def generate_chart():
    results_path = os.path.join(os.path.dirname(__file__), "caveagents_v1_v2_results.json")
    with open(results_path, "r") as f:
        data = json.load(f)

    sweep = data["turn_sweep"]
    live = data["live_task_comparison"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6.4), dpi=300, facecolor="#ffffff")
    fig.patch.set_facecolor("#ffffff")

    # -------------------------------------------------------------
    # Panel 1: Token Scaling Curve (3 to 50 Turns)
    # -------------------------------------------------------------
    turns = [r["turns"] for r in sweep]
    m_std = [r["mono_standard"] / 1000 for r in sweep]
    t_std = [r["agent_teams_standard"] / 1000 for r in sweep]
    v1_toks = [r["caveagents_v1"] / 1000 for r in sweep]
    v2_toks = [r["caveagents_v2"] / 1000 for r in sweep]

    ax1.set_facecolor("#ffffff")
    ax1.plot(turns, m_std, marker="o", markersize=6, linewidth=2.0, color="#cf222e", linestyle="--", label="1. Monolithic (Standard Verbose)")
    ax1.plot(turns, t_std, marker="s", markersize=6, linewidth=2.0, color="#0969da", linestyle="-.", label="2. AgentTeams (Standard Subagents)")
    ax1.plot(turns, v1_toks, marker="D", markersize=6, linewidth=2.2, color="#d97706", linestyle=":", label="3. CaveAgents v1 (Serial Pipeline + Caveman)")
    ax1.plot(turns, v2_toks, marker="*", markersize=9.5, linewidth=2.8, color="#1a7f37", label="4. CaveAgents v2 (Cloned Coders + P2P Comms)")

    # Fill savings area for v2 vs Monolith
    ax1.fill_between(turns[1:], v2_toks[1:], m_std[1:], color="#1a7f37", alpha=0.08, label="CaveAgents v2 Savings vs Monolith (up to 85.1%)")

    # Annotations
    ax1.annotate(
        "Crossover (~6 Turns)\nCaveAgents v2 beats Monolith",
        xy=(turns[1], v2_toks[1]),
        xytext=(turns[1] + 1.5, v2_toks[1] + 140),
        arrowprops=dict(facecolor="#24292f", shrink=0.08, width=1.0, headwidth=5),
        fontsize=8.5,
        fontweight="bold",
        color="#24292f",
        bbox=dict(boxstyle="round,pad=0.3", fc="#f6f8fa", ec="#d0d7de", lw=1)
    )

    ax1.annotate(
        f"At 50 Turns:\n• -85.1% vs Monolith\n• -61.3% vs v1\n(651k tokens saved!)",
        xy=(turns[-1], v2_toks[-1]),
        xytext=(turns[-1] - 22, v2_toks[-1] + 190),
        arrowprops=dict(facecolor="#1a7f37", shrink=0.08, width=1.2, headwidth=6),
        fontsize=8.5,
        fontweight="bold",
        color="#1a7f37",
        bbox=dict(boxstyle="round,pad=0.35", fc="#dafbe1", ec="#4ac26b", lw=1)
    )

    ax1.set_title("A. Token Scaling Curve: CaveAgents v1 vs v2 Across Turns")
    ax1.set_xlabel("Conversation Turns")
    ax1.set_ylabel("Total Billed Tokens (Thousands / k)")
    ax1.set_xticks(turns)
    ax1.set_xlim(1, 52)
    ax1.set_ylim(0, 830)
    ax1.grid(True, linestyle="--", alpha=0.6)
    ax1.legend(loc="upper left", frameon=True, facecolor="#ffffff", edgecolor="#d0d7de", fontsize=8.2)

    # -------------------------------------------------------------
    # Panel 2: Live Empirical Test (TokenBucket) Comparison
    # -------------------------------------------------------------
    ax2.set_facecolor("#ffffff")
    labels = [
        "Standard\nTeamwork",
        "AgentTeams\n(Standard)",
        "CaveAgents\nv1",
        "CaveAgents\nv2",
        "Monolithic\n(Standard)",
    ]
    toks = [
        live["standard_teamwork"]["tokens"] / 1000,
        live["agent_teams_standard"]["tokens"] / 1000,
        live["caveagents_v1"]["tokens"] / 1000,
        live["caveagents_v2"]["tokens"] / 1000,
        live["monolithic_standard"]["tokens"] / 1000,
    ]
    costs = [
        live["standard_teamwork"]["cost"],
        live["agent_teams_standard"]["cost"],
        live["caveagents_v1"]["cost"],
        live["caveagents_v2"]["cost"],
        live["monolithic_standard"]["cost"],
    ]
    colors = ["#d97706", "#0969da", "#f59e0b", "#1a7f37", "#cf222e"]

    bars = ax2.bar(labels, toks, color=colors, width=0.55, edgecolor="#24292f", linewidth=0.8, alpha=0.9)

    for bar, tok, cost_val in zip(bars, toks, costs):
        y_val = bar.get_height()
        ax2.text(
            bar.get_x() + bar.get_width() / 2,
            y_val + 4,
            f"{tok:.1f}k tok\n(${cost_val:.4f})",
            ha="center",
            va="bottom",
            fontsize=8.2,
            fontweight="bold",
            color="#24292f"
        )

    # Callout highlighting v2 reduction
    ax2.annotate(
        "CaveAgents v2 drops under 89k tok!\n• -57.6% vs Standard Teamwork\n• -23.5% vs CaveAgents v1",
        xy=(3, toks[3] + 25),
        xytext=(1.8, 185),
        arrowprops=dict(facecolor="#1a7f37", edgecolor="#1a7f37", shrink=0.05, width=1.2, headwidth=6),
        fontsize=8.5,
        fontweight="bold",
        color="#1a7f37",
        bbox=dict(boxstyle="round,pad=0.35", fc="#dafbe1", ec="#4ac26b", lw=1)
    )

    ax2.set_title("B. Live Empirical Test: TokenBucket (Gemini 3.8 Flash)")
    ax2.set_ylabel("Total Billed Tokens (Thousands / k)")
    ax2.set_ylim(0, 275)
    ax2.grid(True, axis="y", linestyle="--", alpha=0.6)

    plt.suptitle("CaveAgents Evolution: v1 (Serial Pipeline) vs. v2 (Cloned Parallel Coders + Direct P2P)", fontsize=13.5, y=0.98)
    plt.tight_layout()

    out_png = os.path.join(ASSETS_DIR, "chart_agent_teams_caveman.png")
    plt.savefig(out_png, dpi=300, bbox_inches="tight")
    plt.close()
    print(f"Successfully generated v1 vs v2 high-res chart: {out_png}")


if __name__ == "__main__":
    generate_chart()
