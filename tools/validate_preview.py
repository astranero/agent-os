"""Validate the provider-neutral visual preview contract."""

import argparse
import json
from pathlib import Path


def validate_preview(preview):
    errors = []
    kind = preview.get("kind")
    if kind not in {"ui", "non-ui"}:
        return ["kind must be 'ui' or 'non-ui'"]

    if kind == "non-ui":
        if preview.get("preview_not_applicable") is not True:
            errors.append("non-ui work must set preview_not_applicable to true")
        return errors

    if not isinstance(preview.get("preview_url"), str) or not preview["preview_url"].strip():
        errors.append("preview_url is required for UI work")
    states = preview.get("states")
    if not isinstance(states, list) or not states or not all(isinstance(state, str) and state.strip() for state in states):
        errors.append("states must contain at least one named UI state")
    if not isinstance(preview.get("accessibility_notes"), str) or not preview["accessibility_notes"].strip():
        errors.append("accessibility_notes is required for UI work")
    return errors


def main(arguments=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("preview_file")
    options = parser.parse_args(arguments)
    preview = json.loads(Path(options.preview_file).read_text(encoding="utf-8"))
    errors = validate_preview(preview)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print("OK: preview contract is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
