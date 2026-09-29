import json

with open('artifacts/experiment_results/benchmark_deep_eval/trials.jsonl') as f:
    trials = [json.loads(line) for line in f]

print(f"Total trials: {len(trials)}")
arms = {}
for t in trials:
    arm = t['arm']
    if arm not in arms:
        arms[arm] = {
            'n': 0, 'success': 0, 'turns': 0, 'time': 0.0, 'cost': 0.0,
            'prompt_tok': 0, 'comp_tok': 0, 'total_tok': 0,
            'cache_write': 0, 'cache_read': 0
        }
    a = arms[arm]
    a['n'] += 1
    if t['success']:
        a['success'] += 1
    a['turns'] += t.get('interaction_turns', 0)
    a['time'] += t.get('elapsed_seconds', 0.0)
    a['cost'] += t.get('cost_usd', 0.0)
    a['prompt_tok'] += t.get('prompt_tokens', 0)
    a['comp_tok'] += t.get('completion_tokens', 0)
    a['total_tok'] += t.get('total_tokens', 0)
    a['cache_write'] += t.get('cache_creation_tokens', 0)
    a['cache_read'] += t.get('cache_read_tokens', 0)

for arm, a in arms.items():
    n = a['n']
    print('='*50)
    print(f"Arm: {arm} (N={n})")
    print(f"  Success: {a['success']}/{n} ({a['success']/n*100:.1f}%)")
    print(f"  Mean Turns: {a['turns']/n:.2f}")
    print(f"  Mean Time: {a['time']/n:.2f}s (Total: {a['time']:.1f}s)")
    print(f"  Total Cost: ${a['cost']:.4f} (Mean: ${a['cost']/n:.4f})")
    print(f"  Prompt Tokens: {a['prompt_tok']:,} (Mean: {a['prompt_tok']/n:,.0f})")
    print(f"  Comp Tokens:   {a['comp_tok']:,} (Mean: {a['comp_tok']/n:,.0f})")
    print(f"  Total Tokens:  {a['total_tok']:,} (Mean: {a['total_tok']/n:,.0f})")
    print(f"  Cache Write:   {a['cache_write']:,}")
    print(f"  Cache Read:    {a['cache_read']:,}")

total_cost = sum(a['cost'] for a in arms.values())
print('='*50)
print(f"Total Tier 4 Cost: ${total_cost:.4f}")
