"""Search and validate the curated RE catalog without network access or writes.

All commands are read-only. ``index`` emits the deterministic Korean index to
stdout; a maintainer may explicitly redirect it to INDEX.ko.md.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = REPO_ROOT / "vg/docs/re_dictionary/catalog.json"
SCHEMA_PATH = REPO_ROOT / "vg/docs/re_dictionary/catalog.schema.json"
INDEX_PATH = REPO_ROOT / "vg/docs/re_dictionary/INDEX.ko.md"


def load_json(path: Path) -> dict[str, Any]:
    def unique_object(pairs):
        obj = {}
        for key, value in pairs:
            if key in obj:
                raise ValueError(f"duplicate JSON key: {key}")
            obj[key] = value
        return obj
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)


def schema_errors(value: Any, schema: dict, root: dict | None = None,
                  where: str = "$") -> list[str]:
    """Implement the small, documented JSON Schema subset used by this catalog.

    No arbitrary schema execution, remote references, or optional dependency.
    The committed schema is also a normal draft-2020-12 JSON Schema.
    """
    root = schema if root is None else root
    if "$ref" in schema:
        ref = schema["$ref"]
        if not ref.startswith("#/$defs/"):
            return [f"{where}: unsupported schema reference {ref}"]
        return schema_errors(value, root["$defs"][ref.removeprefix("#/$defs/")], root, where)
    errors = []
    types = {"object": lambda x: isinstance(x, dict),
             "array": lambda x: isinstance(x, list),
             "string": lambda x: isinstance(x, str),
             "integer": lambda x: isinstance(x, int) and not isinstance(x, bool),
             "boolean": lambda x: isinstance(x, bool),
             "null": lambda x: x is None}
    expected = schema.get("type")
    if expected:
        expected = expected if isinstance(expected, list) else [expected]
        if not any(types[t](value) for t in expected):
            return [f"{where}: expected {'/'.join(expected)}"]
    if "const" in schema and value != schema["const"]:
        errors.append(f"{where}: expected constant {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{where}: unsupported value {value!r}")
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            errors.append(f"{where}: string is empty")
        if len(value) > schema.get("maxLength", float("inf")):
            errors.append(f"{where}: string too long")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errors.append(f"{where}: invalid format")
    if isinstance(value, int) and not isinstance(value, bool):
        if value < schema.get("minimum", -float("inf")):
            errors.append(f"{where}: below minimum")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errors.append(f"{where}: not enough items")
        if schema.get("uniqueItems") and len({json.dumps(x, sort_keys=True) for x in value}) != len(value):
            errors.append(f"{where}: duplicate array item")
        for i, item in enumerate(value):
            errors += schema_errors(item, schema.get("items", {}), root, f"{where}[{i}]")
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{where}: missing {key}")
        properties = schema.get("properties", {})
        for key, item in value.items():
            if key in properties:
                errors += schema_errors(item, properties[key], root, f"{where}.{key}")
            elif schema.get("additionalProperties") is False:
                errors.append(f"{where}: unknown property {key}")
            elif isinstance(schema.get("additionalProperties"), dict):
                errors += schema_errors(item, schema["additionalProperties"], root, f"{where}.{key}")
    return errors


def portable_path(path: str) -> bool:
    return (bool(path) and not path.startswith("/") and "\\" not in path
            and ":" not in path
            and not any(ord(c) < 32 for c in path)
            and all(p not in ("", ".", "..") for p in path.split("/")))


def validate_document(catalog: dict, schema: dict | None = None) -> list[str]:
    errors = schema_errors(catalog, load_json(SCHEMA_PATH) if schema is None else schema)
    if errors:
        return errors  # Shape checks precede all indexing.
    maps = {}
    for section in ("artifacts", "sources", "entries"):
        maps[section] = {}
        for item in catalog[section]:
            if item["id"] in maps[section]:
                errors.append(f"duplicate {section} ID: {item['id']}")
            maps[section][item["id"]] = item
    artifacts, sources, entries = (maps[k] for k in ("artifacts", "sources", "entries"))
    for source in sources.values():
        loc = source["location"]
        if not portable_path(loc["path"]):
            errors.append(f"{source['id']}: source path must be portable and relative")
        if loc["namespace"] != "repo" and loc["namespace"] not in catalog["external_namespaces"]:
            errors.append(f"{source['id']}: undeclared external namespace")
        expected = "existing_repository" if loc["namespace"] == "repo" else "external_reference_only"
        if source["publication"] != expected:
            errors.append(f"{source['id']}: publication/namespace mismatch")
    for artifact in artifacts.values():
        for ref in artifact["source_refs"]:
            if ref not in sources:
                errors.append(f"{artifact['id']}: unknown source {ref}")
    for entry in entries.values():
        eid = entry["id"]
        scoped = entry["scope"]["artifact_refs"]
        for ref in scoped:
            if ref not in artifacts:
                errors.append(f"{eid}: unknown artifact {ref}")
        for item in entry["evidence"]:
            if item["source_id"] not in sources:
                errors.append(f"{eid}: unknown source {item['source_id']}")
        for ref in entry["related_entry_ids"]:
            if ref not in entries or ref == eid:
                errors.append(f"{eid}: invalid related entry {ref}")
        for function in entry["functions"]:
            ref = function["artifact_id"]
            if ref not in artifacts or ref not in scoped:
                errors.append(f"{eid}: function artifact outside entry scope: {ref}")
            elif function["address_kind"] != artifacts[ref]["address_kind"]:
                errors.append(f"{eid}: function/address-kind mismatch: {function['address']}")
        for call in entry["calls"]:
            if call["artifact_id"] not in scoped:
                errors.append(f"{eid}: call artifact outside entry scope")
        if entry["proof"]["status"] == "corrected" and not entry["corrections_ko"]:
            errors.append(f"{eid}: corrected entry needs an explicit correction")
    # The catalog contains schema names, never actual player UUID observations.
    serialized = json.dumps(catalog, ensure_ascii=False)
    if re.search(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b", serialized):
        errors.append("catalog must not contain literal UUID-shaped identity values")
    if "/workspace/" in serialized or "/home/" in serialized:
        errors.append("catalog must not contain machine-specific absolute paths")
    return errors


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_sources(catalog: dict, repo_root: Path = REPO_ROOT,
                   external_roots: dict[str, Path] | None = None) -> list[dict]:
    """Resolve only caller-selected roots; report missing external artifacts honestly."""
    roots = {**(external_roots or {}), "repo": repo_root}
    results = []
    for source in catalog["sources"]:
        ns, rel = (source["location"][k] for k in ("namespace", "path"))
        result = {"source_id": source["id"], "reference": f"{ns}:{rel}",
                  "expected_sha256": source["sha256"]}
        if not portable_path(rel):
            result["status"] = "unsafe_path"
        elif ns not in roots:
            result["status"] = "unresolved_external"
        else:
            root = roots[ns].resolve()
            path = (root / PurePosixPath(rel)).resolve()
            if not path.is_relative_to(root):
                result["status"] = "unsafe_path"
            else:
                try:
                    if not path.is_file():
                        result["status"] = "missing_source"
                    else:
                        result["actual_sha256"] = file_sha256(path)
                        result["status"] = "verified" if result["actual_sha256"] == source["sha256"] else "hash_mismatch"
                except OSError as exc:
                    result["status"] = "unreadable_source"
                    result["error"] = str(exc)
        results.append(result)
    return results


def search(catalog: dict, query: str = "", category: str | None = None,
           opcode: str | None = None, status: str | None = None) -> list[dict]:
    tokens = query.casefold().split()
    opcode = opcode.lower().removeprefix("0x") if opcode else None
    results = []
    for entry in catalog["entries"]:
        if category and entry["category"] != category:
            continue
        if opcode and opcode not in entry["opcodes"]:
            continue
        if status and entry["proof"]["status"] != status:
            continue
        text = json.dumps(entry, ensure_ascii=False).casefold()
        if all(token in text for token in tokens):
            results.append(entry)
    return sorted(results, key=lambda e: e["id"])


CATEGORY_NAMES = {
    "provenance": "파일·빌드 출처", "framing": "프레임·시간 소유권",
    "identity": "actor·roster·계정 경계", "result": "종료·승패·완전성",
    "items": "아이템·설정·소유", "cooldown": "쿨다운·clock·timer",
    "requests": "게임 요청과 전송", "platform": "플랫폼 JSON schema",
    "android": "Android 패키지와 routing", "upload": "VGNA replay upload",
    "combat_math": "client 산술·HUD·stub", "health": "받은 HP와 표시",
    "correlation": "action↔impact의 제한된 연관", "implementation": "구현 상태",
}


def render_index(catalog: dict) -> str:
    lines = ["# Vainglory RE 기능 사전", "",
             "이 파일은 catalog.json에서 생성됩니다. 직접 수정하지 말고 원본 catalog를 갱신하세요.", "",
             f"기준 checkout: `{catalog['baseline_commit']}` · 갱신: {catalog['updated']} · 항목: {len(catalog['entries'])}", "",
             "검토된 기능 묶음과 중요한 정정만 담았습니다. 기존 evidence 전체를 검증 완료로 승격한 목록이 아닙니다.",
             "정적 명령 검증, synthetic test, 개발 corpus 관측, runtime 관측은 서로 다른 증거입니다. semantic confidence가 높아도 서버 권위나 live 실행은 증명되지 않습니다.",
             "raw binary/replay, 실제 player UUID, 새 raw disassembly는 포함하지 않습니다. 외부 원문은 hash-bound reference로만 남습니다.", "",
             "## 빠른 검색", "", "```sh", "python -B -m vg.research.dictionary search 쿨다운", "python -B -m vg.research.dictionary search --opcode 0449",
             "python -B -m vg.research.dictionary show VGRE-health-impact-prefix", "python -B -m vg.research.dictionary validate --check-index", "```", "",
             "외부 근거의 미해결은 검증 성공과 구별됩니다. 실제 source를 가진 사람은 `--external-root research=/path/to/research --external-root shared=/path/to/shared --require-external`을 validate에 추가하세요.", "",
             "## 기능별 목차", ""]
    categories = sorted({e["category"] for e in catalog["entries"]}, key=lambda k: (list(CATEGORY_NAMES).index(k) if k in CATEGORY_NAMES else 99, k))
    for category in categories:
        label = CATEGORY_NAMES.get(category, category)
        lines.append(f"- {label}: " + ", ".join(f"[{e['title_ko']}](#{e['id'].lower()})" for e in catalog["entries"] if e["category"] == category))
    for category in categories:
        lines += ["", f"## {CATEGORY_NAMES.get(category, category)}", ""]
        for e in sorted((x for x in catalog["entries"] if x["category"] == category), key=lambda x: x["id"]):
            p, scope = e["proof"], e["scope"]
            lines += [f"### {e['id']}", "", f"**{e['title_ko']}**", "", e["claim_ko"], "",
                      f"- 상태: {p['status']} · 의미 확신: {p['semantic_confidence']} · 검증: {', '.join(p['validation_kinds'])}",
                      f"- 경계: {scope['layer']} / {scope['direction']} / {scope['execution_context']}",
                      f"- 정확한 파일: {', '.join('`'+a+'`' for a in scope['artifact_refs'])}"]
            if e["opcodes"]:
                lines.append("- Opcode: " + ", ".join("`"+x+"`" for x in e["opcodes"]))
            if e["functions"]:
                lines.append("- 함수/위치: " + "; ".join(f"`{f['address']}` ({f['artifact_id']}, {f['address_kind']}, {f['role']})" for f in e["functions"]))
            for f in e["fields"]:
                lines.append(f"- 필드: {f['name']} = {f['offset_base']}+{f['offset']} ({f['encoding']})" + (f"; {f['note']}" if f['note'] else ""))
            for layout in e.get("layout_notes", []):
                lines.append("- 원문 layout: " + layout)
            for correction in e["corrections_ko"]:
                lines.append("- 정정: " + correction)
            for limit in e["limitations_ko"]:
                lines.append("- 한계: " + limit)
            for proof in e["evidence"]:
                lines.append(f"- 근거: [{proof['source_id']}](#{proof['source_id'].lower()}) · {proof['locator']}")
            lines.append("")
    lines += ["## 정확한 입력 파일과 주소 공간", ""]
    for a in catalog["artifacts"]:
        lines += [f"### {a['id']}", "", f"- 파일: {a['filename']}", f"- SHA-256 ({a['hash_kind']}): `{a['sha256']}`",
                  f"- 플랫폼/ABI: {a['platform']} / {a['abi']}", f"- 빌드: {a['build']['label']} (release 식별 검증: {a['build']['verified_release']})",
                  f"- 주소: {a['address_kind']} · image base: {a['image_base'] or '해당 없음'}", f"- 주의: {a['build']['note']}", ""]
    lines += ["## 근거 manifest", "", "repo 경로는 현재 checkout에서 hash를 확인합니다. 외부 namespace 경로는 원문 위치를 이식 가능하게 표현하며, 링크가 열리거나 파일이 배포되었다는 의미가 아닙니다.", ""]
    for s in catalog["sources"]:
        loc = s["location"]
        ref = f"{loc['namespace']}:{loc['path']}"
        display = f"[{ref}](../../../{loc['path']})" if loc["namespace"] == "repo" else f"`{ref}`"
        # INDEX lives at vg/docs/re_dictionary: ../../../ reaches repository root.
        lines += [f"### {s['id']}", "", f"- {display}", f"- SHA-256: `{s['sha256']}`", f"- 종류: {s['kind']} · 보관: {s['publication']}", ""]
    return "\n".join(lines).rstrip()+"\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=CATALOG_PATH)
    sub = parser.add_subparsers(dest="command", required=True)
    find = sub.add_parser("search", help="case-insensitive AND search; no writes")
    find.add_argument("query", nargs="*", default=[])
    find.add_argument("--category")
    find.add_argument("--opcode")
    find.add_argument("--status")
    find.add_argument("--json", action="store_true")
    show = sub.add_parser("show", help="one complete machine-readable entry")
    show.add_argument("entry_id")
    sub.add_parser("index", help="render deterministic Korean Markdown to stdout")
    check = sub.add_parser("validate", help="schema, IDs, source hashes, optional generated-index check")
    check.add_argument("--external-root", action="append", default=[], metavar="NAMESPACE=PATH")
    check.add_argument("--require-external", action="store_true")
    check.add_argument("--check-index", action="store_true")
    check.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        catalog = load_json(args.catalog)
        errors = validate_document(catalog)
        if errors:
            print("\n".join(errors), file=sys.stderr)
            return 2
        if args.command == "search":
            results = search(catalog, " ".join(args.query), args.category, args.opcode, args.status)
            if args.json:
                print(json.dumps(results, ensure_ascii=False, indent=2))
            else:
                for e in results:
                    print(f"{e['id']} [{e['proof']['status']}/{e['proof']['semantic_confidence']}] {e['title_ko']}")
                    print("  " + e["claim_ko"])
            return 0
        if args.command == "show":
            entry = next((e for e in catalog["entries"] if e["id"] == args.entry_id), None)
            if entry is None:
                print(f"unknown entry: {args.entry_id}", file=sys.stderr)
                return 1
            print(json.dumps(entry, ensure_ascii=False, indent=2))
            return 0
        if args.command == "index":
            print(render_index(catalog), end="")
            return 0
        roots = {}
        for value in args.external_root:
            ns, sep, path = value.partition("=")
            if not sep or not path or ns not in catalog["external_namespaces"] or ns in roots:
                raise ValueError(f"invalid or duplicate external root: {value}")
            roots[ns] = Path(path)
        results = verify_sources(catalog, external_roots=roots)
        failed = [r for r in results if r["status"] not in ("verified", "unresolved_external")]
        unresolved = [r for r in results if r["status"] == "unresolved_external"]
        index_ok = None
        if args.check_index:
            index_ok = INDEX_PATH.read_text(encoding="utf-8") == render_index(catalog)
            if not index_ok:
                errors.append("generated Korean index is stale")
        report = {"schema_valid": True, "entries": len(catalog["entries"]), "sources": results,
                  "verified_sources": len(results)-len(failed)-len(unresolved),
                  "unresolved_external_sources": len(unresolved), "failed_sources": len(failed),
                  "generated_index_matches": index_ok, "errors": errors,
                  "scope": "Catalog consistency and source-file identity only; not renewed native execution or server validation."}
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print(f"{report['entries']} entries; {report['verified_sources']} source hashes verified; {len(unresolved)} external sources unresolved; {len(failed)} source failures")
            for r in failed + unresolved:
                print(f"{r['status']}: {r['reference']}")
            for error in errors:
                print(error)
            print(report["scope"])
        return 2 if failed or errors or (args.require_external and unresolved) else 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"dictionary: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
