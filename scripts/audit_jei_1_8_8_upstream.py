#!/usr/bin/env python3
"""Audit official JEI 1.8.8 from memory; never persist or create a JAR.

The last public CurseForge release for this target is 2.12.0.49,
file ID 2271876. JEI 2.0.0 was only the original beta.
Run in GitHub Actions; no user computer needed.
"""
import hashlib
import io
import json
import urllib.parse
import urllib.request
import zipfile

PROJECT = "u6dRKJwZ"
VERSION = "2.12.0.49"
FILENAME = "jei_1.8.8-2.12.0.49.jar"
OFFICIAL_URL = "https://edge.forgecdn.net/files/2271/876/" + FILENAME
HEADERS = {"User-Agent": "JEI-Translation-Expansion-1.8.8-Audit/1.0"}


def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=50) as response:
        return response.read()


def published_bytes():
    filters = urllib.parse.urlencode({
        "game_versions": json.dumps(["1.8.8"]),
        "loaders": json.dumps(["forge"]),
    })
    try:
        versions = json.loads(fetch(
            "https://api.modrinth.com/v2/project/" + PROJECT + "/version?" + filters
        ))
        for version in versions:
            if version["version_number"] != VERSION:
                continue
            for file in version["files"]:
                if file.get("filename") == FILENAME:
                    content = fetch(file["url"])
                    sha512 = file.get("hashes", {}).get("sha512")
                    if sha512 and hashlib.sha512(content).hexdigest() != sha512:
                        raise ValueError("Modrinth SHA-512 mismatch")
                    return content, file["url"]
    except (OSError, ValueError, KeyError):
        pass
    return fetch(OFFICIAL_URL), OFFICIAL_URL


def parse_lang(contents):
    result = {}
    for line in contents.decode("utf-8-sig").splitlines():
        if not line or line.lstrip().startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if key:
            result[key] = value
    return result


def main():
    binary, source = published_bytes()
    if binary[:2] != b"PK":
        raise ValueError("The official release is not a valid ZIP/JAR file")
    with zipfile.ZipFile(io.BytesIO(binary)) as jar:
        locales = {
            name.rsplit("/", 1)[-1][:-5].lower(): name
            for name in jar.namelist()
            if name.startswith("assets/jei/lang/") and name.lower().endswith(".lang")
        }
        if "en_us" not in locales:
            raise ValueError("Upstream JEI 1.8.8 lacks English source")
        english = parse_lang(jar.read(locales["en_us"]))
        if not english:
            raise ValueError("Empty upstream English inventory")
        result = {
            "minecraft": "1.8.8",
            "published_jei": VERSION,
            "curseforge_file_id": 2271876,
            "source_url": source,
            "official_jar_sha256": hashlib.sha256(binary).hexdigest(),
            "upstream_english_keys": len(english),
            "upstream_locale_count": len(locales),
            "upstream_locale_key_counts": {
                code: len(parse_lang(jar.read(path)))
                for code, path in sorted(locales.items())
            },
            "scope": "audit only; no release JAR, no translation candidate generated",
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print("PASS: official JEI 1.8.8 audited in memory, no JAR written")


if __name__ == "__main__":
    main()
