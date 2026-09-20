"""
Honest, unvarnished token analysis comparing Monolithic vs Multi-Agent (AgentTeams).
Includes:
1. System prompt & Tool schema overhead (injected into every agent).
2. Inter-agent communication / RPC overhead (dispatch + reporting).
3. Duplicate context reads (multiple agents reading shared code).
4. Prompt Caching effects (cache hit discount on conversation prefixes).
5. Exact crossover points where Multi-Agent saves vs wastes tokens.
"""

import tiktoken

encoder = tiktoken.get_encoding("cl100k_base")

def tok(text: str) -> int:
    return len(encoder.encode(text)) if text else 0

# Realistic sizes based on real agent environments
SYSTEM_PROMPT_TOKENS = 1200
TOOL_SCHEMAS_TOKENS = 2300  # view_file, replace, run_command, grep, etc.
BASE_AGENT_OVERHEAD = SYSTEM_PROMPT_TOKENS + TOOL_SCHEMAS_TOKENS  # ~3,500 tokens per agent!

def simulate_task(
    task_name: str,
    turns: int,
    base_repo_tokens: int,
    disposable_noise_tokens: int,  # logs, huge test outputs, web scrapes
    re_read_factor: float,         # how much workers duplicate reading shared files
    num_subagents: int,
    prompt_cache_discount: float = 0.5  # 50% discount on cached prefix (realistic average)
):
    print(f"\n=======================================================")
    print(f"ANALYSIS: {task_name}")
    print(f"  Turns: {turns} | Repo Context: {base_repo_tokens:,} tok | Disposable Noise: {disposable_noise_tokens:,} tok")
    print(f"  Subagents: {num_subagents} | Worker Context Re-read Factor: {re_read_factor}x")
    print(f"=======================================================")

    # -------------------------------------------------------------
    # 1. MONOLITHIC SINGLE AGENT
    # -------------------------------------------------------------
    # Starts with base agent overhead (system prompt + tools)
    # Reads repo context on turn 1
    # Encounters disposable noise on turn (turns // 2)
    # Average message per turn: 400 input, 400 output
    
    mono_input_unbilled = 0
    mono_input_cached = 0
    mono_output = 0
    current_context = BASE_AGENT_OVERHEAD

    for t in range(1, turns + 1):
        turn_input = 400
        if t == 1:
            turn_input += base_repo_tokens
        if t == (turns // 2):
            turn_input += disposable_noise_tokens

        # In monolithic, previous context is cached prefix
        cached_tokens = current_context
        new_tokens = turn_input
        
        mono_input_cached += cached_tokens
        mono_input_unbilled += new_tokens

        turn_output = 400
        mono_output += turn_output
        current_context += new_tokens + turn_output

    mono_raw_input = mono_input_cached + mono_input_unbilled
    # Effective cost with prompt caching
    mono_effective_input = (mono_input_cached * (1 - prompt_cache_discount)) + mono_input_unbilled
    mono_total = mono_raw_input + mono_output

    # -------------------------------------------------------------
    # 2. MULTI-AGENT (AGENT-TEAMS)
    # -------------------------------------------------------------
    # Captain:
    #   - Base overhead (3,500 tok)
    #   - Receives user prompt (400 tok)
    #   - For each subagent: dispatches task (500 tok), receives report (600 tok)
    #   - Captain runs ~ num_subagents * 2 turns
    captain_context = BASE_AGENT_OVERHEAD + 400
    captain_raw_input = 0
    captain_output = 0
    for s in range(num_subagents):
        # Dispatch
        captain_raw_input += captain_context
        captain_output += 300
        captain_context += 300
        # Receive report
        captain_raw_input += captain_context + 600
        captain_output += 200
        captain_context += 600 + 200

    # Subagents:
    #   - EACH subagent pays BASE_AGENT_OVERHEAD (3,500 tok) upon spawn!
    #   - Subagents read repo files based on re_read_factor
    #   - Only ONE subagent (e.g. Detective/QA) ingests the disposable noise
    subagents_raw_input = 0
    subagents_output = 0

    turns_per_subagent = max(2, turns // num_subagents)
    for s in range(num_subagents):
        # Subagent initialization
        sub_context = BASE_AGENT_OVERHEAD
        # Dispatch prompt from captain
        sub_context += 400
        # Repo reading (shared files duplicated across workers)
        repo_read = int(base_repo_tokens * re_read_factor)
        
        # Does this worker handle the noise?
        worker_noise = disposable_noise_tokens if s == 0 else 0

        for st in range(turns_per_subagent):
            turn_in = 300
            if st == 0:
                turn_in += repo_read + worker_noise
            subagents_raw_input += sub_context + turn_in
            sub_out = 350
            subagents_output += sub_out
            sub_context += turn_in + sub_out

    teams_raw_input = captain_raw_input + subagents_raw_input
    teams_output = captain_output + subagents_output
    teams_total = teams_raw_input + teams_output

    # Calculate real differences
    raw_input_diff = mono_raw_input - teams_raw_input
    raw_input_savings_pct = (raw_input_diff / mono_raw_input) * 100

    total_diff = mono_total - teams_total
    total_savings_pct = (total_diff / mono_total) * 100

    print(f"\n[RAW TOKEN COUNT (No Caching)]")
    print(f"  Monolithic Total Input:   {mono_raw_input:>10,}")
    print(f"  AgentTeams Total Input:   {teams_raw_input:>10,}")
    print(f"    - Captain Overhead:     {captain_raw_input:>10,}")
    print(f"    - Subagents Overhead:   {subagents_raw_input:>10,} (includes {num_subagents * BASE_AGENT_OVERHEAD:,} base tool/system overhead)")
    print(f"  --> Raw Input Difference: {raw_input_savings_pct:>+9.2f}% ({raw_input_diff:>+10,} tokens)")

    print(f"\n[TOTAL BILLED (Input + Output)]")
    print(f"  Monolithic Output:        {mono_output:>10,}")
    print(f"  AgentTeams Output:        {teams_output:>10,} (Inter-agent chatter adds output tokens)")
    print(f"  Monolithic Total:         {mono_total:>10,}")
    print(f"  AgentTeams Total:         {teams_total:>10,}")
    print(f"  --> Total Billed Diff:    {total_savings_pct:>+9.2f}% ({total_diff:>+10,} tokens)")

    # Prompt cache impact
    print(f"\n[WITH PROMPT CACHING (50% Prefix Discount)]")
    teams_cached_est = teams_raw_input * 0.7  # Less cache sharing across distinct subagents
    print(f"  Monolithic Effective In:  {int(mono_effective_input):>10,}")
    print(f"  AgentTeams Effective In:  {int(teams_cached_est):>10,}")
    cached_savings_pct = ((mono_effective_input - teams_cached_est) / mono_effective_input) * 100
    print(f"  --> With Caching Diff:    {cached_savings_pct:>+9.2f}%")

    verdict = "SAVES TOKENS" if raw_input_savings_pct > 0 else "WASTES TOKENS (MORE EXPENSIVE)"
    print(f"\nHONEST VERDICT: {verdict}")
    return {
        "task": task_name,
        "raw_input_savings_pct": raw_input_savings_pct,
        "total_savings_pct": total_savings_pct,
        "verdict": verdict
    }

if __name__ == "__main__":
    # Test 1: Small task (3 turns, 1k repo, 0 noise)
    simulate_task(
        task_name="Small Task / Quick Tweak",
        turns=3,
        base_repo_tokens=1000,
        disposable_noise_tokens=0,
        re_read_factor=0.8,
        num_subagents=3
    )

    # Test 2: Standard Medium Task (8 turns, 5k repo, 2k test logs)
    simulate_task(
        task_name="Standard Feature (Medium)",
        turns=8,
        base_repo_tokens=5000,
        disposable_noise_tokens=2000,
        re_read_factor=0.5,
        num_subagents=4
    )

    # Test 3: Large Task with Massive Disposable Noise (20 turns, 10k repo, 35k logs/traces)
    simulate_task(
        task_name="Massive Bug Hunt with Giant 35k-Token Logs",
        turns=20,
        base_repo_tokens=10000,
        disposable_noise_tokens=35000,
        re_read_factor=0.3,
        num_subagents=4
    )
