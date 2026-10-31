"""
Safety wrapper: ensures scripts/generate_rules.py generates only official rules
without dummy placeholder texts.
"""
from scripts.generate_official_rules import generate_official_rules

if __name__ == "__main__":
    generate_official_rules()
