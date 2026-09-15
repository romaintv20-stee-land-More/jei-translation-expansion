#!/usr/bin/env python3
"""Validate frozen Minecraft 26.2 / JEI 30.32.0 source, ownership, and reuse metadata."""
from __future__ import annotations

import json

import reconstruct_26_2 as g51


def main() -> int:
    base, target = g51.verify_semantics()
    scope = json.loads(g51.SCOPE_PATH.read_text(encoding="utf-8"))
    diff = json.loads(g51.DIFF_PATH.read_text(encoding="utf-8"))
    policy = json.loads(g51.POLICY_PATH.read_text(encoding="utf-8"))
    normal = {k for k in target if not k.startswith(g51.DEBUG_PREFIX)}

    if base != target:
        raise ValueError("G51 English source is no longer byte-semantically identical to G50 after JSON cleaning")
    if (len(target), len(normal), len(target) - len(normal)) != (334, 328, 6):
        raise ValueError("G51 target source counts changed")
    if (
        diff.get("unchanged_key_and_value_count"),
        diff.get("added_key_count"),
        diff.get("removed_key_count"),
        diff.get("changed_english_value_count"),
    ) != (334, 0, 0, 0):
        raise ValueError("G51 frozen semantic delta changed")
    if diff.get("added_keys") or diff.get("removed_keys") or diff.get("changed_english_values"):
        raise ValueError("G51 frozen diff unexpectedly records changed semantics")

    full = set(scope["addon_full_locales"])
    supplements = set(scope["selected_upstream_incomplete_locales"])
    complete = set(scope["selected_upstream_complete_locales"])
    if len(full | supplements | complete) != 90 or full & supplements or full & complete or supplements & complete:
        raise ValueError("G51 ownership sets do not form a disjoint 90-locale scope")
    if (len(full), len(supplements), len(complete)) != (63, 26, 1) or complete != {"en_us"}:
        raise ValueError("G51 ownership counts changed")
    if scope.get("malformed_upstream_full_override_locales") != []:
        raise ValueError("G51 unexpectedly records malformed selected upstream JSON")
    if scope.get("upstream_commit") != g51.G51_COMMIT:
        raise ValueError("G51 pinned upstream commit changed")

    reuse = policy.get("translation_reuse", {})
    if reuse.get("eligible_unchanged_key_count") != 334:
        raise ValueError("G51 eligible reuse count changed")
    if reuse.get("reuse_only_exact_same_key_same_english") is not True:
        raise ValueError("G51 exact semantic reuse rule changed")
    if reuse.get("cross_key_reuse_allowed") is not False:
        raise ValueError("G51 cross-key reuse must remain forbidden")

    print("PASS: Minecraft 26.2 frozen delta and ownership metadata")
    print("English: 334/334 exact G50 key/value semantics unchanged")
    print("Ownership: 63 full + 26 supplements + 1 complete upstream = 90")
    print(f"Upstream safety overrides: {scope.get('upstream_literal_safety_override_count')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
