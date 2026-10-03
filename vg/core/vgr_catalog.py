from collections.abc import Mapping
from typing import TypedDict

from vg.core.vgr_mapping import BINARY_HERO_ID_MAP, HERO_ID_MAP, normalize_hero_name


class HeroReference(TypedDict, total=False):
    hero_id: int | None
    hero_name: str | None
    hero_namespace: str


def resolve_hero_to_catalog(player: HeroReference, catalog: Mapping[str, int]) -> tuple[int | None, int | None, str, str]:
    raw_id = player.get('hero_id')
    name = normalize_hero_name(player.get('hero_name') or '').strip().casefold()
    namespace = player.get('hero_namespace')
    if namespace not in ('binary', 'legacy_mapping'):
        namespace = ('binary' if raw_id in BINARY_HERO_ID_MAP else
                     'legacy_mapping' if raw_id in HERO_ID_MAP else 'unknown')
    if name not in catalog:
        return None, raw_id, namespace, 'Hero name does not identify a catalog entry.'
    mapped = (BINARY_HERO_ID_MAP.get(raw_id) if namespace == 'binary' else
              HERO_ID_MAP.get(raw_id, {}).get('name') if namespace == 'legacy_mapping' else None)
    if namespace != 'unknown' and (mapped is None or normalize_hero_name(mapped).casefold() != name):
        return None, raw_id, namespace, 'Source hero ID disagrees with the supplied hero name.'
    return catalog[name], raw_id, namespace, 'Resolved canonical hero name to the catalog ID.'


# All heroes from VaingloryFire wiki
HEROES_DATA = [
    # name, role, attack_type
    ("Adagio", "Captain", "Ranged"),
    ("Alpha", "Warrior", "Melee"),
    ("Amael", "Mage", "Ranged"),
    ("Anka", "Assassin", "Melee"),
    ("Ardan", "Captain", "Melee"),
    ("Baptiste", "Mage", "Ranged"),
    ("Baron", "Sniper", "Ranged"),
    ("Blackfeather", "Assassin", "Melee"),
    ("Caine", "Sniper", "Ranged"),
    ("Catherine", "Captain", "Melee"),
    ("Celeste", "Mage", "Ranged"),
    ("Churnwalker", "Captain", "Melee"),
    ("Flicker", "Captain", "Melee"),
    ("Fortress", "Captain", "Melee"),
    ("Glaive", "Warrior", "Melee"),
    ("Grace", "Captain", "Melee"),
    ("Grumpjaw", "Warrior", "Melee"),
    ("Gwen", "Sniper", "Ranged"),
    ("Idris", "Assassin", "Melee"),
    ("Inara", "Warrior", "Melee"),
    ("Ishtar", "Sniper", "Ranged"),
    ("Joule", "Warrior", "Melee"),
    ("Karas", "Assassin", "Melee"),
    ("Kensei", "Warrior", "Melee"),
    ("Kestrel", "Sniper", "Ranged"),
    ("Kinetic", "Sniper", "Ranged"),
    ("Koshka", "Assassin", "Melee"),
    ("Krul", "Warrior", "Melee"),
    ("Lance", "Captain", "Melee"),
    ("Leo", "Warrior", "Melee"),
    ("Lorelai", "Captain", "Ranged"),
    ("Lyra", "Captain", "Ranged"),
    ("Magnus", "Mage", "Ranged"),
    ("Malene", "Mage", "Ranged"),
    ("Miho", "Assassin", "Melee"),
    ("Ozo", "Warrior", "Melee"),
    ("Petal", "Mage", "Ranged"),
    ("Phinn", "Captain", "Melee"),
    ("Reim", "Mage", "Melee"),
    ("Reza", "Assassin", "Melee"),
    ("Ringo", "Sniper", "Ranged"),
    ("Rona", "Warrior", "Melee"),
    ("Samuel", "Mage", "Ranged"),
    ("San Feng", "Warrior", "Melee"),
    ("SAW", "Sniper", "Ranged"),
    ("Shin", "Captain", "Melee"),
    ("Silvernail", "Sniper", "Ranged"),
    ("Skaarf", "Mage", "Ranged"),
    ("Skye", "Mage", "Ranged"),
    ("Taka", "Assassin", "Melee"),
    ("Tony", "Warrior", "Melee"),
    ("Varya", "Mage", "Ranged"),
    ("Viola", "Captain", "Ranged"),
    ("Vox", "Sniper", "Ranged"),
    ("Warhawk", "Sniper", "Ranged"),
    ("Yates", "Captain", "Melee"),
    ("Ylva", "Assassin", "Melee"),
]

