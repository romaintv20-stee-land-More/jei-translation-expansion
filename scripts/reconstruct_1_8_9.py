#!/usr/bin/env python3
"""Reconstruct complete JEI 1.8.9 locale files from the 1.8 base + G2 deltas.

By default, files are written under:
  build/reconstructed/1.8.9/assets/jei/lang/

Use --check to reconstruct in a temporary directory and verify the full output
without leaving generated files behind.
"""
from __future__ import annotations

from pathlib import Path
import argparse
import csv
import shutil
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BASE_TRANSLATIONS = ROOT / "translations" / "g1-mc1.8"
BASE_SOURCE = ROOT / "upstream" / "sources" / "1.8" / "en_US.lang"
TARGET_SOURCE = ROOT / "upstream" / "sources" / "1.8.9" / "en_US.lang"
DELTA_DIR = ROOT / "translations" / "g2-mc1.8.9"
DEFAULT_OUTPUT = ROOT / "build" / "reconstructed" / "1.8.9" / "assets" / "jei" / "lang"


def parse_lang(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if "=" not in raw:
            raise ValueError(f"{path}:{lineno}: non-comment line has no '='")
        key, value = raw.split("=", 1)
        key = key.strip()
        if key in data:
            raise ValueError(f"{path}:{lineno}: duplicate key {key}")
        data[key] = value
    return data


def load_delta_rows() -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    for path in sorted(DELTA_DIR.glob("delta-*.tsv")):
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            if not reader.fieldnames or reader.fieldnames[0] != "locale":
                raise ValueError(f"{path}: invalid delta header")
            keys = reader.fieldnames[1:]
            for row in reader:
                locale = (row.get("locale") or "").strip()
                if not locale:
                    raise ValueError(f"{path}: empty locale")
                if locale in rows:
                    raise ValueError(f"duplicate locale in delta batches: {locale}")
                rows[locale] = {key: row.get(key, "") for key in keys}
    return rows


def target_layout() -> list[tuple[str, str | None]]:
    layout: list[tuple[str, str | None]] = []
    for raw in TARGET_SOURCE.read_text(encoding="utf-8").splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            layout.append((raw, None))
            continue
        key, _ = raw.split("=", 1)
        layout.append((raw, key.strip()))
    return layout


def reconstruct_locale(locale: str, delta: dict[str, str], target_keys: set[str]) -> dict[str, str]:
    base_path = BASE_TRANSLATIONS / f"{locale}.lang"
    if not base_path.is_file():
        raise ValueError(f"missing 1.8 base locale: {locale}")

    base = parse_lang(base_path)
    complete = {key: value for key, value in base.items() if key in target_keys}
    complete.update(delta)

    missing = sorted(target_keys - set(complete))
    extra = sorted(set(complete) - target_keys)
    if missing or extra:
        raise ValueError(
            f"{locale}: reconstruction mismatch; missing={missing}, extra={extra}"
        )
    if any(value == "" for value in complete.values()):
        raise ValueError(f"{locale}: reconstructed locale contains an empty value")
    return complete


def write_locale(path: Path, complete: dict[str, str], layout: list[tuple[str, str | None]]) -> None:
    lines: list[str] = []
    for raw, key in layout:
        if key is None:
            lines.append(raw)
        else:
            lines.append(f"{key}={complete[key]}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def reconstruct_all(output: Path, clean: bool = True) -> tuple[int, int]:
    base_source = parse_lang(BASE_SOURCE)
    target = parse_lang(TARGET_SOURCE)
    deltas = load_delta_rows()
    layout = target_layout()

    added = set(target) - set(base_source)
    changed = {key for key in set(base_source) & set(target) if base_source[key] != target[key]}
    expected_delta = added | changed

    if clean and output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True, exist_ok=True)

    for locale, delta in sorted(deltas.items()):
        if set(delta) != expected_delta:
            raise ValueError(f"{locale}: delta key set does not match audited 1.8.9 delta")
        complete = reconstruct_locale(locale, delta, set(target))
        out_path = output / f"{locale}.lang"
        write_locale(out_path, complete, layout)

        reparsed = parse_lang(out_path)
        if reparsed != complete:
            raise ValueError(f"{locale}: written file does not round-trip correctly")
        if set(reparsed) != set(target):
            raise ValueError(f"{locale}: written file does not match target key set")

    return len(deltas), len(target)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="reconstruct to a temporary directory and validate without keeping output",
    )
    args = parser.parse_args()

    if args.check:
        with tempfile.TemporaryDirectory(prefix="jei-1.8.9-reconstruct-") as tmp:
            count, key_count = reconstruct_all(Path(tmp) / "assets" / "jei" / "lang")
        print(f"PASS: reconstructed and verified {count} Minecraft 1.8.9 locale files")
        print(f"Keys per complete locale: {key_count}")
        return 0

    count, key_count = reconstruct_all(args.output)
    print(f"Reconstructed {count} Minecraft 1.8.9 locale files")
    print(f"Keys per complete locale: {key_count}")
    print(f"Output: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
