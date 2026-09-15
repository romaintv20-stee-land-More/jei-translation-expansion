#!/usr/bin/env python3
"""Synchronize upstream/versions.json and upstream/generations.json from completed targets.

The completed packaging registry is the chronological target inventory. This script preserves
richer historical metadata already recorded in the upstream registries, while filling every
completed generation with canonical source, scope, reconstruction and loader metadata.
Unverified future notes that are not completed packaging targets are retained in versions.json.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGING = ROOT / "packaging" / "completed-versions.json"
VERSIONS = ROOT / "upstream" / "versions.json"
GENERATIONS = ROOT / "upstream" / "generations.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def source_path(cfg: dict) -> str:
    mc = cfg["minecraft"]
    name = "en_US.lang" if cfg["format"] == "lang" and mc in {"1.8", "1.8.9", "1.9", "1.9.4", "1.10", "1.10.2"} else (
        "en_us.lang" if cfg["format"] == "lang" else "en_us.json"
    )
    path = ROOT / "upstream" / "sources" / mc / name
    if not path.is_file() and cfg["format"] == "lang":
        alternative = ROOT / "upstream" / "sources" / mc / ("en_us.lang" if name == "en_US.lang" else "en_US.lang")
        if alternative.is_file():
            path = alternative
    if not path.is_file():
        raise FileNotFoundError(f"missing frozen English source for Minecraft {mc}: {path}")
    return path.relative_to(ROOT).as_posix()


def scope_path(mc: str) -> Path:
    return ROOT / "upstream" / f"minecraft-{mc}-language-scope.json"


def audit_path(mc: str) -> Path:
    return ROOT / "upstream" / f"minecraft-{mc}-language-audit.json"


def diff_path(base_mc: str, mc: str) -> Path:
    return ROOT / "upstream" / "diffs" / f"{base_mc}-to-{mc}.json"


def selected_counts(cfg: dict) -> tuple[int | None, int, int, int | None]:
    scope_file = scope_path(cfg["minecraft"])
    if not scope_file.is_file():
        return None, int(cfg["full"]), int(cfg["supplements"]), None
    scope = load(scope_file)
    selected = scope.get("selected_scope_count")
    full = scope.get("addon_full_locale_count")
    if full is None and isinstance(scope.get("addon_full_locales"), list):
        full = len(scope["addon_full_locales"])
    supplements = scope.get("selected_upstream_incomplete_locale_count")
    if supplements is None and isinstance(scope.get("selected_upstream_incomplete_locales"), list):
        supplements = len(scope["selected_upstream_incomplete_locales"])
    if supplements is None:
        supplements = scope.get("upstream_missing_key_supplement_locale_count")
    complete = scope.get("selected_upstream_complete_locale_count")
    if complete is None and isinstance(scope.get("selected_upstream_complete_locales"), list):
        complete = len(scope["selected_upstream_complete_locales"])
    if complete is None:
        complete = scope.get("upstream_complete_selected_locale_count")
    full = int(cfg["full"] if full is None else full)
    supplements = int(cfg["supplements"] if supplements is None else supplements)
    if selected is None and complete is not None:
        selected = full + supplements + int(complete)
    if selected is not None:
        selected = int(selected)
        if complete is None:
            complete = selected - full - supplements
        if full + supplements + int(complete) != selected:
            raise ValueError(f"{cfg['minecraft']}: scope ownership does not sum to selected count")
    if full != int(cfg["full"]) or supplements != int(cfg["supplements"]):
        raise ValueError(
            f"{cfg['minecraft']}: packaging/scope ownership mismatch: "
            f"packaging={cfg['full']}/{cfg['supplements']} scope={full}/{supplements}"
        )
    return selected, full, supplements, None if complete is None else int(complete)


def endpoint_commit(mc: str) -> str | None:
    path = audit_path(mc)
    if not path.is_file():
        return None
    audit = load(path)
    value = audit.get("jei_upstream_commit")
    if isinstance(value, str) and value:
        return value
    endpoint = audit.get("endpoint_resolution", {})
    for key in (
        f"final_{mc.replace('.', '_')}_commit",
        "final_endpoint_commit",
        "final_commit",
        "audited_commit",
    ):
        value = endpoint.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def sync_versions(packaging: dict, current: dict, date: str) -> dict:
    existing = {str(item.get("minecraft")): dict(item) for item in current.get("versions", []) if item.get("minecraft")}
    completed_mcs = {cfg["minecraft"] for cfg in packaging["versions"]}
    verified: list[dict] = []
    for cfg in packaging["versions"]:
        mc = cfg["minecraft"]
        item = existing.get(mc, {})
        item.update({
            "generation": cfg["generation"],
            "minecraft": mc,
            "jei": cfg["jei"],
            "loaders": [cfg.get("loader", "forge")],
            "language_format": cfg["format"],
            "english_source": source_path(cfg),
            "english_key_count": int(cfg["keys"]),
            "java_target": int(cfg["java_target"]),
            "verified": True,
        })
        commit = endpoint_commit(mc)
        if commit:
            item["audited_commit"] = commit
        if cfg.get("loader") == "neoforge":
            item["neoforge"] = cfg["neoforge"]
            item["neoforge_loader_version_range"] = cfg["loader_version_range"]
            item["neoforge_version_range"] = cfg["neoforge_version_range"]
        verified.append(item)

    future = [
        dict(item) for item in current.get("versions", [])
        if str(item.get("minecraft")) not in completed_mcs and not item.get("verified", False)
    ]
    return {
        "schema_version": current.get("schema_version", 1),
        "last_updated": date,
        "upstream_repository": current.get("upstream_repository", "mezz/JustEnoughItems"),
        "audit_status": f"verified-through-{packaging['versions'][-1]['generation'].lower()}",
        "versions": verified + future,
    }


def sync_generations(packaging: dict, current: dict, date: str) -> dict:
    existing = {str(item.get("id")): dict(item) for item in current.get("generations", []) if item.get("id")}
    result: list[dict] = []
    previous_cfg: dict | None = None
    for cfg in packaging["versions"]:
        gid = f"{cfg['generation'].lower()}-mc{cfg['minecraft']}"
        item = existing.get(gid, {})
        selected, full, supplements, complete = selected_counts(cfg)
        item.update({
            "id": gid,
            "minecraft_versions": [cfg["minecraft"]],
            "jei_versions": [cfg["jei"]],
            "source": source_path(cfg),
            "resource_format": cfg["format"],
            "key_count": int(cfg["keys"]),
            "addon_full_locale_count": full,
            "upstream_missing_key_supplement_locale_count": supplements,
            "reconstruction_script": cfg.get("reconstruct_script"),
            "loader": cfg.get("loader", "forge"),
            "java_target": int(cfg["java_target"]),
            "translation_scope_status": "complete-for-selected-scope",
        })
        if selected is not None:
            item["selected_scope_count"] = selected
        if complete is not None:
            item["upstream_complete_selected_locale_count"] = complete
        commit = endpoint_commit(cfg["minecraft"])
        if commit:
            item["audited_commit"] = commit
        scope_file = scope_path(cfg["minecraft"])
        if scope_file.is_file():
            item["minecraft_language_scope"] = scope_file.relative_to(ROOT).as_posix()
        audit_file = audit_path(cfg["minecraft"])
        if audit_file.is_file():
            item["minecraft_language_audit"] = audit_file.relative_to(ROOT).as_posix()
        if previous_cfg is not None:
            previous_gid = f"{previous_cfg['generation'].lower()}-mc{previous_cfg['minecraft']}"
            item["base_generation"] = previous_gid
            diff_file = diff_path(previous_cfg["minecraft"], cfg["minecraft"])
            if diff_file.is_file():
                item["diff_manifest"] = diff_file.relative_to(ROOT).as_posix()
        if cfg.get("loader") == "neoforge":
            item["neoforge"] = cfg["neoforge"]
            item["neoforge_loader_version_range"] = cfg["loader_version_range"]
            item["neoforge_version_range"] = cfg["neoforge_version_range"]
        result.append(item)
        previous_cfg = cfg

    rules = dict(current.get("rules", {}))
    rules.update({
        "same_generation_requires_compatible_keys": True,
        "same_generation_requires_compatible_english_meaning": True,
        "one_release_jar_per_minecraft_version": True,
        "never_group_multiple_minecraft_versions_in_one_jar": True,
        "translation_reuse_between_versions_is_allowed": True,
        "cross_key_reuse_allowed": False,
        "delta_generations_must_be_reconstructed_and_validated_before_release": True,
        "runtime_promotion_is_separate_from_static_validation": True,
    })
    return {
        "schema_version": current.get("schema_version", 1),
        "last_updated": date,
        "status": f"complete-through-{packaging['versions'][-1]['generation'].lower()}",
        "generations": result,
        "rules": rules,
        "notes": "Translation inheritance reduces repeated work but never implies multi-version packaging. Every final Minecraft target reconstructs and validates independently; runtime-tested release promotion remains separate.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default="2026-09-15")
    args = parser.parse_args()
    packaging = load(PACKAGING)
    versions = sync_versions(packaging, load(VERSIONS), args.date)
    generations = sync_generations(packaging, load(GENERATIONS), args.date)
    if len(versions["versions"]) < len(packaging["versions"]):
        raise RuntimeError("versions registry lost completed targets")
    if len(generations["generations"]) != len(packaging["versions"]):
        raise RuntimeError("generation registry does not match completed packaging target count")
    dump(VERSIONS, versions)
    dump(GENERATIONS, generations)
    print(
        f"PASS: synchronized upstream registries through {packaging['versions'][-1]['generation']} / "
        f"Minecraft {packaging['versions'][-1]['minecraft']}"
    )
    print(f"Completed targets: {len(packaging['versions'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
