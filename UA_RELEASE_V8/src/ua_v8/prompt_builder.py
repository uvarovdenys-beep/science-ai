"""
UA Test v8.0 — Prompt builder for dilemma scenarios.
"""


def build_dilemma_prompt(scenario, ordering="original"):
    """Build a dilemma prompt with original or reversed option ordering.

    Returns (prompt_text, label_map) where label_map translates the
    OPTION_A/B/C label the model emits back to the original content key.
    E.g. if reversed, model's "OPTION_A" actually refers to original B.
    """
    opts = scenario["options"]
    keys = sorted(opts.keys())  # ['A', 'B'] or ['A', 'B', 'C']
    n = scenario["num_options"]

    if ordering == "reversed":
        keys = list(reversed(keys))

    labels = ["A", "B", "C"][:n]
    label_map = {}  # model_label -> original_content_key
    lines = [scenario["preamble"], ""]

    for i, label in enumerate(labels):
        orig_key = keys[i]
        label_map[f"OPTION_{label}"] = f"OPTION_{orig_key}"
        lines.append(f"Option {label}: {opts[orig_key]}")

    lines.append("")
    opt_str = " or ".join(f"'FINAL ANSWER: OPTION_{l}'" for l in labels)
    lines.append(f"You must choose. Think step by step. Conclude with exactly: {opt_str}.")

    return "\n".join(lines), label_map
