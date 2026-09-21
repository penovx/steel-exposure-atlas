from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SELF = Path(__file__).resolve()

TEXT_SUFFIXES = {
    ".py", ".js", ".mjs", ".css", ".html", ".md", ".json",
    ".yml", ".yaml", ".txt", ".gitignore",
}

SECRET_PATTERNS = {
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "GitHub classic token": re.compile(r"ghp_[A-Za-z0-9]{30,}"),
    "GitHub fine-grained token": re.compile(r"github_pat_[A-Za-z0-9_]{30,}"),
    "OpenAI-style secret": re.compile(r"sk-(?:proj-)?[A-Za-z0-9_-]{20,}"),
    "AWS access key": re.compile(r"AKIA[0-9A-Z]{16}"),
}

LOCAL_PATH_PATTERNS = {
    "macOS user path": re.compile(r"/Users/[A-Za-z0-9._-]+/"),
    "Linux user path": re.compile(r"/home/[A-Za-z0-9._-]+/"),
    "Windows user path": re.compile(r"[A-Za-z]:\\\\Users\\\\[^\\\\]+\\\\"),
}


def text_files() -> list[Path]:
    result: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.resolve() == SELF:
            continue
        if any(part in {".git", "tmp", "_site"} for part in path.parts):
            continue
        if path.suffix.lower() in TEXT_SUFFIXES or path.name == ".gitignore":
            result.append(path)
    return result


class RepositoryHygieneContractTests(unittest.TestCase):
    def test_no_obvious_secret_material_is_committed(self) -> None:
        findings: list[str] = []
        for path in text_files():
            text = path.read_text(encoding="utf-8", errors="ignore")
            for label, pattern in SECRET_PATTERNS.items():
                if pattern.search(text):
                    findings.append(f"{path.relative_to(ROOT)}: {label}")
        self.assertEqual(findings, [], "\n".join(findings))

    def test_no_local_user_paths_are_committed(self) -> None:
        findings: list[str] = []
        for path in text_files():
            text = path.read_text(encoding="utf-8", errors="ignore")
            for label, pattern in LOCAL_PATH_PATTERNS.items():
                if pattern.search(text):
                    findings.append(f"{path.relative_to(ROOT)}: {label}")
        self.assertEqual(findings, [], "\n".join(findings))


if __name__ == "__main__":
    unittest.main()
