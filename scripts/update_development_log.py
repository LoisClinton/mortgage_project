#!/usr/bin/env python3
"""Append a completed commit to DEVELOPMENT_LOG.md."""

from __future__ import annotations

import argparse
import re
import subprocess
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = ROOT / "DEVELOPMENT_LOG.md"
TEST_COMMAND = "python3 -m unittest discover -s tests -v"


def git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def markdown_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def test_result() -> str:
    result = subprocess.run(
        TEST_COMMAND.split(),
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    output = f"{result.stdout}\n{result.stderr}"
    match = re.search(r"Ran (\d+) tests?", output)
    count = f"{match.group(1)} tests" if match else "tests"
    outcome = "passed" if result.returncode == 0 else f"failed (exit code {result.returncode})"
    return f"`{TEST_COMMAND}` — {count} {outcome}."


def remote_commit_link(commit_sha: str) -> str:
    try:
        remote = git("remote", "get-url", "origin")
    except subprocess.CalledProcessError:
        return f"`{commit_sha[:7]}`"
    remote = re.sub(r"\.git$", "", remote)
    if remote.startswith("git@github.com:"):
        remote = "https://github.com/" + remote.removeprefix("git@github.com:")
    return f"[{commit_sha[:7]}]({remote}/commit/{commit_sha})"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("commit", nargs="?", default="HEAD")
    args = parser.parse_args()

    commit_sha = git("rev-parse", args.commit)
    existing_log = LOG_PATH.read_text(encoding="utf-8")
    if commit_sha[:7] in existing_log:
        return

    commit_date = git("show", "-s", "--format=%cs", commit_sha)
    subject = git("show", "-s", "--format=%s", commit_sha)
    changed_files = git(
        "diff-tree", "--no-commit-id", "--name-only", "-r", commit_sha
    ).splitlines()
    changed = ", ".join(f"`{markdown_cell(path)}`" for path in changed_files)
    changed = changed or "No files listed"
    if len(changed) > 160:
        changed = changed[:157] + "..."

    row = (
        f"| {commit_date or date.today().isoformat()} | "
        f"{remote_commit_link(commit_sha)} | {markdown_cell(subject)} "
        f"{changed}. | {test_result()} | "
        "Recorded automatically after the commit for traceability and reproducible "
        "development evidence. |\n"
    )

    lines = existing_log.splitlines(keepends=True)
    placeholder_index = next(
        (index for index, line in enumerate(lines) if line.startswith("| [date]")),
        len(lines),
    )
    lines.insert(placeholder_index, row)
    LOG_PATH.write_text("".join(lines), encoding="utf-8")
    print(f"Added {commit_sha[:7]} to {LOG_PATH.name}; review and commit the log update.")


if __name__ == "__main__":
    main()
