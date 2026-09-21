from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PagesDeploymentContractTests(unittest.TestCase):
    def test_pages_workflow_is_manual_and_main_only(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "pages.yml").read_text(encoding="utf-8")

        self.assertIn("workflow_dispatch:", workflow)
        self.assertNotIn("branches:", workflow)
        self.assertIn("github.ref == 'refs/heads/main'", workflow)
        self.assertIn("pages: write", workflow)
        self.assertIn("id-token: write", workflow)
        self.assertIn("name: github-pages", workflow)

    def test_pages_artifact_contains_only_public_runtime_surface(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "pages.yml").read_text(encoding="utf-8")

        self.assertIn("cp index.html privacy.html _site/", workflow)
        self.assertIn("cp -R src public _site/", workflow)
        self.assertIn("touch _site/.nojekyll", workflow)
        self.assertIn("test ! -e _site/prototype", workflow)
        self.assertIn("test ! -e _site/tests", workflow)
        self.assertIn("test ! -e _site/pipeline", workflow)
        self.assertNotIn("path: '.'", workflow)

    def test_pages_actions_use_current_reviewed_majors(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "pages.yml").read_text(encoding="utf-8")
        ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

        self.assertIn("actions/checkout@v7", workflow)
        self.assertIn("actions/configure-pages@v6", workflow)
        self.assertIn("actions/upload-pages-artifact@v5", workflow)
        self.assertIn("actions/deploy-pages@v5", workflow)
        self.assertNotIn("actions/checkout@v4", ci)
        self.assertNotIn("actions/setup-python@v5", ci)
        self.assertIn("actions/checkout@v7", ci)
        self.assertIn("actions/setup-python@v7", ci)

    def test_internal_prototype_is_not_part_of_public_homepage(self) -> None:
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("./prototype/", index)


if __name__ == "__main__":
    unittest.main()
