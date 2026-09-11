#!/usr/bin/env python3
"""Audit the pinned JEI 3.3.3 / Minecraft 1.9 localization endpoint.

This script intentionally performs no translation. It verifies the actual Minecraft
1.9 language asset set, compares it with the project's Minecraft 1.8 language
policy, and measures completeness of JEI's upstream 1.9 locale files.
"""

from __future__ import annotations

import argparse
import json
import urllib.request
from pathlib import Path

PINNED_JEI_COMMIT = "b2ffe6bd7734d093006de99f9dc99b2b77ce780d"
MINECRAFT_ASSET_INDEX_URL = (
    "https://piston-meta.mojang.com/v1/packages/"
    "d7aae43ea69d80cc3441bee4179abd791f6534cd/1.9.json"
)
JEI_RAW_BASE = (
    "https://raw.githubusercontent.com/mezz/JustEnoughItems/"
    f"{PINNED_JEI_COMMIT}/src/main/resources/assets/jei/lang"
)
JEI_LOCALES = [
    "de_DE",
    "en_US",
    "fi_FI",
    "fr_FR",
    "ko_KR",
    "nb_NO",
    "ru_RU",
    "zh_CN",
]
DEBUG_KEYS = {
    "description.jei.wooden.door.1",
    "description.jei.wooden.door.2",
    "description.jei.wooden.door.3",
}


def fetch_bytes(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "JEI-Translation-Expansion-audit"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def fetch_json(url: str) -> dict:
    return json.loads(fetch_bytes(url).decode("utf-8"))


def fetch_text(url: str) -> str:
    return fetch_bytes(url).decode("utf-8")


def parse_lang(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in raw_line:
            continue
        key, value = raw_line.split("=", 1)
        values[key.strip()] = value
    return values


def load_1_8_scope(repo_root: Path) -> dict:
    path = repo_root / "upstream" / "minecraft-1.8-language-scope.json"
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default="build/audit/minecraft-1.9-language-audit.json",
        help="Path for the generated machine-readable audit",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    prior_scope = load_1_8_scope(repo_root)

    asset_index = fetch_json(MINECRAFT_ASSET_INDEX_URL)
    external_languages = sorted(
        Path(name).stem
        for name in asset_index.get("objects", {})
        if name.startswith("minecraft/lang/") and name.endswith(".lang")
    )
    raw_languages = sorted(set(external_languages) | {"en_US"})

    prior_policy = prior_scope["policy"]
    excluded = sorted(set(prior_policy["exclude_novelty_or_fantasy"]) & set(raw_languages))
    deferred = sorted(
        set(prior_policy["defer_regional_or_orthographic_variants"]) & set(raw_languages)
    )

    prior_raw = set(prior_scope["retained_primary_languages"])
    prior_raw.update(prior_policy["exclude_novelty_or_fantasy"])
    prior_raw.update(prior_policy["defer_regional_or_orthographic_variants"])
    current_raw = set(raw_languages)

    added_since_1_8 = sorted(current_raw - prior_raw)
    removed_since_1_8 = sorted(prior_raw - current_raw)
    review_required_new_codes = [
        code for code in added_since_1_8 if code not in excluded and code not in deferred
    ]

    english = parse_lang(fetch_text(f"{JEI_RAW_BASE}/en_US.lang"))
    english_keys = set(english)
    normal_keys = english_keys - DEBUG_KEYS

    upstream_completeness: dict[str, dict] = {}
    for locale in JEI_LOCALES:
        values = parse_lang(fetch_text(f"{JEI_RAW_BASE}/{locale}.lang"))
        keys = set(values)
        normal_present = keys & normal_keys
        missing_normal = sorted(normal_keys - keys)
        extra = sorted(keys - english_keys)
        upstream_completeness[locale] = {
            "key_count": len(keys),
            "normal_key_count_present": len(normal_present),
            "normal_key_count_target": len(normal_keys),
            "missing_normal_key_count": len(missing_normal),
            "missing_normal_keys": missing_normal,
            "extra_key_count": len(extra),
            "extra_keys": extra,
            "complete_for_normal_keys": not missing_normal,
        }

    audit = {
        "schema_version": 1,
        "minecraft": "1.9",
        "jei": "3.3.3",
        "jei_upstream_commit": PINNED_JEI_COMMIT,
        "minecraft_asset_index_url": MINECRAFT_ASSET_INDEX_URL,
        "minecraft_external_language_file_count": len(external_languages),
        "minecraft_raw_language_count_including_en_us": len(raw_languages),
        "minecraft_language_codes": raw_languages,
        "minecraft_has_no_NO": "no_NO" in current_raw,
        "minecraft_has_nb_NO": "nb_NO" in current_raw,
        "comparison_with_1_8_scope": {
            "added_codes": added_since_1_8,
            "removed_codes": removed_since_1_8,
            "carried_exclusions_present": excluded,
            "carried_deferred_variants_present": deferred,
            "new_codes_requiring_policy_review": review_required_new_codes,
        },
        "jei_english": {
            "key_count": len(english_keys),
            "normal_key_count": len(normal_keys),
            "debug_only_key_count": len(DEBUG_KEYS & english_keys),
        },
        "jei_upstream_locales": JEI_LOCALES,
        "jei_upstream_locale_completeness": upstream_completeness,
        "norwegian_reconciliation": {
            "minecraft_locale_code": "no_NO" if "no_NO" in current_raw else None,
            "jei_upstream_locale_code": "nb_NO" if "nb_NO" in JEI_LOCALES else None,
            "nb_NO_exists_in_minecraft_asset_index": "nb_NO" in current_raw,
            "no_NO_exists_in_minecraft_asset_index": "no_NO" in current_raw,
            "conclusion": (
                "Minecraft 1.9 assets contain no_NO and not nb_NO; JEI 3.3.3 ships nb_NO. "
                "Treat no_NO as the Minecraft-facing locale until runtime evidence proves an alias. "
                "Do not rename or overwrite JEI's upstream nb_NO file."
            ),
        },
    }

    output = repo_root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print("PASS: Minecraft 1.9 / JEI 3.3.3 localization audit")
    print(f"Minecraft external .lang files: {len(external_languages)}")
    print(f"Minecraft language codes incl. en_US: {len(raw_languages)}")
    print(f"Added since project 1.8 raw scope: {', '.join(added_since_1_8) or '(none)'}")
    print(f"Removed since project 1.8 raw scope: {', '.join(removed_since_1_8) or '(none)'}")
    print(
        "New codes requiring policy review: "
        + (", ".join(review_required_new_codes) or "(none)")
    )
    print(f"Minecraft no_NO present: {'yes' if 'no_NO' in current_raw else 'no'}")
    print(f"Minecraft nb_NO present: {'yes' if 'nb_NO' in current_raw else 'no'}")
    print("JEI upstream locale completeness (normal keys):")
    for locale in JEI_LOCALES:
        item = upstream_completeness[locale]
        print(
            f"  {locale}: {item['normal_key_count_present']}/{item['normal_key_count_target']} "
            f"missing={item['missing_normal_key_count']}"
        )
    print(f"Wrote: {output.relative_to(repo_root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
