"""Read user-owned 32-bit CFF definition manifests, without modifying assets.

This is an explicitly configured build profile, not a universal CFF decoder.
No executable keys, resources, or guessed definition names are bundled.
"""
from dataclasses import dataclass, replace
from .cff_resource import (
    CatalogError, _key_at_va, _mask_constant, _span, _u32, _verify_hash, load_cff,
)
from .entity_definition import EntityKindEvidence, load_entity_kind


@dataclass(frozen=True)
class BuildProfile:
    build_sha256: str
    manifest_sha256: str
    key_table_va: int
    version: int
    definition_count: int
    architecture: int = 0


@dataclass(frozen=True)
class Definition:
    index: int
    name: str
    kind: str = 'unknown'
    serialized_name: str = ''
    kind_evidence: EntityKindEvidence | None = None


@dataclass(frozen=True)
class DefinitionCatalog:
    profile: BuildProfile
    definitions: tuple

    def lookup(self, index):
        if not isinstance(index, int) or not 0 <= index < len(self.definitions):
            raise CatalogError(f'definition index out of range: {index}')
        return self.definitions[index]


def load_catalog(manifest: bytes, executable: bytes, profile: BuildProfile):
    """Validate hashes, container, selected INST and relocations; return names.

    definition_count is explicit profile evidence, never guessed from string IDs.
    Only the configured 32-bit DEF0 architecture is interpreted. Other chunk
    envelopes are checked but their native object layouts are not interpreted.
    """
    _verify_hash(manifest, profile.manifest_sha256, 'manifest')
    if profile.definition_count <= 0 or not 0 <= profile.version <= 255:
        raise CatalogError('invalid count or version')
    decoded = load_cff(
        manifest, executable, build_sha256=profile.build_sha256,
        resource_sha256=profile.manifest_sha256, key_table_va=profile.key_table_va,
        version=profile.version, architecture=profile.architecture,
    )
    blob, relocations = decoded.inst, decoded.relocations
    def pointer(at):
        if at not in relocations:
            raise CatalogError(f'missing relocation at {at}')
        return relocations[at]
    table = pointer(0)
    _span(blob, table, profile.definition_count * 4 + 4)
    if _u32(blob, table + profile.definition_count * 4) != 0:
        raise CatalogError('definition count does not end at null sentinel')
    definitions = []
    for index in range(profile.definition_count):
        entry = pointer(table + index * 4)
        name_at = pointer(entry)
        end = blob.find(0, name_at, min(len(blob), name_at + 1025))
        if end < 0:
            raise CatalogError('unterminated or oversized definition name')
        try:
            name = blob[name_at:end].decode('ascii')
        except UnicodeDecodeError as exc:
            raise CatalogError('non-ASCII definition name') from exc
        if not name or any(ord(c) < 32 or ord(c) > 126 for c in name):
            raise CatalogError('invalid definition name')
        definitions.append(Definition(index, name.strip('*'), serialized_name=name))
    return DefinitionCatalog(profile, tuple(definitions))


SUPPORTED_BUILD_SHA256 = '659f9eed557a426db57554d2a768efe34ba9fe02ba1085d77db64390b0d92642'
# Manifest from which the bundled native roster/item catalogs were derived.
SUPPORTED_MANIFEST_SHA256 = '7292b885378be83cb8596601bad7d0c7adfaab1e91e23f8ea65601f03136755c'

def supported_build_profile(build_sha256: str, manifest_sha256: str):
    """Observed Windows PE32 profile. Manifest hash is a user trust assertion.

    Callers must establish that their manifest belongs to this executable;
    hashing two arbitrary files does not prove that pairing.
    """
    if build_sha256 != SUPPORTED_BUILD_SHA256:
        raise CatalogError('unsupported build SHA-256')
    return BuildProfile(build_sha256, manifest_sha256, 0x01e3f978, 12, 932)


def enrich_definition(catalog: DefinitionCatalog, index: int, resource: bytes,
                      executable: bytes, resource_sha256: str) -> DefinitionCatalog:
    """Return a catalog with one definition enriched by a paired Actor resource.

    Kind decoding is restricted to the native layout audited for this build.
    The original catalog and its manifest provenance are preserved.
    """
    profile = catalog.profile
    if profile != supported_build_profile(profile.build_sha256, profile.manifest_sha256):
        raise CatalogError('unsupported entity kind build profile')
    definition = catalog.lookup(index)
    evidence = load_entity_kind(
        resource, executable, build_sha256=profile.build_sha256,
        resource_sha256=resource_sha256, key_table_va=profile.key_table_va,
        version=profile.version, architecture=profile.architecture,
        expected_name=definition.serialized_name,
    )
    definitions = list(catalog.definitions)
    definitions[index] = replace(definition, kind=evidence.kind, kind_evidence=evidence)
    return replace(catalog, definitions=tuple(definitions))


def main(argv=None):
    """Inspect a local catalog as JSON; stdout only, never rewrite source files."""
    import argparse
    from dataclasses import asdict
    import json
    from pathlib import Path
    import sys
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True, type=Path)
    parser.add_argument('--executable', required=True, type=Path)
    parser.add_argument('--build-sha256', required=True)
    parser.add_argument('--manifest-sha256', required=True,
                        help='Expected hash of a manifest independently paired with this build')
    parser.add_argument('--index', type=int, action='append', help='Definition index; repeat to select multiple')
    args = parser.parse_args(argv)
    try:
        profile = supported_build_profile(args.build_sha256, args.manifest_sha256)
        catalog = load_catalog(args.manifest.read_bytes(), args.executable.read_bytes(), profile)
        definitions = [catalog.lookup(index) for index in args.index] if args.index else catalog.definitions
        print(json.dumps({'profile': asdict(profile), 'definition_count': len(catalog.definitions),
                          'definitions': [asdict(item) for item in definitions]}, indent=2))
    except (OSError, CatalogError) as exc:
        print(f'catalog: {exc}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
