"""
Extended Token & Cost Benchmark Suite for AgentTeams:
1. Scaling sweeps across turn counts (3 to 50 turns).
2. Financial Cost Analysis specifically for Gemini 3.8 Flash (Low, Medium, High).
"""

import json
import os

BASE_AGENT_OVERHEAD = 3500  # System prompt + tool declarations

# Gemini 3.8 Flash Pricing
# Input: $0.075 / 1M tokens
# Output (including thinking/reasoning tokens): $0.30 / 1M tokens
GEMINI_FLASH_RATES = {
    "input": 0.075 / 1e6,
    "output": 0.30 / 1e6
}

# Thinking / reasoning tokens per turn by effort level
THINKING_LEVELS = {
    "Gemini 3.8 Flash (Low)": {
        "thinking_tokens_per_turn": 350,
        "description": "Minimal reasoning overhead; quick execution"
    },
    "Gemini 3.8 Flash (Medium)": {
        "thinking_tokens_per_turn": 1400,
        "description": "Balanced reasoning; standard software tasks"
    },
    "Gemini 3.8 Flash (High)": {
        "thinking_tokens_per_turn": 3800,
        "description": "Deep reasoning; complex architecture & verification"
    },
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


def compute_gemini_flash_financials(mono_in: int, teams_in: int, turns_mono: int, turns_teams: int):
    """
    Calculate costs strictly for Gemini 3.8 Flash across Low, Medium, and High thinking effort.
    """
    cost_data = {}
    for level_name, config in THINKING_LEVELS.items():
        thought_toks = config["thinking_tokens_per_turn"]
        
        # Total output = base response tokens (400 per turn) + thinking tokens
        mono_out = turns_mono * (400 + thought_toks)
        teams_out = turns_teams * (350 + thought_toks)

        mono_cost = (mono_in * GEMINI_FLASH_RATES["input"]) + (mono_out * GEMINI_FLASH_RATES["output"])
        teams_cost = (teams_in * GEMINI_FLASH_RATES["input"]) + (teams_out * GEMINI_FLASH_RATES["output"])
        saved = mono_cost - teams_cost

        cost_data[level_name] = {
            "thinking_effort": level_name.replace("Gemini 3.8 Flash ", "").strip("()"),
            "thinking_tokens_per_turn": thought_toks,
            "monolithic_input_tokens": mono_in,
            "monolithic_output_tokens": mono_out,
            "monolithic_cost_usd": round(mono_cost, 5),
            "agent_teams_input_tokens": teams_in,
            "agent_teams_output_tokens": teams_out,
            "agent_teams_cost_usd": round(teams_cost, 5),
            "dollar_savings_usd": round(saved, 5),
            "savings_percent": round((saved / mono_cost) * 100, 2),
            "description": config["description"]
        }
    return cost_data


def run_extended():
    sweep = compute_turn_sweep()
    
    # 20-Turn Bug Hunt Scenario Context:
    mono_in = 815000
    teams_in = 393000
    turns_mono = 20
    turns_teams = 24  # Captain turns + worker turns

    costs = compute_gemini_flash_financials(mono_in, teams_in, turns_mono, turns_teams)

    output = {
        "turn_sweep": sweep,
        "gemini_3_8_flash_financial_analysis": costs
    }

    out_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "extended_results.json")
    with open(out_file, "w") as f:
        json.dump(output, f, indent=2)

    print("\n==========================================================================")
    print("      GEMINI 3.8 FLASH FINANCIAL COST ANALYSIS (Low, Medium, High)        ")
    print("==========================================================================")
    for level, data in costs.items():
        print(f"\nModel Tier: {level}")
        print(f"  Thinking Tokens/Turn: {data['thinking_tokens_per_turn']:,}")
        print(f"  Monolithic Total Cost:  ${data['monolithic_cost_usd']:.5f}  ({data['monolithic_input_tokens']:,} in, {data['monolithic_output_tokens']:,} out)")
        print(f"  AgentTeams Total Cost:  ${data['agent_teams_cost_usd']:.5f}  ({data['agent_teams_input_tokens']:,} in, {data['agent_teams_output_tokens']:,} out)")
        print(f"  --> DOLLAR SAVINGS:     ${data['dollar_savings_usd']:.5f} ({data['savings_percent']}%)")

    return output

if __name__ == "__main__":
    run_extended()
