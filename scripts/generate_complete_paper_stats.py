import json
import pandas as pd
from edel.il.eval_stats import compute_paired_statistics

df_100 = pd.read_json('artifacts/experiment_results/benchmark_100_eval/trials.jsonl', lines=True)
df_deep_hol = pd.read_json('artifacts/experiment_results/benchmark_deep_eval/trials.jsonl', lines=True)
df_deep_afp = pd.read_json('artifacts/experiment_results/benchmark_afp_deep_eval/trials.jsonl', lines=True)
df_comb_120 = pd.concat([df_100, df_deep_hol], ignore_index=True)
df_comb_140 = pd.concat([df_100, df_deep_hol, df_deep_afp], ignore_index=True)

for name, df in [
    ('100 Standard Benchmark', df_100),
    ('Tier 4 Deep Structural Benchmark (HOL-Library)', df_deep_hol),
    ('Tier 5 Deep Structural Benchmark (Pure AFP)', df_deep_afp),
    ('Combined 120-Theorem Benchmark', df_comb_120),
    ('Grand Total 140-Theorem Pooled Benchmark', df_comb_140)
]:
    stats = compute_paired_statistics(df, primary_arm='il_treatment', reference_arms=['control_rag', 'baseline'])
    print('='*80)
    print(f"SUITE: {name} (N={stats['n_theorems']} theorems, {len(df)} trials)")
    print('='*80)
    
    # Arm summary
    for arm, d in stats['arm_summary'].items():
        print(f"  {arm:15s}: Pass@1 = {d['pass_count']}/{stats['n_theorems']} ({d['pass_rate']:.1f}%) | "
              f"Mean Comp Tok = {d['mean_comp_tokens']:,.1f} | "
              f"Mean Prompt Tok = {d['mean_prompt_tokens']:,.1f} | "
              f"Mean Turns = {d['mean_turns']:.2f} | "
              f"Mean Errs = {d['mean_errors']:.2f}")
    print('-'*80)
    
    # Pairwise
    for ref in ['control_rag', 'baseline']:
        pw_key = f"il_treatment_vs_{ref}"
        pw = stats['pairwise'][pw_key]
        disc = pw['discordant']
        b, c = disc['b'], disc['c']
        or_val = disc['odds_ratio']
        mcn = pw['mcnemar']
        boot = pw['bootstrap']
        wil = pw['wilcoxon']
        print(f"  I/L vs {ref:12s}: Discordant (b:c) = {b}:{c} (OR = {or_val:.2f})")
        print(f"                    McNemar: 1-sided p = {mcn['p_one_sided']:.4f} | 2-sided p = {mcn['p_two_sided']:.4f}")
        print(f"                    Bootstrap 95% CI: [{boot['delta_pass_ci95'][0]:+.2f}%, {boot['delta_pass_ci95'][1]:+.2f}%] | Prob(I/L > Ref): {boot['prob_primary_greater']*100:.1f}%")
        print(f"                    Wilcoxon Comp Tokens: W = {wil['completion_tokens']['stat']:6.1f}, p = {wil['completion_tokens']['p_value']:.5f}")
        print(f"                    Wilcoxon Turns:       W = {wil['interaction_turns']['stat']:6.1f}, p = {wil['interaction_turns']['p_value']:.5f}")
        print(f"                    Wilcoxon Kernel Errs: W = {wil['error_count']['stat']:6.1f}, p = {wil['error_count']['p_value']:.5f}")
    print()
