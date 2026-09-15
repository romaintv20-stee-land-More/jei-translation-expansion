#!/usr/bin/env python3
"""Validate the frozen provisional Minecraft 26.3 RC2 English delta and release gate."""
from __future__ import annotations

import json

import reconstruct_26_3_rc_2 as pre


def main() -> int:
    base, target = pre.verify_semantics()
    scope = json.loads(pre.SCOPE_PATH.read_text(encoding="utf-8"))
    diff = json.loads(pre.DIFF_PATH.read_text(encoding="utf-8"))
    policy = json.loads(pre.POLICY_PATH.read_text(encoding="utf-8"))

    if base != target:
        raise ValueError("provisional 26.3 RC2 target no longer exactly matches G51 English semantics")
    if (len(target), len([k for k in target if not k.startswith(pre.DEBUG_PREFIX)])) != (334, 328):
        raise ValueError("provisional 26.3 RC2 frozen source counts changed")
    if (
        diff.get("unchanged_key_and_value_count"),
        diff.get("added_key_count"),
        diff.get("removed_key_count"),
        diff.get("changed_english_value_count"),
    ) != (334, 0, 0, 0):
        raise ValueError("provisional 26.3 RC2 frozen delta changed")
    if scope.get("status") != "provisional-rc-audit-only" or scope.get("not_a_completed_generation") is not True:
        raise ValueError("provisional scope lost its non-final status")
    if scope.get("publishable_candidate") is not False:
        raise ValueError("provisional scope unexpectedly allows candidate publication")
    if policy.get("packaging_registration_allowed") is not False or policy.get("runtime_promotion_allowed") is not False:
        raise ValueError("provisional policy unexpectedly allows final packaging/promotion")
    reuse = policy.get("translation_reuse", {})
    if reuse.get("eligible_unchanged_key_count") != 334:
        raise ValueError("provisional reuse count changed")
    if not reuse.get("reuse_only_exact_same_key_same_english") or reuse.get("cross_key_reuse_allowed") is not False:
        raise ValueError("provisional reuse policy is unsafe")

    print("PASS: provisional Minecraft 26.3 RC2 frozen semantic delta")
    print("334 unchanged same-key/same-English semantics; no added/removed/changed values")
    print("Final G52 packaging remains explicitly blocked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
