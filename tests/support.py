"""Shared test helpers: where the skill lives, and a small valid plan to bend in each test."""

import copy
import os
import sys

sys.dont_write_bytecode = True
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(ROOT, "skills", "week-planner")
SCRIPTS = os.path.join(SKILL, "scripts")
EXAMPLES = os.path.join(SKILL, "examples")
sys.path.insert(0, SCRIPTS)

_BASE = {
    "days": [
        {"date": "2026-10-04", "free_hours": 2, "items": [{"title": "Pick a direction", "kind": "decision", "hours": 1}]},
        {"date": "2026-10-05", "free_hours": 3, "items": [{"title": "Run the checks", "stage": "active", "hours": 2}]},
        {"date": "2026-10-06", "free_hours": 2, "items": [{"kind": "buffer", "hours": 1}]},
    ]
}


def plan(**changes):
    data = copy.deepcopy(_BASE)
    data.update(changes)
    return data


def examples():
    return sorted(os.path.join(EXAMPLES, f) for f in os.listdir(EXAMPLES) if f.endswith(".json"))
