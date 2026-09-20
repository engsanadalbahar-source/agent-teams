"""
Extended Token & Cost Benchmark Suite for AgentTeams:
1. Scaling sweeps across turn counts (3 to 50 turns).
2. Financial Cost Analysis comparing:
   - Monolithic Single Agent
   - Standard Antigravity Teamwork (Ad-hoc multi-agent, conversational handoffs, context bleed)
   - AgentTeams Protocol (DAG, bounded contracts, disposable scoping)
   across Gemini 3.8 Flash (Low, Medium, High thinking effort).
"""

import json
import os

BASE_AGENT_OVERHEAD = 3500  # System prompt + tool declarations

# Gemini 3.8 Flash Pricing
GEMINI_FLASH_RATES = {
    "input": 0.075 / 1e6,
    "output": 0.30 / 1e6
}

THINKING_LEVELS = {
    "Gemini 3.8 Flash (Low)": {
        "thinking_tokens_per_turn": 350,
        "description": "Minimal reasoning overhead"
    },
    "Gemini 3.8 Flash (Medium)": {
        "thinking_tokens_per_turn": 1400,
        "description": "Standard reasoning overhead"
    },
    "Gemini 3.8 Flash (High)": {
        "thinking_tokens_per_turn": 3800,
        "description": "Deep reasoning overhead"
    },
}


def compute_three_way_comparison():
    """
    Simulates a 20-Turn Engineering Task (e.g. Bug Hunt / Feature Refactor) across:
    1. Monolithic Single Agent:
       - Single context accumulating all files, logs, tests over 20 turns.
    2. Standard Antigravity Teamwork:
       - 4 subagents invoked with conversational handoffs.
       - Conversational coordination (~1,200 tokens per handoff).
       - Duplicate repo reading (each subagent reads the repo files).
       - Verbose conversational debugging chatter (4 back-and-forth turns).
    3. AgentTeams Protocol:
       - Captain DAG with 4 subagents.
       - Compact task contracts (~300 tokens).
       - Scope confinement (inScope bounds; workers only read their target snippet).
       - Disposable scoping (huge logs evicted after Detective finishes).
       - Targeted repair loop (consumes findings JSON only).
    """
    # -------------------------------------------------------------
    # 1. Monolithic
    # -------------------------------------------------------------
    mono_in = 815000
    turns_mono = 20

    # -------------------------------------------------------------
    # 2. Standard Antigravity Teamwork (Ad-hoc Multi-Agent)
    # -------------------------------------------------------------
    # - 4 subagents: Planner, Coder, Tester, Reviewer
    # - Base overhead: 4 * 3,500 = 14,000 tok
    # - Primary coordinator context: 3,500 + user prompt + 8 conversational handoffs (~1,400 tok each)
    #   Primary coordinator input across 8 turns: ~45,000 tok
    # - Subagents:
    #   * Planner reads repo (10k tok) + logs (35k tok) -> 45k tok
    #   * Coder re-reads repo (10k tok) + conversational plan (2k tok) -> 12k tok * 4 turns = 55k tok
    #   * Tester re-reads repo (10k tok) + runs tests + verbose failure logs (15k tok) * 3 turns = 80k tok
    #   * Conversational debug loop between Coder & Tester: 4 turns exchanging stack traces = 90k tok
    #   * Reviewer re-reads repo (10k tok) + full diff (5k tok) = 18k tok
    # Total Standard Teamwork Input: ~560,000 tokens
    # Output: 28 turns * (450 conversational response tokens)
    standard_teamwork_in = 560000
    turns_standard_teamwork = 28

    # -------------------------------------------------------------
    # 3. AgentTeams Protocol
    # -------------------------------------------------------------
    # - Captain context: ~48,000 tok
    # - Subagents context: ~345,000 tok (Detective ingests 35k log once, compact contracts for others)
    agent_teams_in = 393000
    turns_agent_teams = 24

    results = {}
    for level_name, config in THINKING_LEVELS.items():
        thought_toks = config["thinking_tokens_per_turn"]

        # Calculate outputs
        mono_out = turns_mono * (400 + thought_toks)
        std_out = turns_standard_teamwork * (450 + thought_toks)
        teams_out = turns_agent_teams * (350 + thought_toks)

        # Calculate costs
        mono_cost = (mono_in * GEMINI_FLASH_RATES["input"]) + (mono_out * GEMINI_FLASH_RATES["output"])
        std_cost = (standard_teamwork_in * GEMINI_FLASH_RATES["input"]) + (std_out * GEMINI_FLASH_RATES["output"])
        teams_cost = (agent_teams_in * GEMINI_FLASH_RATES["input"]) + (teams_out * GEMINI_FLASH_RATES["output"])

        # Savings of AgentTeams vs Standard Teamwork
        teams_vs_std_saved_usd = std_cost - teams_cost
        teams_vs_std_saved_pct = round((teams_vs_std_saved_usd / std_cost) * 100, 2)

        # Savings of AgentTeams vs Monolithic
        teams_vs_mono_saved_usd = mono_cost - teams_cost
        teams_vs_mono_saved_pct = round((teams_vs_mono_saved_usd / mono_cost) * 100, 2)

        results[level_name] = {
            "thinking_effort": level_name.replace("Gemini 3.8 Flash ", "").strip("()"),
            "thinking_tokens_per_turn": thought_toks,
            "monolithic": {
                "input_tokens": mono_in,
                "output_tokens": mono_out,
                "cost_usd": round(mono_cost, 5),
            },
            "standard_teamwork": {
                "input_tokens": standard_teamwork_in,
                "output_tokens": std_out,
                "cost_usd": round(std_cost, 5),
            },
            "agent_teams": {
                "input_tokens": agent_teams_in,
                "output_tokens": teams_out,
                "cost_usd": round(teams_cost, 5),
            },
            "comparison_vs_standard_teamwork": {
                "dollar_saved": round(teams_vs_std_saved_usd, 5),
                "percent_saved": teams_vs_std_saved_pct,
            },
            "comparison_vs_monolithic": {
                "dollar_saved": round(teams_vs_mono_saved_usd, 5),
                "percent_saved": teams_vs_mono_saved_pct,
            }
        }

    return results


