"""
Extended Token & Cost Benchmark Suite for AgentTeams:
1. Scaling sweeps across turn counts (3 to 50 turns).
2. Disposable noise sweeps (0 to 100k tokens).
3. Multi-Model Financial Cost Analysis (Gemini Flash, Gemini Pro, Claude 3.5 Sonnet, GPT-4o).
"""

import json
import os

BASE_AGENT_OVERHEAD = 3500  # System prompt + tool declarations

MODEL_PRICING = {
    "Gemini 1.5 / 2.0 Flash": {"input": 0.075 / 1e6, "output": 0.30 / 1e6},
    "Gemini 1.5 Pro": {"input": 1.25 / 1e6, "output": 5.00 / 1e6},
    "Claude 3.5 Sonnet": {"input": 3.00 / 1e6, "output": 15.00 / 1e6},
    "GPT-4o": {"input": 2.50 / 1e6, "output": 10.00 / 1e6},
}


def compute_turn_sweep():
    """Evaluate token scaling as the conversation grows from 3 to 50 turns."""
    turns_list = [3, 5, 10, 15, 20, 30, 50]
    base_repo = 5000
    disposable_noise = 15000  # e.g., moderate logs or test traces
    num_subagents = 4

    sweep_results = []
    for turns in turns_list:
        # Monolithic:
        mono_in = 0
        mono_out = 0
        ctx = BASE_AGENT_OVERHEAD
        for t in range(1, turns + 1):
            t_in = 400
            if t == 1:
                t_in += base_repo
            if t == (turns // 2):
                t_in += disposable_noise
            mono_in += ctx + t_in
            t_out = 400
            mono_out += t_out
            ctx += t_in + t_out

        # AgentTeams:
        # Captain:
        capt_ctx = BASE_AGENT_OVERHEAD + 400
        capt_in = 0
        capt_out = 0
        for s in range(num_subagents):
            capt_in += capt_ctx
            capt_out += 300
            capt_ctx += 300
            capt_in += capt_ctx + 600
            capt_out += 200
            capt_ctx += 600 + 200

        # Subagents:
        sub_in = 0
        sub_out = 0
        turns_per_sub = max(2, turns // num_subagents)
        for s in range(num_subagents):
            sub_ctx = BASE_AGENT_OVERHEAD + 400
            repo_read = int(base_repo * 0.4)
            noise = disposable_noise if s == 0 else 0
            for st in range(turns_per_sub):
                t_in = 300
                if st == 0:
                    t_in += repo_read + noise
                sub_in += sub_ctx + t_in
                t_out = 350
                sub_out += t_out
                sub_ctx += t_in + t_out

        teams_in = capt_in + sub_in
        teams_out = capt_out + sub_out

        savings_pct = round(((mono_in + mono_out) - (teams_in + teams_out)) / (mono_in + mono_out) * 100, 2)

        sweep_results.append({
            "turns": turns,
            "monolithic_total": mono_in + mono_out,
            "agent_teams_total": teams_in + teams_out,
            "savings_percent": savings_pct,
            "advantage": "AgentTeams" if savings_pct > 0 else "Monolithic"
        })

    return sweep_results


def compute_financial_comparison(mono_in: int, mono_out: int, teams_in: int, teams_out: int):
    """Calculate monetary costs across standard LLM APIs."""
    cost_data = {}
    for model, rates in MODEL_PRICING.items():
        mono_cost = (mono_in * rates["input"]) + (mono_out * rates["output"])
        teams_cost = (teams_in * rates["input"]) + (teams_out * rates["output"])
        saved = mono_cost - teams_cost
        cost_data[model] = {
            "monolithic_cost_usd": round(mono_cost, 4),
            "agent_teams_cost_usd": round(teams_cost, 4),
            "saved_usd": round(saved, 4),
            "savings_percent": round((saved / mono_cost) * 100, 2)
        }
    return cost_data


def run_extended():
    sweep = compute_turn_sweep()
    
    # Financial for the 20-turn bug hunt scenario:
    # From honest_token_analysis:
    mono_in, mono_out = 815000, 8000
    teams_in, teams_out = 393000, 9000
    costs = compute_financial_comparison(mono_in, mono_out, teams_in, teams_out)

    output = {
        "turn_sweep": sweep,
        "financial_analysis_20_turn_bug_hunt": costs
    }

    out_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "extended_results.json")
    with open(out_file, "w") as f:
        json.dump(output, f, indent=2)

    print("\n=======================================================")
    print("        TURN COUNT SCALING SWEEP (3 TO 50 TURNS)       ")
    print("=======================================================")
    for row in sweep:
        print(f"Turns: {row['turns']:>2} | Mono: {row['monolithic_total']:>10,} tok | Teams: {row['agent_teams_total']:>10,} tok | Savings: {row['savings_percent']:>+6.2f}% | Winner: {row['advantage']}")

    print("\n=======================================================")
    print("      FINANCIAL COST SAVINGS (20-Turn Bug Hunt)        ")
    print("=======================================================")
    for model, data in costs.items():
        print(f"{model:<24} | Mono: ${data['monolithic_cost_usd']:.4f} | Teams: ${data['agent_teams_cost_usd']:.4f} | Saved: ${data['saved_usd']:.4f} ({data['savings_percent']}%)")

    return output

if __name__ == "__main__":
    run_extended()
