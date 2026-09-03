from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_content.py"


def load_validator():
    spec = spec_from_file_location("validate_content", VALIDATOR)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ContentFrontMatterTests(unittest.TestCase):
    def test_every_post_markdown_starts_and_closes_front_matter(self):
        failures = []
        for path in sorted((ROOT / "content" / "posts").rglob("*.md")):
            text = path.read_text(encoding="utf-8")
            if not text.startswith("---\n") or "\n---\n" not in text[4:]:
                failures.append(str(path.relative_to(ROOT)))

        self.assertEqual([], failures, "Invalid front matter: " + ", ".join(failures))

    def test_content_validator_script_exists(self):
        assert VALIDATOR.is_file(), f"Missing validator: {VALIDATOR}"

    def test_validator_exposes_tree_validation(self):
        validator = load_validator()
        assert callable(getattr(validator, "validate_tree", None))

    def test_validator_exposes_cli_main(self):
        validator = load_validator()
        assert callable(getattr(validator, "main", None))

    def test_validator_rejects_missing_front_matter(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "index.md").write_text("Body only\n", encoding="utf-8")
            errors = validator.validate_tree(root)

        assert any("front matter" in error for error in errors), errors

    def test_validator_rejects_missing_required_field(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "index.md").write_text(
                "---\ndate: 2026-01-01\ndraft: true\ndescription: Test\ntags: [test]\n---\nBody\n",
                encoding="utf-8",
            )
            errors = validator.validate_tree(root)

        assert any("title" in error for error in errors), errors

    def test_validator_rejects_ipv4_addresses(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "index.md").write_text(
                "---\ntitle: Test\ndate: 2026-01-01\ndraft: true\ndescription: Test\ntags: [test]\n---\nServer: 192.168.10.25\n",
                encoding="utf-8",
            )
            errors = validator.validate_tree(root)

        assert any("IPv4" in error for error in errors), errors

    def test_validator_rejects_literal_credentials(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "index.md").write_text(
                "---\ntitle: Test\ndate: 2026-01-01\ndraft: true\ndescription: Test\ntags: [test]\n---\npassword = \"hunter2\"\n",
                encoding="utf-8",
            )
            errors = validator.validate_tree(root)

        assert any("credential" in error for error in errors), errors

    def test_validator_rejects_authorization_bearer_tokens(self):
        validator = load_validator()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "index.md").write_text(
                "---\ntitle: Test\ndate: 2026-01-01\ndraft: true\ndescription: Test\ntags: [test]\n---\nAuthorization: Bearer abcdefghijklmnop\n",
                encoding="utf-8",
            )
            errors = validator.validate_tree(root)

        assert any("credential" in error for error in errors), errors

    def test_generated_public_directory_is_ignored(self):
        ignored = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        assert "/public/" in ignored

    def test_pull_requests_build_but_do_not_deploy(self):
        workflow = (ROOT / ".github" / "workflows" / "hugo.yaml").read_text(encoding="utf-8")
        assert "pull_request:" in workflow
        assert "if: github.event_name == 'push'" in workflow
        assert workflow.count("if: github.event_name == 'push'") == 3
        assert "python3 scripts/validate_content.py" in workflow


if __name__ == "__main__":
    unittest.main()
