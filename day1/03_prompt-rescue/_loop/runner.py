"""
Standalone eval runner for the Prompt Rescue workshop.

Execs the notebook's REAL harness (cell 5) so scoring is byte-identical to what
the notebook produces, then runs a candidate prompt (or chain) defined in
candidate.py and prints a detailed per-case / per-criterion failure breakdown.

Usage:
    python runner.py            # run whatever candidate.py defines
"""
import json
import os
import sys
import time
import importlib

NB_PATH = os.path.join(
    os.path.dirname(__file__), "..", "Prompt_Rescue_solo.ipynb"
)


def load_harness():
    """Extract cell 5 (the eval harness) from the notebook and exec it."""
    with open(NB_PATH, encoding="utf-8") as f:
        nb = json.load(f)
    harness_src = None
    for c in nb["cells"]:
        if c["cell_type"] != "code":
            continue
        src = "".join(c["source"])
        if "_EVAL_CASES_B64" in src and "def run_eval" in src:
            harness_src = src
            break
    if harness_src is None:
        raise RuntimeError("Could not find harness cell in notebook")
    ns = {"__name__": "_harness"}
    exec(compile(harness_src, "<harness>", "exec"), ns)
    return ns


def detailed_report(eval_result, cases_by_id):
    """Print a per-case, per-criterion breakdown of failures."""
    print("\n" + "=" * 70)
    print("DETAILED FAILURE BREAKDOWN")
    print("=" * 70)
    for r in eval_result["results"]:
        if r["pass"]:
            continue
        cid = r["case_id"]
        case = cases_by_id[cid]
        print(f"\n--- Case {cid} [{r['category']}] gold_priority={case['gold_priority']}")
        for name, crit in r["criteria"].items():
            mark = "OK " if crit["pass"] else "XX "
            print(f"   {mark}{name}: {crit['reason']}")
        # show a trimmed raw output for debugging
        raw = r.get("raw_output", "")
        snippet = raw[:400].replace("\n", " ")
        print(f"   raw: {snippet}")

    print("\n" + "=" * 70)
    print("CATEGORY SUMMARY")
    print("=" * 70)
    for k, v in eval_result["categories"].items():
        print(f"   {v['label']:<24} {v['passed']}/{v['total']}")
    tp = eval_result["total_passed"]
    tc = eval_result["total_cases"]
    print(f"\n   TOTAL: {tp}/{tc}  ({round(100*tp/tc)}%)")


def main():
    ns = load_harness()
    run_eval = ns["run_eval"]
    _load_cases = ns["_load_cases"]
    b64 = ns["_EVAL_CASES_B64"]
    anthropic = ns["anthropic"]

    client = anthropic.Anthropic()
    cases_data = _load_cases(b64)
    cases_by_id = {c["id"]: c for c in cases_data["cases"]}

    # Reload candidate each run so edits are picked up
    sys.path.insert(0, os.path.dirname(__file__))
    import candidate
    importlib.reload(candidate)
    prompts = candidate.PROMPTS
    label = getattr(candidate, "LABEL", "candidate")

    mode = "single" if len(prompts) == 1 else f"{len(prompts)}-step chain"
    print(f"Label: {label}  |  Mode: {mode}  |  Model: {ns['MODEL']}")
    start = time.time()
    result = run_eval(client, prompts, cases_data)
    print(f"\nCompleted in {time.time()-start:.1f}s")
    detailed_report(result, cases_by_id)


if __name__ == "__main__":
    main()
