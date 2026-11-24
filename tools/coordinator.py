"""Create deterministic, least-privilege work claims for Ready cards."""

import argparse
import json
from pathlib import Path

import yaml

from tools.validate_card import validate_card


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = PROJECT_ROOT / ".ai" / "policies" / "role-permissions.yaml"


def _load_manifest():
    return yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))


def _load_claims(path):
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def claim_card(card_path, role, claim_id, owned_paths, dependencies, claims_path, output_path):
    card_text = Path(card_path).read_text(encoding="utf-8")
    errors = validate_card(card_text, stage="ready")
    if errors:
        raise ValueError("card is not Ready: " + "; ".join(errors))

    manifest = _load_manifest()
    role_definition = manifest.get("roles", {}).get(role)
    if role_definition is None:
        raise ValueError(f"unknown role: {role}")
    required = {"claim_ready_card", "create_branch", "open_draft_pull_request"}
    if not required.issubset(set(role_definition.get("can", []))):
        raise ValueError(f"role {role} cannot claim Ready work")
    if any(capability in role_definition.get("can", []) for capability in (
        "merge_pull_request", "modify_branch_protection", "disable_security_workflows",
    )):
        raise ValueError(f"role {role} has forbidden authority")

    normalized_paths = sorted(set(owned_paths))
    claims = _load_claims(Path(claims_path))
    claimed_paths = {
        path for claim in claims if claim.get("status") == "claimed"
        for path in claim.get("owned_paths", [])
    }
    overlap = claimed_paths.intersection(normalized_paths)
    if overlap:
        raise ValueError("owned path already claimed: " + ", ".join(sorted(overlap)))

    known_claims = {claim.get("claim_id") for claim in claims}
    missing = sorted(set(dependencies).difference(known_claims))
    if missing:
        raise ValueError("unknown dependency claim: " + ", ".join(missing))

    record = {
        "card": str(Path(card_path).resolve()),
        "claim_id": claim_id,
        "dependencies": sorted(set(dependencies)),
        "owned_paths": normalized_paths,
        "role": role,
        "status": "claimed",
    }
    output_path = Path(output_path)
    output_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    claims.append(record)
    Path(claims_path).write_text(json.dumps(claims, indent=2) + "\n", encoding="utf-8")
    return record


def main(arguments=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--card", required=True)
    parser.add_argument("--role", required=True)
    parser.add_argument("--claim-id", required=True)
    parser.add_argument("--owned-path", action="append", required=True)
    parser.add_argument("--dependency", action="append", default=[])
    parser.add_argument("--claims", default=".ai/claims.json")
    parser.add_argument("--output", required=True)
    options = parser.parse_args(arguments)
    claim_card(
        options.card, options.role, options.claim_id, options.owned_path,
        options.dependency, options.claims, options.output,
    )


if __name__ == "__main__":
    main()
