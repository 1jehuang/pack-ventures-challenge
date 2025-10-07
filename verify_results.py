#!/usr/bin/env python3
"""
Verify that founders.json contains the correct founder information.
Expected results are based on web research conducted earlier.
"""

import json
from pathlib import Path

# Expected results based on web research
EXPECTED_RESULTS = {
    "Approval AI": ["Arjun Lalwani", "Helly Shah"],
    "Meteor": ["Pranav Madhukar", "Farhan Khan"],
    "Read AI": ["David Shim", "Robert Williams", "Elliott Waldron"],
    "Profound": ["James Cadwallader", "Dylan Babbs"],
    "Wayfinder Bio": ["Jason Fontana", "David Sparkman-Yager", "Chuhern Hwang"],
    "Modulus Therapeutics": ["Max Darnell", "Bryce Daines"],
    "Persephone Bio": ["Stephanie Culler", "Steve Van Dien"],
    "Casium": ["Priyanka Kulkarni"],
    "Kernel": ["Catherine Jue", "Rafael Garcia"],
    "Rosie": ["Mitra Raman", "Karthika Shankar"]
}

def normalize_names(names):
    """Normalize a list of names for comparison (case-insensitive, sorted)"""
    return sorted([name.strip().lower() for name in names])

def verify_results():
    """Verify founders.json against expected results"""

    # Load the generated results
    results_file = Path("founders.json")
    if not results_file.exists():
        print("❌ founders.json not found!")
        return False

    with open(results_file) as f:
        actual_results = json.load(f)

    print("=" * 60)
    print("VERIFICATION REPORT")
    print("=" * 60)
    print()

    all_correct = True

    for company, expected_founders in EXPECTED_RESULTS.items():
        print(f"Checking: {company}")

        if company not in actual_results:
            print(f"  ❌ MISSING from results!")
            all_correct = False
            continue

        actual_founders = actual_results[company]

        # Normalize for comparison (order doesn't matter)
        expected_normalized = normalize_names(expected_founders)
        actual_normalized = normalize_names(actual_founders)

        if expected_normalized == actual_normalized:
            print(f"  ✅ CORRECT ({len(actual_founders)} founders)")
            print(f"     {actual_founders}")
        else:
            print(f"  ❌ MISMATCH!")
            print(f"     Expected: {expected_founders}")
            print(f"     Got:      {actual_founders}")

            # Show what's missing/extra
            expected_set = set(expected_normalized)
            actual_set = set(actual_normalized)

            missing = expected_set - actual_set
            extra = actual_set - expected_set

            if missing:
                print(f"     Missing: {missing}")
            if extra:
                print(f"     Extra: {extra}")

            all_correct = False

        print()

    print("=" * 60)
    if all_correct:
        print("🎉 ALL RESULTS CORRECT!")
    else:
        print("⚠️  SOME RESULTS INCORRECT - Review above")
    print("=" * 60)

    return all_correct

if __name__ == '__main__':
    success = verify_results()
    exit(0 if success else 1)
