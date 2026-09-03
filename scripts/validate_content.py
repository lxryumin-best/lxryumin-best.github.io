#!/usr/bin/env python3
"""Validate Hugo portfolio content before build and publication."""

from pathlib import Path
import re
import sys


IPV4_RE = re.compile(r"(?<![\d.])(?:25[0-5]|2[0-4]\d|1?\d?\d)(?:\.(?:25[0-5]|2[0-4]\d|1?\d?\d)){3}(?![\d.])")
CREDENTIAL_RE = re.compile(
    r"(?im)(?:\b(?:password|passwd|pass|token|api[_-]?key|secret)\s*[:=]\s*[\"']?(?![$<])[^\s\"']{4,}"
    r"|\bauthorization\s*:\s*(?:bearer|basic)\s+(?![$<])\S{6,}"
    r"|-----BEGIN [A-Z ]*PRIVATE KEY-----)"
)


def validate_tree(content_root: Path) -> list[str]:
    """Return validation errors for a Hugo content tree."""
    errors: list[str] = []
    for path in sorted(content_root.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---\n") or "\n---\n" not in text[4:]:
            errors += [f"{path}: missing or unclosed front matter"]
            continue
        end = text.find("\n---\n", 4)
        front_matter = text[4:end]
        for field in ("title", "date", "draft", "description", "tags"):
            if re.search(rf"(?m)^{field}\s*:", front_matter) is None:
                errors += [f"{path}: missing required field '{field}'"]
        if re.findall(IPV4_RE, text):
            errors += [f"{path}: contains an IPv4 address"]
        if re.findall(CREDENTIAL_RE, text):
            errors += [f"{path}: contains a literal credential"]
    return errors


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    root = Path(args[0]) if args else Path("content/posts")
    errors = validate_tree(root)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(f"Content validation passed: {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