# Korean names mapping (official translations from Namu Wiki)
KOREAN_NAMES = {
    "Adagio": "아다지오",
    "Alpha": "알파",
    "Amael": "아마엘",
    "Anka": "앙카",
    "Ardan": "아단",
    "Baptiste": "바티스트",
    "Baron": "바론",
    "Blackfeather": "흑깃",
    "Caine": "케인",
    "Catherine": "캐서린",
    "Celeste": "셀레스트",
    "Churnwalker": "어둠추적자",
    "Flicker": "플리커",
    "Fortress": "포트리스",
    "Glaive": "글레이브",
    "Grace": "그레이스",
    "Grumpjaw": "사슬니",
    "Gwen": "그웬",
    "Idris": "이드리스",
    "Inara": "이나라",
    "Ishtar": "이슈타르",
    "Joule": "쥴",
    "Karas": "카라스",
    "Kensei": "켄세이",
    "Kestrel": "케스트럴",
    "Kinetic": "키네틱",
    "Koshka": "코쉬카",
    "Krul": "크럴",
    "Lance": "랜스",
    "Leo": "레오",
    "Lorelai": "로렐라이",
    "Lyra": "라이라",
    "Magnus": "마그누스",
    "Malene": "말렌",
    "Miho": "미호",
    "Ozo": "오조",
    "Petal": "페탈",
    "Phinn": "핀",
    "Reim": "라임",
    "Reza": "레자",
    "Ringo": "링고",
    "Rona": "로나",
    "Samuel": "사무엘",
    "San Feng": "삼봉",
    "SAW": "쏘우",
    "Shin": "신",
    "Silvernail": "실버네일",
    "Skaarf": "스카프",
    "Skye": "스카이",
    "Taka": "타카",
    "Tony": "토니",
    "Varya": "바리야",
    "Viola": "비올라",
    "Vox": "복스",
    "Warhawk": "워호크",
    "Yates": "예이츠",
    "Ylva": "일바",
}

# Item categories
ITEMS_DATA = [
    # Weapon items
    ("Weapon Blade", "Weapon", "Basic", 1),
    ("Book of Eulogies", "Weapon", "Basic", 1),
    ("Swift Shooter", "Weapon", "Basic", 1),
    ("Minion's Foot", "Weapon", "Basic", 1),
    ("Heavy Steel", "Weapon", "Tier 2", 2),
    ("Six Sins", "Weapon", "Tier 2", 2),
    ("Blazing Salvo", "Weapon", "Tier 2", 2),
    ("Lucky Strike", "Weapon", "Tier 2", 2),
    ("Piercing Spear", "Weapon", "Tier 2", 2),
    ("Barbed Needle", "Weapon", "Tier 2", 2),
    ("Sorrowblade", "Weapon", "Tier 3", 3),
    ("Serpent Mask", "Weapon", "Tier 3", 3),
    ("Tornado Trigger", "Weapon", "Tier 3", 3),
    ("Tyrant's Monocle", "Weapon", "Tier 3", 3),
    ("Bonesaw", "Weapon", "Tier 3", 3),
    ("Poisoned Shiv", "Weapon", "Tier 3", 3),
    ("Breaking Point", "Weapon", "Tier 3", 3),
    ("Tension Bow", "Weapon", "Tier 3", 3),
    ("Spellsword", "Weapon", "Tier 3", 3),

    # Crystal items
    ("Crystal Bit", "Crystal", "Basic", 1),
    ("Energy Battery", "Crystal", "Basic", 1),
    ("Hourglass", "Crystal", "Basic", 1),
    ("Eclipse Prism", "Crystal", "Tier 2", 2),
    ("Heavy Prism", "Crystal", "Tier 2", 2),
    ("Piercing Shard", "Crystal", "Tier 2", 2),
    ("Chronograph", "Crystal", "Tier 2", 2),
    ("Void Battery", "Crystal", "Tier 2", 2),
    ("Shatterglass", "Crystal", "Tier 3", 3),
    ("Frostburn", "Crystal", "Tier 3", 3),
    ("Eve of Harvest", "Crystal", "Tier 3", 3),
    ("Broken Myth", "Crystal", "Tier 3", 3),
    ("Clockwork", "Crystal", "Tier 3", 3),
    ("Alternating Current", "Crystal", "Tier 3", 3),
    ("Dragon's Eye", "Crystal", "Tier 3", 3),
    ("Spellfire", "Crystal", "Tier 3", 3),

    # Defense items
    ("Light Shield", "Defense", "Basic", 1),
    ("Light Armor", "Defense", "Basic", 1),
    ("Oakheart", "Defense", "Basic", 1),
    ("Kinetic Shield", "Defense", "Tier 2", 2),
    ("Coat of Plates", "Defense", "Tier 2", 2),
    ("Dragonheart", "Defense", "Tier 2", 2),
    ("Reflex Block", "Defense", "Tier 2", 2),
    ("Aegis", "Defense", "Tier 3", 3),
    ("Metal Jacket", "Defense", "Tier 3", 3),
    ("Fountain of Renewal", "Defense", "Tier 3", 3),
    ("Crucible", "Defense", "Tier 3", 3),
    ("Atlas Pauldron", "Defense", "Tier 3", 3),
    ("Slumbering Husk", "Defense", "Tier 3", 3),
    ("Pulseweave", "Defense", "Tier 3", 3),
    ("Capacitor Plate", "Defense", "Tier 3", 3),

    # Utility items
    ("Sprint Boots", "Utility", "Basic", 1),
    ("Travel Boots", "Utility", "Tier 2", 2),
    ("Journey Boots", "Utility", "Tier 3", 3),
    ("Halcyon Chargers", "Utility", "Tier 3", 3),
    ("War Treads", "Utility", "Tier 3", 3),
    ("Teleport Boots", "Utility", "Tier 3", 3),
    ("Flare", "Utility", "Consumable", 1),
    ("Scout Trap", "Utility", "Consumable", 1),
    ("Flare Gun", "Utility", "Tier 2", 2),
    ("Contraption", "Utility", "Tier 3", 3),
    ("Superscout 2000", "Utility", "Tier 3", 3),
    ("Nullwave Gauntlet", "Utility", "Tier 3", 3),
    ("Echo", "Utility", "Tier 3", 3),
    ("Stormcrown", "Utility", "Tier 3", 3),
    ("Aftershock", "Crystal", "Tier 3", 3),
]