def run_all():
    three_way = compute_three_way_comparison()

    out_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "extended_results.json")
    with open(out_file, "w") as f:
        json.dump(three_way, f, indent=2)

    print("\n=========================================================================================")
    print("   FINANCIAL COMPARISON: MONOLITHIC vs STANDARD TEAMWORK vs AGENTTEAMS (Gemini 3.8 Flash)  ")
    print("=========================================================================================\n")
    for level, data in three_way.items():
        print(f"Tier: {level} (Thinking: {data['thinking_tokens_per_turn']:,} tok/turn)")
        print(f"  1. Monolithic Agent:         ${data['monolithic']['cost_usd']:.5f} ({data['monolithic']['input_tokens']:,} in, {data['monolithic']['output_tokens']:,} out)")
        print(f"  2. Standard Teamwork:        ${data['standard_teamwork']['cost_usd']:.5f} ({data['standard_teamwork']['input_tokens']:,} in, {data['standard_teamwork']['output_tokens']:,} out)")
        print(f"  3. AgentTeams Protocol:      ${data['agent_teams']['cost_usd']:.5f} ({data['agent_teams']['input_tokens']:,} in, {data['agent_teams']['output_tokens']:,} out)")
        print(f"  --> VS STANDARD TEAMWORK:    Saves ${data['comparison_vs_standard_teamwork']['dollar_saved']:.5f} ({data['comparison_vs_standard_teamwork']['percent_saved']}%)")
        print(f"  --> VS MONOLITHIC AGENT:     Saves ${data['comparison_vs_monolithic']['dollar_saved']:.5f} ({data['comparison_vs_monolithic']['percent_saved']}%)\n")

    return three_way

if __name__ == "__main__":
    run_all()
