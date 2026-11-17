"""Build a source-only ZIP using an explicit delivery allowlist."""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile
import hashlib

root = Path(__file__).resolve().parents[1]
destination = root / "release"
destination.mkdir(exist_ok=True)
archive = destination / "flowharbor-0.1.0-source.zip"
folders = ("frontend", "backend", "deploy", "examples", "tests", "scripts", "docs", "licenses", ".github")
excluded = {"node_modules", "dist", "__pycache__", ".pytest_cache", ".venv", "test-results", "playwright-report", ".ruff_cache"}
files = [root / name for name in ("README.md", "LICENSE", "THIRD_PARTY_NOTICES.md", "CHANGELOG.md", "compose.yaml", ".env.example", ".gitignore", ".gitattributes", ".dockerignore")]
for folder in folders:
    files.extend(path for path in (root / folder).rglob("*") if path.is_file() and not excluded.intersection(path.relative_to(root).parts) and not path.name.startswith(".env") and path.suffix not in {".pyc", ".log"})
with ZipFile(archive, "w", compression=ZIP_DEFLATED) as package:
    for path in sorted(files):
        package.write(path, Path("flowharbor") / path.relative_to(root))
digest = hashlib.sha256(archive.read_bytes()).hexdigest()
(destination / "SHA256SUMS.txt").write_text(f"{digest}  {archive.name}\n", encoding="utf-8")
print(f"{archive}\nSHA256: {digest}\nFiles: {len(files)}")
