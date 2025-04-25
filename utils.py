import json


def load_debate_config(config_file):
    """Load debate configuration from a JSON file."""
    with open(config_file, "r") as f:
        return json.load(f)
