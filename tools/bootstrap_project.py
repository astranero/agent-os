#!/usr/bin/env python3
"""Create a clean product project from the Agent OS framework."""

import argparse
import shutil
import sys
from pathlib import Path


FRAMEWORK_PATHS = (
    ".ai",
    ".github",
    "tools",
    "tests",
    ".gitignore",
    "requirements.txt",
    "requirements-dev.txt",
)
EXCLUDED_NAMES = {"HANDOFF.md", "__pycache__", ".DS_Store"}


class BootstrapError(ValueError):
    """Raised when a project cannot be created without risking existing files."""


def ignore_source_files(directory, names):
    """Exclude vault-only and generated files from copied directories."""
    return {name for name in names if name in EXCLUDED_NAMES}


def project_readme(project_name, repository):
    return f"""# {project_name}

This project uses [Agent OS](https://github.com/astranero/agent-os) for
role-based, test-driven delivery.

Repository: https://github.com/{repository}

## Development flow

Work starts from a small implementation card, follows the project's
architecture and acceptance criteria, and is delivered through a tested pull
request. The project manager reviews and merges changes after the required
quality gates pass.

## Commands

```text
python3 -m unittest discover -s tests -v
python3 tools/validate_constitution.py
python3 tools/generate_github_templates.py --check
python3 tools/validate_repository_rules.py
```
"""


def bootstrap_project(source_root, target, project_name, repository):
    """Copy the approved framework into a new empty target directory."""
    source_root = Path(source_root).resolve()
    target = Path(target).resolve()
    if target == source_root or source_root in target.parents:
        raise BootstrapError("target must not be the source project or inside it")
    if target.exists():
        if not target.is_dir():
            raise BootstrapError("target exists and is not a directory")
        if any(target.iterdir()):
            raise BootstrapError("target must be empty; no files were changed")
    missing = [path for path in FRAMEWORK_PATHS if not (source_root / path).exists()]
    if missing:
        raise BootstrapError(f"source is missing framework paths: {', '.join(missing)}")

    target.mkdir(parents=True, exist_ok=True)
    for relative_path in FRAMEWORK_PATHS:
        source = source_root / relative_path
        destination = target / relative_path
        if source.is_dir():
            shutil.copytree(source, destination, ignore=ignore_source_files)
        else:
            shutil.copy2(source, destination)
    (target / "README.md").write_text(
        project_readme(project_name, repository), encoding="utf-8"
    )


def build_argument_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--repository", required=True)
    return parser


def main(arguments):
    options = build_argument_parser().parse_args(arguments)
    try:
        bootstrap_project(
            options.source_root, options.target, options.name, options.repository
        )
    except (OSError, BootstrapError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"OK: bootstrapped {options.name} at {options.target}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
