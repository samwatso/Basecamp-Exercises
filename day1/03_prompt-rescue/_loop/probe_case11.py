"""Probe case 11's judge: generate the response once, then run the judge
several times to see the pass rate and the actual failure reasons."""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from runner import load_harness
import candidate

ns = load_harness()
anthropic = ns["anthropic"]
client = anthropic.Anthropic()
cases = ns["_load_cases"](ns["_EVAL_CASES_B64"])["cases"]
c11 = next(c for c in cases if c["id"] == 11)

raw = ns["run_single_prompt"](client, candidate.PROMPTS[0], c11["input"])
parsed, _ = ns["parse_output"](raw)
priority = parsed.get("priority")
response = parsed.get("response")
print("PRIORITY:", priority)
print("RESPONSE:\n", response)
print("\n--- JUDGE x6 ---")
for i in range(6):
    ok, reason = ns["judge_response"](client, c11["input"], priority, response)
    print(f"{i+1}: {'PASS' if ok else 'FAIL'} | {reason}")
