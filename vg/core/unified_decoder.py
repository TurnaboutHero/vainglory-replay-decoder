#!/usr/bin/env python3
"""
Unified Replay Decoder - Single entry point for complete VGR replay analysis.

Combines all solved detection modules:
  - VGRParser: players, teams, heroes, game mode (100% accuracy)
  - KDADetector: kills 99.0%, deaths 98.0%, assists 98.0% (combined 98.3%)
  - Gold: strict action 0x06 partial observations; final earned gold is withheld.
  - WinLossDetector: crystal destruction detection (100% accuracy)
  - Item-Player Mapping: [10 04 3D] acquire events → per-player item builds
  - Crystal Death Detection: eid 2000-2005 death → game duration & winner
  - Objective Events: Kraken vs Gold Mine via player kill proximity (eid>60000)

Team label limitation:
  The team_byte at player block +0xD5 groups players correctly (100%),
  but the 1→left / 2→right mapping is non-deterministic (~50% of matches
  have swapped labels). No binary-level signal has been found to resolve
  this (exhaustive search: player block bytes, entity events, event headers,
  turret clustering, crystal entity IDs, map position, player block order —
  all fail to discriminate left/right).
  Map position IS encoded, contrary to what this note used to say: see
  _detect_positions. It does not settle the label, and the reason is worth
  knowing. team_byte 1 is the low-x side of the map in all 11 truth matches,
  so x-ordering and team_byte are the same partition - sorting teams by x
  re-derives the byte and adds nothing. Measured against truth, team_byte 1
  is the left column in 6 matches of 11, and the team owning the first player
  block in 7 of 11. Both are coin flips. Blocks are interleaved by team
  (1212221112), so there is no team-major slot order left to read either.
  What truth calls "left"/"right" is the column in the result screenshot,
  which is a property of the screen rather than of the match: across a
  tournament series the column stays put while team_byte flips from game to
  game, which is what teams switching map sides looks like. The part that is
  a match property is recorded as DecodedPlayer.map_side. Worked through in
  vg/docs/TEAM_LABEL_2026-08-10.md.
  Kill totals do not establish a terminal winner. Winner output is withheld
  until terminal winner evidence and its team mapping are validated.

Usage:
    from vg.core.unified_decoder import UnifiedDecoder

    decoder = UnifiedDecoder("/path/to/replay")
    match = decoder.decode()
    print(match.to_json())

CLI:
    python -m vg.core.unified_decoder /path/to/replay
"""

import bisect
import json
import math
import statistics
import struct
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Literal, NotRequired, Optional, Set, Tuple, TypedDict
from vg.core.stat_evidence import final_field_reason, inspect_replay_evidence
from vg.core.vgr_records import VGRRecordError, iter_records

# Local imports with fallback for both package and direct execution
try:
    from vg.core.vgr_parser import VGRParser
    from vg.core.kda_detector import KDADetector
    from vg.core.vgr_mapping import ITEM_ID_MAP, RECIPES
    from vg.analysis.win_loss_detector import WinLossDetector
except ImportError:
    try:
        from vgr_parser import VGRParser
        from kda_detector import KDADetector
        from vgr_mapping import ITEM_ID_MAP, RECIPES
        _root = Path(__file__).resolve().parent.parent
        sys.path.insert(0, str(_root.parent))
        from vg.analysis.win_loss_detector import WinLossDetector
    except ImportError as e:
        raise ImportError(f"Cannot import required modules: {e}")

# Event headers for item and objective detection
_ITEM_ACQUIRE_HEADER = bytes([0x10, 0x04, 0x3D])
_ITEM_EQUIP_HEADER = bytes([0x10, 0x04, 0x4B])
_CREDIT_HEADER = bytes([0x10, 0x04, 0x1D])
_DEATH_HEADER = bytes([0x08, 0x04, 0x31])
_KILL_HEADER = bytes([0x18, 0x04, 0x1C])
_PLAYER_EID_RANGE = set(range(1500, 1510))  # BE entity IDs for players

# Map position, as (header, offset of the first of three float32 BE).
#
# Found by looking for smoothness rather than by guessing a layout: a position
# has to be continuous, so consecutive samples of one entity must move at
# something like a hero's speed. Three tests then agreed. In match 7 every
# player on the left sits at negative x in the opening minute and every player
# on the right at positive x. Speed between consecutive samples has a median of
# 2.7 m/s. And the middle float never leaves zero - median 0.0000, largest
# 0.041 - which is the height axis of a flat map.
#
# Across all 11 truth matches the team carrying team_byte 1 has the lower
# median x, 11 for 11. The sign does not always separate the two, because by
# the 120-second mark players have spread into lanes, but the ordering holds.
# This is what map_side records. Note what it does NOT give you: since the
# byte already picks out the low-x side, x cannot disagree with it, and so it
# carries no information about which side the scoreboard calls "left".
#
# Sampling is sparse: about 1800 points a match for ten players, one every nine
# seconds or so. This is position attached to particular events, not a
# continuous track.
#
# What the two events are, as far as it has been pinned down. Both stop while
# their player is dead - neither ever fires within a second of that player's own
# death, against 0.5% for the same samples shifted in time - and both are
# suppressed around item acquisition, which is the same fact seen from the shop.
# [18 04 16] carries the bulk and is close to uniform in time. [18 04 03] is
# rarer, clusters near kills (1.88x against a shifted control, where [18 04 16]
# manages 1.23x), and holds an extra float32 ahead of the coordinates: an
# mostly-integer value between 1 and 60 that is locked to the hero: the same
# hero picked by a different player in a different match produces the same one
# to three values, and they appear throughout the match together. Grumpjaw is
# 16 and 14 across six matches, Caine 13, Kinetic 22.5.
#
# What the constant measures is not settled, and four readings are ruled out.
# Respawn time - subtracting it does not land on the preceding death, median
# error 124s. Anything that grows with the match - the median holds at 16, 16,
# 18 across thirds. A cooldown carrying cooldown acceleration - the values
# coexist all match rather than stepping down, and Blackfeather's 8.57 appears
# 77 seconds before he buys the item that would explain it. A cooldown at all -
# 49% of consecutive same-value events for one player are closer together than
# the value, which a cooldown cannot be. A distance in map units - the range to
# the nearest enemy sits under the value 62.6% of the time against 62.3% when
# the value is swapped for another event's, so it knows nothing about range.
# One value per active ability is out too: matching hero ability lists from the
# Korean guide database against the values each hero produces, only 4 heroes of
# 15 line up. Skye, Reza, Kinetic, Fortress and Grace each hold three actives
# and emit a single value; Baptiste emits six.
#
# The guide database has ability names but its stat arrays carry labels with no
# numbers, so it cannot close this. Somebody's extracted ability table would.
#
# The same search did confirm the unit. The hero sheet lists move speeds of 3.1
# to 3.7, and the speed measured between consecutive samples here runs 2.71 to
# 3.11, so these coordinates are in metres and the map is about 140 across.
#
# Role inference was tried on these coordinates and does not work. Against
# minion kills as the role proxy, every spatial feature is flat - distance from
# own base -0.02, spread of that distance -0.02, lane offset -0.01, absolute
# lane offset 0.21 over 75 players. The only things that correlate are total
# path length (0.55) and sample count (0.58), which measure how often a player
# was recorded rather than where they were. Positions say who was busy, not who
# was in the jungle.
_POSITION_EVENTS = ((bytes([0x18, 0x04, 0x16]), 7),
                    (bytes([0x18, 0x04, 0x03]), 11))
# A point is kept only if it looks like one: on the map, and on the ground.
_POSITION_MAP_LIMIT = 150.0
_POSITION_GROUND_LIMIT = 0.5

# ===== ITEM BUILD ESTIMATION =====
# Upgrade tree using BINARY REPLAY IDs (from ITEM_ID_MAP).
#
# Two ID ranges:
#   - 200-255: standard shop purchases (qty=1)
#   - 0-27: T3/special item completions (qty=2), identified via hero distribution
#
def _build_upgrade_tree() -> Dict[int, Set[int]]:
    """
    component_id -> every result it could have been consumed by, transitively.

    Derived from RECIPES rather than written out, because the two were kept
    side by side and drifted. Warmail is what exposed it: the recipe source
    names Kinetic Shield in Fountain of Renewal and Aegis where the shop
    charges for Warmail, so nothing ever consumed a Warmail and it sat in
    every build that bought one until the end of the match. Correcting the
    recipes would not have been enough on its own - the tree still said
    Kinetic Shield - and that is the failure this removes rather than fixes.

    Transitive, so a single pass can compare each component against every
    result it could have fed even when the intermediate step is itself gone
    from the final build.
    """
    direct: Dict[int, Set[int]] = defaultdict(set)
    for result, components in RECIPES.items():
        for component in components:
            direct[component].add(result)

    tree: Dict[int, Set[int]] = {}
    for component in direct:
        reachable: Set[int] = set()
        pending = list(direct[component])
        while pending:
            result = pending.pop()
            if result in reachable:
                continue
            reachable.add(result)
            pending.extend(direct.get(result, ()))
        tree[component] = reachable
    return tree


UPGRADE_TREE = _build_upgrade_tree()

# One .vgr section covers this much game time. Measured externally across 14
# matches spanning 716-2939s (9.94-10.00 s/section), so section count times this
# gives how long the recording ran - a length the event stream cannot fake.
SECONDS_PER_SECTION = 10

# Below this, the event stream stops well before the recording does, which means
# the tail of the match was never captured. Separates 10 complete tournament
# matches (0.97-1.00) from the one known truncated recording (0.56); the gap
# either side of it is empty, so the exact cut point is not tuned.
COMPLETENESS_THRESHOLD = 0.90

# Consumables leave no event when they are used, so a Flare or an infusion
# bought early is almost certainly gone by the end while the purchase log still
# shows it. Keep one only if it was bought in the last stretch of the player's
# purchases. Dropping them outright scores higher on F1 (93.4% precision against
# 91.7%) but costs a real item, so the conservative cut is the one used.
CONSUMABLE_KEEP_FRACTION = 0.90

# Granted at match start, never bought, so never part of a final build.
# Consumables that ARE bought (infusions, flares) stay eligible and are held
# back by the slot ranking instead.
STARTER_IDS = {
    457,  # Healing Flask   (1,201) - auto-granted at match start
    526,  # Scout Camera    (2,14)  - auto-granted at match start
}
# Both are handed to every player rather than bought: each appears for 456/502
# players, and per match either everyone has it (51 matches) or nobody does
# (5 matches whose start frames are missing) - never a partial split, which is
# what a purchased item produces.


def _le_to_be(eid_le: int) -> int:
    """Convert uint16 Little Endian entity ID to Big Endian."""
    return struct.unpack('>H', struct.pack('<H', eid_le))[0]


def _assess_core_completeness(
    duration: Optional[int],
    recorded_seconds: Optional[int],
    crystal_ts: Optional[float],
    duration_est: Optional[float],
) -> Tuple[Optional[bool], str]:
    if not duration or not recorded_seconds:
        return None, "Insufficient timing evidence to assess match completion."
    if duration / recorded_seconds < COMPLETENESS_THRESHOLD:
        return False, "Event duration falls short of the recorded span."
    if (
        crystal_ts is not None
        and duration_est is not None
        and abs(crystal_ts - duration_est) <= 30
    ):
        return None, "Terminal crystal candidate agrees with the player-death tail; this heuristic does not confirm completion."
    return None, "Recording coverage alone does not confirm a terminal match end."


# An acquire and the cost it was charged for sit within a few hundred bytes of
# each other. 400 pairs 10479 of the corpus's purchases without ever reaching
# past a neighbouring purchase.
_COST_WINDOW = 400
# Refunds land on whole gold, so anything looser than a rounding slack would
# start matching items the player did not sell.
_SALE_TOLERANCE = 1.0
# Every price in the game is a multiple of 25, so half of one lands on 12.5 at
# worst; 93.6% of the corpus's refunds are a clean multiple of 25. The rest are
# accounting drift wearing a refund's clothes (see _detect_wallet), and this is
# what keeps most of it out.
_REFUND_STEP = 25
# When a match ends the whole inventory goes back to the shop at once, and the
# purse reports it item by item within a second or two. Those are not sales -
# the player finished holding every one of them - so a run of reports packed
# this tightly is thrown away. Real sales sit alone: the isolated ones in the
# corpus are seconds to minutes from their neighbours, never fractions.
_LIQUIDATION_GAP = 10.0     # seconds; wider than any burst, narrower than any pair of real sales
_LIQUIDATION_RUN = 3        # reports in one burst before it reads as liquidation

# Automatic gold starts at a fixed point in the match, one tick a second, and
# the replays agree: 300 ticks in every 300 seconds, flat from the first to the
# last. That fixed start is what dates a recording.
#
# When and how much, both per mode and both measured across the 56-file corpus:
#
#   5v5  starts 0:40, 3 gold a second   (48 files; earliest first tick 41.4)
#   3v3  starts 0:35, 6 gold a second   (7 files; first ticks cluster 37.7-38.0)
#
# The 2018 update notes for 3.0 said 5 a second from 0:45 for 5v5, which is a
# different game to this one - these recordings are dated June 2022. Do not
# reach for those notes to explain a number here.
#
# A warning about the other source that gets consulted for these numbers. The
# Glory Guide companion app's 5v5 data (5v5.plist) agrees with the replays on
# the trickle, on minion gold (35 melee, 25 ranged, 60 siege) and on Goldoak at
# 220 - and then says the mythic creatures award "0 each". They do not: the
# corpus carries 541 credits of 125 and 260 of 250, which is Ghostwing and
# Blackclaw paying out normally. That section of the app data was never filled
# in. Agreeing with measurement in six places does not make a source right in
# the seventh.
#
# Timestamps run from where the recording begins, so a file that covers the
# match start shows its first tick a second or two after the mode's start
# time - the 5v5 corpus lands 41 to 77 - and
# one that joined a match already in progress shows it within a couple of
# seconds, because the gold was already flowing. Nothing falls in between.
#
# The amount per tick is not fixed: 5v5 pays 3 and 3v3 pays 6, so the tick has
# to be found rather than assumed. It is the commonest income too small to be a
# bounty - the cheapest of those is a minion at 30, and an ally's share of one
# is 18.
# The lower bound is there because one file's commonest small income is 0.3,
# which is not a per-second gold tick and would date the recording wrongly.
# Mythic creatures pay every surviving member of the capturing team at once, so
# the payout names the team without any inference: whoever was paid took it.
#
# The catch is that the same two numbers are hero bounties - the app data gives
# the kill bounty as 250 with 125 per kill on top - and those go to one player.
# Burst size separates them cleanly, and the cut is measured rather than picked:
# across 50 matches every burst of one or two recipients has a player death
# within four seconds (42 of 42), while bursts of four or five sit at 18-22%,
# which is just how often somebody dies in the fight over the objective.
#
# Objective death events do not corroborate these and are not expected to.
# Ghostwing is captured rather than killed, and only 3-12% of the bursts have an
# eid>60000 death anywhere near them.
_MYTHIC_PAYOUT = {125.0: "GHOSTWING_CAPTURE", 250.0: "BLACKCLAW_CAPTURE"}
_MYTHIC_BURST_GAP = 2.0     # seconds; the whole team is paid in one instant
_MYTHIC_MIN_SHARE = 3       # recipients; below this it is a hero bounty

# A destroyed turret pays its team twice over: 50 to every member, and 300 split
# evenly among whoever was standing near it. The split is what makes this
# findable without knowing anything else - value times recipients has to come to
# exactly 300, which is arithmetic no unrelated pile of minion gold satisfies.
# Across 48 5v5 files it lands on the nose 381 times, in every arrangement:
# 300 to one player 140 times, 150 to two 95, 100 to three 55, 75 to four 35,
# and 60 to five 26.
#
# The denominator is worth more than the detection. It counts the heroes who
# were at the turret, which is proximity information the coordinates could not
# give - they are too sparse to say who was where at a given second.
#
# Windows are tight on purpose. Minion gold flows constantly, so a two-second
# window around anything sweeps up dozens of unrelated credits; grouping first
# and filtering second buries the signal.
_TURRET_GLOBAL = 50.0       # paid to every member of the team
_TURRET_POOL = 300.0        # split among those standing near it
_TURRET_TIGHT = 0.2         # seconds; the global payments land together
_TURRET_LOOK = 0.5          # seconds; how far out to read the split

_PASSIVE_TICK_MIN = 1.0
_PASSIVE_TICK_MAX = 10.0
_MATCH_START_CUTOFF = 30.0


# Whether a detected sale removes the item from the build.
#
# Off, because the only truth that can see it says it loses more than it wins.
# Matches 1 to 4 report almost no purse, so the tuning set is blind to this
# feature and scored it 98.0/91.7 either way. Reading the six holdout
# screenshots for slot counts gave the first real measurement: 49 of 60 players
# exact without sales, 48 with. It changed three players and got one of them
# right - Reim in match 7, whose Teleport Boots the screenshot confirms he did
# not finish holding - while taking a Shatterglass and a Teleport Boots off
# Ritoramu and another Teleport Boots off tsuki, both of whom the screenshot
# shows with a full six.
#
# All three removals are the same item in the same match, which points at the
# baseline rather than the rule: it is the match minimum of the residual, so a
# minimum player who sold before their first report drags it low and hands
# every other player a refund they never got.
#
# Tightening it against these three events would be fitting the holdout, which
# is the one thing it cannot be spent on. _detect_wallet still runs and its
# findings stand on their own; only the build edit is withheld.
APPLY_SALES = False


def _timestamp_at(data: bytes, pos: int) -> float:
    """
    Seconds since the recording started, read from in front of an event.

    Every event is preceded by a float32 and three zero bytes, so the stamp
    sits at pos-7. Anything that does not decode to a plausible match time is
    reported as infinite, which keeps a bad read from passing for an early one.
    """
    if pos < 7:
        return math.inf
    when = struct.unpack_from(">f", data, pos - 7)[0]
    if math.isnan(when) or math.isinf(when) or not 0.0 <= when < 1e5:
        return math.inf
    return when


def _is_refund(amount: float) -> bool:
    """Whether a purse increase is shaped like half of an item's price."""
    return abs(amount - round(amount / _REFUND_STEP) * _REFUND_STEP) <= _SALE_TOLERANCE


def _sales_only(
    steps: List[Tuple[int, float, float]],
) -> List[Tuple[int, float]]:
    """
    Keep the purse increases that are sales, drop the end-of-match liquidation.

    Splitting on a gap is what separates them: liquidation arrives as one
    tight run of reports, so any run of _LIQUIDATION_RUN or more is discarded
    whole. Taking only the first few of such a run would be worse than taking
    none, because the items it names are exactly the ones the player kept.

    Args:
        steps: [(byte_offset, timestamp, increase)] in report order

    Returns:
        [(byte_offset, refund)] for the increases that look like sales
    """
    runs: List[List[Tuple[int, float, float]]] = []
    for step in steps:
        if runs and step[1] - runs[-1][-1][1] <= _LIQUIDATION_GAP:
            runs[-1].append(step)
        else:
            runs.append([step])
    return [
        (offset, step)
        for run in runs
        if len(run) < _LIQUIDATION_RUN
        for offset, _, step in run
        if step > _SALE_TOLERANCE and _is_refund(step)
    ]


def _pair_costs(
    acquires: List[Tuple[int, int]],
    costs: List[Tuple[int, float]],
) -> Dict[int, float]:
    """
    Match each acquire with the purchase cost logged beside it.

    The cost is what the player actually handed over, which is the full price
    only when they held none of the components - buying a result you already
    have parts for is charged the difference. That is what makes the amount
    usable for identifying an item, and for pricing what a sale gave back.

    Args:
        acquires: [(byte_offset, item_id)]
        costs: [(byte_offset, amount)] sorted by offset, amounts positive

    Returns:
        {acquire_offset: amount} for acquires with a cost nearby
    """
    positions = [pos for pos, _ in costs]
    paid: Dict[int, float] = {}
    for offset, _ in acquires:
        j = bisect.bisect_left(positions, offset)
        best: Optional[Tuple[int, float]] = None
        for k in (j - 1, j):
            if 0 <= k < len(costs) and abs(costs[k][0] - offset) <= _COST_WINDOW:
                if best is None or abs(costs[k][0] - offset) < abs(best[0] - offset):
                    best = costs[k]
        if best is not None:
            paid[offset] = best[1]
    return paid


def _estimate_final_build(
    acquires: List[Tuple[int, int]],
    costs: List[Tuple[int, float]] = (),
    sales: List[Tuple[int, float]] = (),
) -> List[str]:
    """
    Replay the purchases and return up to 6 items (final build).

    Two passes, because each catches what the other cannot:

    1. Inventory replay against RECIPES. Buying a result consumes one of each
       component, so a component bought three times and upgraded twice still
       leaves one. Counting is what makes that expressible - the older
       set-of-purchased-ids could only say "bought at some point".
    2. Order-aware strip against UPGRADE_TREE. A component bought after the
       result it feeds was never eaten by it, and pass 1 misses that because it
       consumes at the moment of the upgrade. UPGRADE_TREE is transitive, so one
       sweep compares each component against every result it could have fed.

    Pass 2 drops a component outright rather than decrementing it, so it can
    discard copies pass 1 says are still held - buy three Weapon Blades, upgrade
    one, and none survive. Decrementing instead is the coherent reading and was
    measured: it scores 97.5%/90.0% against 98.0%/90.9%, because holding spare
    copies of a component is rarer than the log's repeat purchases suggest.
    The weaker-looking rule wins on the data, so it is the one that ships.

    A sale leaves no event of its own, so pass 1 is also told what each held
    copy cost: a refund is half of that, which is enough to say which item went
    back to the shop. See _detect_wallet for where the refunds come from.

    Args:
        acquires: [(byte_offset, item_id)] in purchase order
        costs: [(byte_offset, amount)] purchase costs, sorted, positive
        sales: [(byte_offset, refund)] refunds inferred from wallet reports

    Returns:
        List of item names in final 6-slot build, sorted by tier desc
    """
    # Pass 1: replay purchases, consuming components as results are bought.
    # `spent_on` shadows the counts with what each held copy is worth, so a
    # refund can be traced back to the copy it came from. None means the price
    # was not readable and that copy can never answer for a sale.
    inventory: Dict[int, int] = defaultdict(int)
    spent_on: Dict[int, List[Optional[float]]] = defaultdict(list)
    paid = _pair_costs(acquires, costs) if sales else {}
    for offset, iid in sorted(acquires):
        recovered, priced = 0.0, offset in paid
        for comp_id in RECIPES.get(iid, ()):
            if inventory[comp_id] > 0:
                inventory[comp_id] -= 1
                consumed = spent_on[comp_id].pop() if spent_on[comp_id] else None
                if consumed is None:
                    priced = False
                else:
                    recovered += consumed
        inventory[iid] += 1
        spent_on[iid].append(paid[offset] + recovered if priced else None)

    # Sales. The refund is half of everything the player put into the item,
    # components included, so double it and look for the copy that cost that
    # much. Drop it only when exactly one copy answers: an ambiguous refund
    # would otherwise cost a real item, and keeping a sold one is the cheaper
    # mistake.
    sold = 0
    for _, refund in sales:
        target = 2 * refund
        matched = [
            (iid, slot)
            for iid, stack in spent_on.items()
            for slot, amount in enumerate(stack)
            if amount is not None and abs(amount - target) <= _SALE_TOLERANCE
        ]
        if len(matched) == 1:
            iid, slot = matched[0]
            spent_on[iid].pop(slot)
            inventory[iid] -= 1
            sold += 1

    # Last purchase of each item, used both to strip and to rank.
    seq: Dict[int, int] = {}
    for offset, iid in acquires:
        if offset > seq.get(iid, -1):
            seq[iid] = offset

    remaining = {iid for iid, n in inventory.items() if n > 0} - STARTER_IDS

    # Pass 2: drop components whose result was bought at or after them.
    for comp_id in list(remaining):
        results = UPGRADE_TREE.get(comp_id, set()) & remaining
        if results and any(seq.get(r, 0) >= seq.get(comp_id, 0) for r in results):
            remaining.discard(comp_id)

    # Convert to named items, dropping consumables bought early enough that the
    # player has almost certainly spent them since.
    last_offset = max((offset for offset, _ in acquires), default=0)
    consumable_cutoff = last_offset * CONSUMABLE_KEEP_FRACTION
    items = []
    for iid in remaining:
        info = ITEM_ID_MAP.get(iid)
        ts = seq.get(iid, 0)
        if info:
            tier = info.get('tier', 0)
            if tier < 1 and ts < consumable_cutoff:
                continue
            items.append((tier, ts, info['name'], iid))
        else:
            items.append((-1, ts, f"Unknown_{iid}", iid))

    # Rank for the 6-slot inventory limit:
    #   1) completed T3 items - held for the rest of the match, so an early
    #      purchase must not be pushed out by components bought later
    #   2) T1/T2 items, most recent first - unconsumed components a player is
    #      still carrying are the ones they bought last
    #   3) consumables (T0: infusions, traps) only fill leftover slots
    # Ranking tier ahead of recency across ALL tiers instead loses the low-tier
    # components players genuinely end the match holding.
    def _slot_rank(entry):
        tier, acquired = entry[0], entry[1]
        bucket = 0 if tier >= 3 else (1 if tier >= 1 else 2)
        return (bucket, -acquired)

    # A sale empties a slot and the player has to be seen buying something to
    # fill it again, so the freed slot stays free rather than being handed to
    # the next candidate. Reim in match 7 is the case that settles it: the
    # screenshot shows five items and one empty slot, and without this the
    # Teleport Boots he sold were replaced by a Warmail he never held.
    selected = sorted(items, key=_slot_rank)[:max(1, 6 - sold)]

    selected.sort(key=lambda x: (-x[0], -x[1]))
    return [name for _, _, name, _ in selected]


@dataclass
class ObjectiveEvent:
    """Detected objective event (Gold Mine/Ghostwing capture or Kraken/Blackclaw death)."""
    timestamp: float
    event_type: str  # 3v3: GOLD_MINE_CAPTURE, KRAKEN_DEATH/WAVE. 5v5: GHOSTWING_CAPTURE, BLACKCLAW_DEATH/WAVE
    entity_count: int
    entity_ids: List[int] = field(default_factory=list)
    # Filled only on mythic captures, where the payout names the team outright.
    capturing_team: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class DecodedPlayer:
    """Player data from unified decoding."""
    name: str
    team: str                          # "left" / "right"
    hero_name: str
    hero_id: Optional[int]
    entity_id: int                     # Little Endian (original)
    # Final native counters require source-bound final-screen validation.
    kills: Optional[int] = None
    deaths: Optional[int] = None
    assists: Optional[int] = None
    minion_kills: Optional[int] = None
    jungle_kills: int = 0  # action 0x0D credit count
    # [(timestamp, x, z)] on the ground plane, only when decode(detect_positions=True)
    positions: List[Tuple[float, float, float]] = field(default_factory=list)
    # Which half of the map this player's team spawned on: "low_x", "high_x",
    # or "" when positions were not read. Measured from the coordinates rather
    # than copied off team_byte, so that a replay where the two disagree shows
    # up instead of being assumed away. Unlike `team` this survives comparison
    # with anything outside the decoder, because it names the map and not a
    # column in a screenshot.
    map_side: str = ""
    gold_spent: int = 0
    gold_earned: Optional[int] = None
    observed_gold_estimate: Optional[int] = None
    gold_status: str = "partial_final_validation_missing"
    entity_id_be: Optional[int] = None
    replay_scope: Optional[str] = None
    items: List[str] = field(default_factory=list)  # Final build (after upgrade tree filtering)
    # Raw acquire log, kept unfiltered. Includes the STARTER_IDS items every
    # player is handed at match start, so subtract those before reading it as
    # purchase frequency.
    items_all_purchased: List[str] = field(default_factory=list)
    # Comparison fields (populated when truth is available)
    truth_kills: Optional[int] = None
    truth_deaths: Optional[int] = None

    def to_dict(self) -> Dict:
        return asdict(self)


class DurationProvenance(TypedDict):
    status: Literal['unknown', 'estimated', 'supplied_truth']
    source: str | None
    reason: str
    accepted_for_index: Literal[False]
    replay_scope: str | None
    selected_match: NotRequired[dict[str, str]]


def _unknown_duration_provenance() -> DurationProvenance:
    return {'status': 'unknown', 'source': None,
            'reason': 'No duration provenance was supplied.',
            'accepted_for_index': False, 'replay_scope': None}


@dataclass
class DecodedMatch:
    """Complete decoded match data."""
    replay_name: str
    replay_path: str
    game_mode: str
    map_name: str
    team_size: int
    duration_seconds: Optional[int] = None
    winner: Optional[str] = None
    left_team: List[DecodedPlayer] = field(default_factory=list)
    right_team: List[DecodedPlayer] = field(default_factory=list)
    total_frames: int = 0
    crystal_death_ts: Optional[float] = None
    crystal_death_eid: Optional[int] = None
    objective_events: List[ObjectiveEvent] = field(default_factory=list)
    # Ghostwing and Blackclaw captures read off the payout, with the capturing
    # team named by whoever received it. Deliberately a separate list from
    # objective_events: the two detectors work from different evidence and
    # merging them would double-count the same capture.
    mythic_captures: List[ObjectiveEvent] = field(default_factory=list)
    # Destroyed turrets, same idea: the team that was paid took it, and
    # entity_count is how many of them were standing at the turret.
    turret_kills: List[ObjectiveEvent] = field(default_factory=list)
    # How much game time the .vgr sections cover, from the section count.
    recorded_seconds: Optional[int] = None
    # duration_seconds / recorded_seconds. Near 1.0 when the event stream runs
    # to the end of the recording; well below when the recording outlasts it.
    completeness_ratio: Optional[float] = None
    # True requires corroborated terminal evidence, False identifies a short
    # event tail, and None means the available evidence is undecidable.
    data_complete: Optional[bool] = None
    completeness_reason: str = ""
    native_stats_status: str = "unavailable"
    native_stats_reason: str = ""
    as_of_game_time: Optional[float] = None
    # Detection flags
    kda_detection_used: bool = False
    win_detection_used: bool = False
    item_detection_used: bool = False
    team_labels_reliable: bool = False  # left/right labels may not match API convention
    final_validation_status: str = "unverified"
    final_stats_reason: str = ""
    recording_evidence: Optional[Dict] = None
    duration_provenance: DurationProvenance = field(default_factory=_unknown_duration_provenance)

    @property
    def all_players(self) -> List[DecodedPlayer]:
        return self.left_team + self.right_team

    def to_dict(self) -> Dict:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


class UnifiedDecoder:
    """
    Single entry point for complete VGR replay analysis.

    Orchestrates VGRParser, KDADetector, WinLossDetector, and ItemExtractor
    to produce a fully decoded match result.
    """

    def __init__(self, replay_path: str):
        """
        Args:
            replay_path: Path to .0.vgr file or replay cache folder.
        """
        self.replay_path = Path(replay_path)

    def decode(self, detect_items: bool = False,
               detect_positions: bool = False) -> DecodedMatch:
        """
        Run full decoding pipeline.

        Capture queries belong to decoder_v2.decode_match(at_game_time=...),
        because items and gold here are decoded over the whole recording.

        Args:
            detect_items: If True, also run ItemExtractor (partial accuracy).
            detect_positions: If True, fill DecodedPlayer.positions. Off by
                default because it adds roughly 1800 points a match to the
                output and nothing downstream reads them yet.

        Returns:
            DecodedMatch with all detected fields populated.
        """
        # --- Step 1: Basic parsing (frame 0) ---
        parser = VGRParser(
            str(self.replay_path),
            detect_heroes=False,
            auto_truth=False,
        )
        parsed = parser.parse()

        match_info = parsed.get("match_info", {})
        replay_name = parsed.get("replay_name", "")
        replay_file = parsed.get("replay_file", str(self.replay_path))

        # Resolve frame directory
        replay_file_path = Path(replay_file)
        frame_dir = replay_file_path.parent
        frame_name = replay_file_path.stem.rsplit('.', 1)[0]

        # Build player list from parsed teams
        left_parsed = parsed.get("teams", {}).get("left", [])
        right_parsed = parsed.get("teams", {}).get("right", [])

        left_team = [self._make_player(p) for p in left_parsed]
        right_team = [self._make_player(p) for p in right_parsed]
        all_players = left_team + right_team

        # --- Step 2: Load all frames ---
        frames = self._load_frames(frame_dir, frame_name)
        # Section count describes the loaded bytes, so derive it from `frames`
        # rather than re-globbing: unreadable or filtered sections must not
        # inflate the recording length we compare the event stream against.
        recorded_seconds = (
            (max(idx for idx, _ in frames) + 1) * SECONDS_PER_SECTION if frames else None
        )

        # --- Step 3: KDA Scanning (event collection only, no filtering yet) ---
        kda_used = False
        duration_est = None
        kda_detector = None
        eid_map_be_kda = {}  # BE -> player
        team_map_kda = {}    # BE -> team name
        if frames and all_players:
            kda_detector, eid_map_be_kda, team_map_kda, duration_est = \
                self._scan_kda_events(frames, all_players)
            kda_used = kda_detector is not None

        # --- Step 4: Win/Loss Detection ---
        # Observe the legacy terminal candidate. Its team label is unverified
        # and does not authorize winner output.
        win_used = False
        winner = None
        try:
            import io
            detector = WinLossDetector(str(self.replay_path))
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()
            try:
                outcome = detector.detect_winner()
            finally:
                sys.stdout = old_stdout
            if outcome:
                win_used = True
        except Exception:
            pass

        # --- Step 5: Per-player Item Detection via [10 04 3D] ---
        item_used = False
        mythic_captures: List[ObjectiveEvent] = []
        turret_kills: List[ObjectiveEvent] = []
        all_data = b"".join(data for _, data in frames) if frames else b""
        if all_data and all_players:
            eid_map_be = {}
            identity_counts = Counter(player.entity_id for player in all_players)
            for player in all_players:
                if isinstance(player.entity_id, int) and not isinstance(player.entity_id, bool) and 0 < player.entity_id <= 0xFFFF and identity_counts[player.entity_id] == 1:
                    eid_be = _le_to_be(player.entity_id)
                    eid_map_be[eid_be] = player
            if eid_map_be:
                self._detect_items_per_player(all_data, eid_map_be)
                self._detect_gold_per_player(frames, eid_map_be)
                item_used = True
            if eid_map_be:
                mythic_captures = self._detect_mythic_captures(all_data, eid_map_be)
                turret_kills = self._detect_turret_kills(all_data, eid_map_be)
            if eid_map_be and detect_positions:
                self._detect_positions(all_data, eid_map_be)
                self._assign_map_sides(all_players)

        # --- Step 6: Crystal Death Detection ---
        crystal_ts = None
        crystal_eid = None
        if all_data:
            crystal_ts, crystal_eid = self._detect_crystal_death(
                all_data, duration_est
            )

        # --- Step 7: Duration estimation ---
        # Crystal death is preferred but eid 2000-2005 can be turrets.
        # If crystal is much earlier than max player death, it's a FP.
        duration = None
        duration_source = None
        if crystal_ts is not None and duration_est is not None:
            if crystal_ts >= duration_est - 30:
                # Crystal death is at or after last player death → valid
                duration = int(crystal_ts)
                duration_source = 'crystal_death_candidate'
            else:
                # Crystal death is much earlier → false positive turret
                duration = int(duration_est)
                duration_source = 'last_player_death'
        elif crystal_ts is not None:
            duration = int(crystal_ts)
            duration_source = 'crystal_death_candidate'
        elif duration_est is not None:
            duration = int(duration_est)
            duration_source = 'last_player_death'

        # --- Step 7a: Completeness ---
        # The event stream ending long before the recording does means the tail
        # was not captured. Coverage and terminal candidates do not establish
        # final-screen validation. See
        # vg/docs/COMPLETENESS_EVIDENCE_2026-09-06.md.
        completeness = None
        if duration and recorded_seconds:
            completeness = duration / recorded_seconds
        data_complete, completeness_reason = _assess_core_completeness(
            duration, recorded_seconds, crystal_ts, duration_est,
        )

        from vg.core.native_stats import read_native_stats
        evidence = inspect_replay_evidence(frames)
        clock = evidence.native_clock
        native = read_native_stats(
            frames, {_le_to_be(p.entity_id) for p in all_players if p.entity_id},
        )
        if not clock.valid:
            data_complete = None
            completeness_reason = f"Native clock integrity failed ({clock.status}): {clock.reason}"
        kda_used = False
        for player in all_players:
            player.entity_id_be = _le_to_be(player.entity_id) if player.entity_id else None
            player.replay_scope = evidence.replay_scope
            player.observed_gold_estimate = player.gold_earned
            player.gold_earned = None
            player.kills = player.deaths = player.assists = player.minion_kills = None

        # --- Step 8: Objective event detection ---
        # 3v3: Kraken / Gold Mine.  5v5: Blackclaw / Ghostwing
        game_mode = match_info.get("mode", "")
        is_5v5 = "5v5" in game_mode
        objective_events = []
        if all_data:
            objective_events = self._detect_objective_events(
                all_data, is_5v5=is_5v5,
            )

        # --- Step 9: Assemble result ---
        return DecodedMatch(
            replay_name=replay_name,
            replay_path=str(replay_file),
            game_mode=match_info.get("mode", "Unknown"),
            map_name=match_info.get("map_name", "Unknown"),
            team_size=match_info.get("team_size", 3),
            duration_seconds=duration,
            duration_provenance={
                'status': 'estimated' if duration is not None else 'unknown',
                'source': duration_source,
                'reason': ('Legacy event timing estimates duration without final-screen validation.'
                           if duration is not None else 'No duration estimate is available.'),
                'accepted_for_index': False,
                'replay_scope': evidence.replay_scope,
            },
            winner=winner,
            left_team=left_team,
            right_team=right_team,
            total_frames=match_info.get("total_frames", 0),
            crystal_death_ts=crystal_ts,
            crystal_death_eid=crystal_eid,
            recorded_seconds=recorded_seconds,
            completeness_ratio=round(completeness, 3) if completeness else None,
            data_complete=data_complete,
            completeness_reason=completeness_reason,
            native_stats_status=native.status,
            native_stats_reason=native.reason,
            as_of_game_time=native.as_of_game_time,
            final_stats_reason=final_field_reason('statistics'),
            recording_evidence=asdict(evidence),
            objective_events=objective_events,
            mythic_captures=mythic_captures,
            turret_kills=turret_kills,
            kda_detection_used=kda_used,
            win_detection_used=win_used,
            item_detection_used=item_used,
        )

    def decode_with_truth(self, truth_path: str) -> DecodedMatch:
        """
        Decode and attach truth data for comparison.

        Args:
            truth_path: Path to tournament_truth.json.

        Returns:
            DecodedMatch with truth_kills/truth_deaths populated.
        """
        match = self.decode()
        truth = self._load_truth(truth_path, match.replay_name)
        if not truth:
            return match

        # Apply truth duration/winner
        truth_info = truth.get("match_info", {})
        if truth_info.get("duration_seconds") is not None:
            match.duration_seconds = truth_info["duration_seconds"]
            match.duration_provenance = {
                'status': 'supplied_truth',
                'source': str(truth_path),
                'reason': 'Duration was supplied by the selected truth record; final validation is not established.',
                'accepted_for_index': False,
                'replay_scope': match.duration_provenance['replay_scope'],
                'selected_match': {key: truth[key] for key in ('replay_name', 'replay_file') if key in truth},
            }
        if truth_info.get("winner"):
            # Keep detected winner, truth is for comparison

            pass

        # Apply truth K/D per player
        truth_players = truth.get("players", {})
        for player in match.all_players:
            tp = truth_players.get(player.name, {})
            if tp:
                player.truth_kills = tp.get("kills")
                player.truth_deaths = tp.get("deaths")

        # Note: KDA is NOT re-run with truth duration. The decoder's own
        # duration estimate (from crystal death / max death timestamp)
        # provides better post-game filtering.

        return match

    def _make_player(self, p: Dict) -> DecodedPlayer:
        """Convert parser player dict to DecodedPlayer."""
        return DecodedPlayer(
            name=p.get("name", "Unknown"),
            team=p.get("team", "unknown"),
            hero_name=p.get("hero_name", "Unknown"),
            hero_id=p.get("hero_id"),
            entity_id=p.get("entity_id", 0),
        )

    def _load_frames(self, frame_dir: Path, replay_name: str) -> List[tuple]:
        """Load all frame files as (frame_idx, data) tuples."""
        frame_files = list(frame_dir.glob(f"{replay_name}.*.vgr"))
        if not frame_files:
            return []

        def _idx(p: Path) -> int:
            try:
                return int(p.stem.split('.')[-1])
            except ValueError:
                return 0

        frame_files.sort(key=_idx)
        return [(_idx(f), f.read_bytes()) for f in frame_files]

    def _scan_kda_events(
        self,
        frames: List[tuple],
        all_players: List[DecodedPlayer],
    ) -> tuple:
        """
        Scan all frames for KDA events (no filtering applied yet).

        Returns:
            (detector, eid_map, team_map, duration_estimate)
            detector is None if no valid entity IDs found.
        """
        # Build BE entity ID set and LE→BE mapping
        eid_map = {}  # BE -> player
        valid_eids = set()
        team_map = {}  # BE -> team name
        for player in all_players:
            if player.entity_id:
                eid_be = _le_to_be(player.entity_id)
                eid_map[eid_be] = player
                valid_eids.add(eid_be)
                team_map[eid_be] = player.team

        if not valid_eids:
            return None, {}, {}, None

        detector = KDADetector(valid_eids)
        for frame_idx, data in frames:
            detector.process_frame(frame_idx, data)

        # Estimate duration from max death timestamp
        duration_est = None
        if detector.death_events:
            duration_est = max(d.timestamp for d in detector.death_events)

        return detector, eid_map, team_map, duration_est

    def _detect_wallet(
        self,
        all_data: bytes,
        valid_eids: Set[int],
    ) -> Tuple[Dict[int, List[Tuple[int, float]]], Dict[int, List[Tuple[int, float]]]]:
        """
        Read purchase costs, and infer sales from the wallet reports.

        A credit event carrying sell_flag=0x01 is not a delta at all: it states
        what the player is holding. Subtract the running (earned - spent) and
        what is left is starting gold plus every refund so far, which is why
        these values were right to keep out of income - counting them would
        have double-counted the whole purse.

        The residual is flat across a match - 750 in 37 of the 47 matches that
        report a purse - so the match minimum is the starting gold and any rise
        above it is a sale. 93.6% of those rises are a multiple of 25 and the
        common ones (150, 550, 700, 850, 1250) are half of a real item price,
        which is what makes them readable as refunds at all.

        Sales before the first report or after the last one are invisible, and
        two sales between one report and the next arrive added together. Both
        show up as a refund matching no single item, which is dropped.

        The residual also absorbs every error in the income accounting, and
        there is one: balances still run negative for some players, so gold is
        being earned somewhere this decoder does not see. That missing income
        creeps into the residual and reads as a run of sales, which is what
        _REFUND_STEP and _MAX_SALES_PER_PLAYER exist to blunt. Left unguarded
        it stripped three players of three or four tier-3 items each. None of
        this is measurable on the tuning set - matches 1 to 4 report almost no
        purse at all - so the guards answer to manual reading, not to a score.

        Args:
            all_data: concatenated replay bytes
            valid_eids: entity IDs of the players

        Returns:
            ({eid: [(offset, cost)]}, {eid: [(offset, refund)]}), both sorted
        """
        costs: Dict[int, List[Tuple[int, float]]] = defaultdict(list)
        sales: Dict[int, List[Tuple[int, float]]] = defaultdict(list)
        purse: Dict[int, List[Tuple[int, float, float]]] = defaultdict(list)
        earned: Dict[int, float] = defaultdict(float)
        spent: Dict[int, float] = defaultdict(float)
        small_income: Counter = Counter()
        first_seen: Dict[float, float] = {}

        pos = 0
        while True:
            pos = all_data.find(_CREDIT_HEADER, pos)
            if pos == -1:
                break
            if pos + 13 > len(all_data) or all_data[pos + 3:pos + 5] != b'\x00\x00':
                pos += 1
                continue
            eid = struct.unpack_from(">H", all_data, pos + 5)[0]
            if eid not in valid_eids or all_data[pos + 11] != 0x06:
                pos += 3
                continue
            value = struct.unpack_from(">f", all_data, pos + 7)[0]
            if math.isnan(value) or math.isinf(value):
                pos += 3
                continue
            if value < 0:
                spent[eid] += -value
                costs[eid].append((pos, -value))
            elif all_data[pos + 12] == 0x01:
                purse[eid].append((pos, _timestamp_at(all_data, pos),
                                   value - (earned[eid] - spent[eid])))
            else:
                earned[eid] += value
                if _PASSIVE_TICK_MIN <= value <= _PASSIVE_TICK_MAX:
                    amount = round(value, 2)
                    small_income[amount] += 1
                    when = _timestamp_at(all_data, pos)
                    if when < first_seen.get(amount, math.inf):
                        first_seen[amount] = when
            pos += 3

        # The tick is whichever small income repeats most; its first appearance
        # dates the recording.
        first_tick = math.inf
        if small_income:
            first_tick = first_seen[small_income.most_common(1)[0][0]]

        # A recording that joined the match late has no usable baseline: both
        # the income and the spending before it started are missing, so the
        # residual is not starting gold plus refunds but starting gold plus
        # whatever those two happened to differ by. The corpus's late joins
        # produce baselines of 461, 388 and 261.5 - none of them a multiple of
        # 25, which is the tell that they mean nothing.
        if first_tick < _MATCH_START_CUTOFF:
            return costs, sales

        residuals = [r for reports in purse.values() for _, _, r in reports]
        if not residuals:
            return costs, sales
        starting_gold = min(residuals)
        for eid, reports in purse.items():
            steps, previous = [], 0.0
            for offset, timestamp, residual in reports:
                refunded = residual - starting_gold
                steps.append((offset, timestamp, refunded - previous))
                previous = refunded
            for offset, step in _sales_only(steps):
                sales[eid].append((offset, step))
        return costs, sales

    def _detect_positions(
        self,
        all_data: bytes,
        eid_map: Dict[int, 'DecodedPlayer'],
    ) -> None:
        """
        Fill each player's ground-plane positions from the two events that
        carry them.

        Layout is the usual one - header, 00 00, entity - followed by three
        float32 BE. The middle of the three is height and sits at zero on this
        map, which is what identifies the triple; a point is dropped if it
        leaves the ground or leaves the map.

        That guard almost never fires. An earlier note here put it at 86% and
        91% of the two events, which was wrong: it counted every occurrence of
        the three header bytes, including the ones that fail the 00 00 check and
        so are byte coincidences rather than events. Among real events 100% and
        99.5% carry a usable position.

        Filtering to eid_map is what keeps this to heroes. The headers do fire
        for other entities - around 70 of them a match, moving in groups of four
        the way minion waves do - but they sit far above the player range and
        contribute a handful of points each against hundreds per player. None of
        them are stationary, so no camp or turret is being read as a hero.

        Args:
            all_data: concatenated replay bytes
            eid_map: BE entity ID -> player
        """
        for header, offset in _POSITION_EVENTS:
            pos = 0
            while True:
                pos = all_data.find(header, pos)
                if pos == -1:
                    break
                end = pos + offset + 12
                if end > len(all_data) or all_data[pos + 3:pos + 5] != b'\x00\x00':
                    pos += 3
                    continue
                player = eid_map.get(struct.unpack_from(">H", all_data, pos + 5)[0])
                if player is None:
                    pos += 3
                    continue
                x, y, z = struct.unpack_from(">fff", all_data, pos + offset)
                if (not any(math.isnan(v) or math.isinf(v) for v in (x, y, z))
                        and abs(y) <= _POSITION_GROUND_LIMIT
                        and abs(x) <= _POSITION_MAP_LIMIT
                        and abs(z) <= _POSITION_MAP_LIMIT):
                    player.positions.append((_timestamp_at(all_data, pos), x, z))
                pos += 3
        for player in eid_map.values():
            player.positions.sort()

    @staticmethod
    def _assign_map_sides(players: List['DecodedPlayer']) -> None:
        """
        Name each team's half of the map from where its players actually were.

        The two teams are told apart by median x: one sits low, the other high.
        Medians rather than means because a player who spends the match roaming
        should not drag their team across the map, and because the samples are
        sparse enough that one outlier is a real risk.

        This deliberately measures instead of reading team_byte, even though the
        two agree in all 11 truth matches. Copying the byte would make the
        agreement unfalsifiable; measuring leaves it a claim that a future
        replay can break.

        Left as "" when a team has no coordinates, or when the two medians are
        equal and there is nothing to order.
        """
        by_team: Dict[str, List[float]] = defaultdict(list)
        for player in players:
            by_team[player.team].extend(x for _, x, _ in player.positions)
        sides = {team: statistics.median(xs)
                 for team, xs in by_team.items() if xs}
        if len(sides) != 2:
            return
        (low, low_x), (high, _) = sorted(sides.items(), key=lambda kv: kv[1])
        if low_x == sides[high]:
            return
        for player in players:
            if player.team == low:
                player.map_side = "low_x"
            elif player.team == high:
                player.map_side = "high_x"

    @staticmethod
    def _team_credits(
        all_data: bytes,
        eid_map: Dict[int, 'DecodedPlayer'],
    ) -> List[tuple]:
        """Every positive gold credit as (timestamp, eid, amount, team), in order."""
        rows = []
        pos = 0
        while True:
            pos = all_data.find(_CREDIT_HEADER, pos)
            if pos == -1:
                break
            if pos + 13 > len(all_data) or all_data[pos + 3:pos + 5] != b'\x00\x00':
                pos += 3
                continue
            player = eid_map.get(struct.unpack_from(">H", all_data, pos + 5)[0])
            if player is not None and all_data[pos + 11] == 0x06 \
                    and all_data[pos + 12] != 0x01:
                amount = struct.unpack_from(">f", all_data, pos + 7)[0]
                when = _timestamp_at(all_data, pos)
                if amount > 0 and when < math.inf:
                    rows.append((when, player.entity_id, round(amount, 2),
                                 player.team))
            pos += 3
        rows.sort()
        return rows

    @classmethod
    def _detect_turret_kills(
        cls,
        all_data: bytes,
        eid_map: Dict[int, 'DecodedPlayer'],
    ) -> List[ObjectiveEvent]:
        """
        Find destroyed turrets from the two payments each one makes.

        Anchor on the flat 50 that goes to the whole team, then look just
        either side for the pool: a group on the same team holding equal
        shares that multiply to _TURRET_POOL. Requiring the product to be
        exact is what keeps minion gold out, and it also hands back how many
        heroes were standing at the turret.

        A turret that falls with no hero nearby pays nobody from the pool and
        is not reported. That is the price of the precision - about 61 of 442
        anchors in the corpus have no split beside them.
        """
        rows = cls._team_credits(all_data, eid_map)
        events: List[ObjectiveEvent] = []
        globals_: List[tuple] = []

        def flush() -> None:
            if len(globals_) < 2:
                return
            teams = {t for _, _, _, t in globals_}
            if len(teams) != 1:
                return
            team = teams.pop()
            when = globals_[0][0]
            near = Counter(
                amount for stamp, _, amount, side in rows
                if side == team and abs(stamp - when) <= _TURRET_LOOK
                and amount != _TURRET_GLOBAL
            )
            for amount, count in near.most_common():
                if abs(amount * count - _TURRET_POOL) < 0.5:
                    events.append(ObjectiveEvent(
                        timestamp=round(when, 2),
                        event_type="TURRET_DESTROYED",
                        entity_count=count,
                        entity_ids=[eid for _, eid, _, _ in globals_],
                        capturing_team=team,
                    ))
                    return

        for row in rows:
            if row[2] != _TURRET_GLOBAL:
                continue
            if globals_ and row[0] - globals_[-1][0] > _TURRET_TIGHT:
                flush()
                globals_ = []
            globals_.append(row)
        flush()
        return events

    @classmethod
    def _detect_mythic_captures(
        cls,
        all_data: bytes,
        eid_map: Dict[int, 'DecodedPlayer'],
    ) -> List[ObjectiveEvent]:
        """
        Find Ghostwing and Blackclaw captures from who got paid for them.

        A capture pays every living member of one team the same amount in the
        same instant, so the recipients are the capturing team - no proximity
        argument, no inference. Bursts that reach fewer than _MYTHIC_MIN_SHARE
        players are hero bounties sharing the same two values and are dropped;
        so is any burst that spans both teams, which nothing legitimate does.

        Kept apart from _detect_objective_events rather than merged into it.
        The two look for different things - a payout against an entity death -
        and appending these to the same list would have anything counting
        objectives count the captures twice.

        5v5 only in practice. Halcyon Fold has the Kraken and the Gold Mine
        instead, which pay something else, so all seven 3v3 files come back
        empty here and _detect_objective_events remains the only reading for
        that mode.
        """
        rows = [r for r in cls._team_credits(all_data, eid_map)
                if r[2] in _MYTHIC_PAYOUT]
        events: List[ObjectiveEvent] = []
        burst: List[tuple] = []

        def flush() -> None:
            if len(burst) < _MYTHIC_MIN_SHARE:
                return
            teams = {t for _, _, _, t in burst}
            if len(teams) != 1:
                return
            events.append(ObjectiveEvent(
                timestamp=round(burst[0][0], 2),
                event_type=_MYTHIC_PAYOUT[burst[0][2]],
                entity_count=len(burst),
                entity_ids=[eid for _, eid, _, _ in burst],
                capturing_team=teams.pop(),
            ))

        for row in rows:
            if burst and (row[0] - burst[-1][0] > _MYTHIC_BURST_GAP
                          or row[2] != burst[-1][2]):
                flush()
                burst = []
            burst.append(row)
        flush()
        return events

    def _detect_items_per_player(
        self,
        all_data: bytes,
        eid_map: Dict[int, 'DecodedPlayer'],
    ) -> None:
        """
        Scan [10 04 3D] item acquire events and [10 04 1D] action=0x06
        purchase costs. Assigns per-player items (final build after upgrade tree)
        and gold_spent.

        Item acquire: [10 04 3D][00 00][eid BE][00 00][qty][item_id LE][00 00][counter BE][ts f32 BE]
        Purchase cost: [10 04 1D][00 00][eid BE][cost f32 BE (negative)][06]
        """
        valid_eids = set(eid_map.keys())
        costs, sales = self._detect_wallet(all_data, valid_eids)

        # --- Scan item acquire events ---
        player_items: Dict[int, Set[int]] = defaultdict(set)  # eid -> set of item_ids
        # Ordered acquisitions, keyed by byte offset. Sections are concatenated
        # in play order, so offset is a total order over purchases and unlike the
        # float timestamp it is never missing or out of range.
        player_acquires: Dict[int, List[Tuple[int, int]]] = defaultdict(list)
        pos = 0
        while True:
            pos = all_data.find(_ITEM_ACQUIRE_HEADER, pos)
            if pos == -1:
                break
            if pos + 20 > len(all_data):
                pos += 1
                continue
            if all_data[pos + 3:pos + 5] != b'\x00\x00':
                pos += 1
                continue

            eid = struct.unpack_from(">H", all_data, pos + 5)[0]
            if eid not in valid_eids:
                pos += 1
                continue

            # qty=1 + IDs 200-255 = standard item purchase
            # qty=2 + IDs 0-27 = T3/special item completion (NOT ability upgrades)
            #   Per-player analysis: only 2-5 qty=2 events (too few for abilities)
            #   Hero distribution matches item buyers perfectly
            # ID 14 is universal (system event, not an item) - filtered below
            qty = all_data[pos + 9]
            if qty not in (1, 2):
                pos += 3
                continue

            # 16-bit BIG-ENDIAN id: high=qty(+9), low=id(+10).
            # item_id = qty*256 + low  (qty=1 -> 457-511, qty=2 -> 512-539).
            # Confirmed vs real bytes + VGNA ground truth. Old code read a
            # uint16 LE at +10 and masked to low byte, discarding the high
            # byte and collapsing 457-539 onto 0-255 (the misID bug).
            item_id = qty * 256 + all_data[pos + 10]
            item_info = ITEM_ID_MAP.get(item_id)
            if item_info:
                player_items[eid].add(item_id)
                player_acquires[eid].append((pos, item_id))

            pos += 3

        # Apply upgrade tree filtering to get final builds
        for eid, item_ids in player_items.items():
            player = eid_map.get(eid)
            if player:
                # Store all purchased items (raw)
                all_purchased = []
                for iid in sorted(item_ids):
                    info = ITEM_ID_MAP.get(iid)
                    if info:
                        all_purchased.append(info['name'])
                player.items_all_purchased = all_purchased

                # Replay the purchases to get the final build (max 6 slots).
                # Sales are read but not applied - see APPLY_SALES.
                player.items = _estimate_final_build(
                    player_acquires.get(eid, []),
                    costs.get(eid, []),
                    sales.get(eid, []) if APPLY_SALES else (),
                )

        # Gold detection moved to _detect_gold_per_player (frame-by-frame dedup)

    def _detect_gold_per_player(
        self,
        frames: List[Tuple[int, bytes]],
        eid_map: Dict[int, 'DecodedPlayer'],
    ) -> None:
        """Keep partial gold estimates inside exact, supported credit records."""
        income: Dict[int, float] = defaultdict(float)
        spent: Dict[int, float] = defaultdict(float)
        count: Dict[int, int] = defaultdict(int)
        invalid: Set[int] = set()
        malformed = False
        for _, data in frames:
            try:
                for record in iter_records(data):
                    if record.opcode != 0x041D:
                        continue
                    if record.content_length != 16:
                        malformed = True
                        continue
                    eid, value, action, operation = struct.unpack_from(">IfBB", record.payload)
                    if eid not in eid_map or action != 6:
                        continue
                    if not math.isfinite(value) or operation not in (0, 1):
                        invalid.add(eid)
                        continue
                    count[eid] += 1
                    if value < 0:
                        spent[eid] += abs(value)
                    elif operation == 0:
                        income[eid] += value
            except VGRRecordError:
                malformed = True
        for eid, player in eid_map.items():
            supported = not malformed and eid not in invalid and count[eid] > 0
            player.gold_earned = 600 + round(income[eid]) if supported else None
            player.gold_status = ("partial_final_validation_missing" if supported else
                                  "partial_unsupported_or_missing_credit_records")
            if supported:
                player.gold_spent = round(spent[eid])

    def _detect_objective_events(
        self,
        all_data: bytes,
        eid_threshold: int = 60000,
        cluster_window: float = 5.0,
        is_5v5: bool = False,
    ) -> List[ObjectiveEvent]:
        """
        Detect objective events (Gold Mine captures and Kraken deaths).

        Classification rule for single-entity deaths (n=1, eid > 60000):
          - Player kill [18 04 1C] within ±500B → KRAKEN_DEATH
          - No player kill nearby → GOLD_MINE_CAPTURE
        Multi-entity clusters (n>1) are KRAKEN_WAVE or MINION_WAVE.

        For 5v5, prefer mythic_captures and turret_kills. They read the payout,
        which only an objective makes, and they name the team from who was paid.
        This one and those two describe different events almost entirely: of 151
        payout-detected captures across 49 files, 2 have anything from this
        detector within eight seconds.

        The reason is the eid>60000 threshold, which does not isolate
        objectives. There are 67 to 94 such deaths in a match - 60017, 61129,
        62796 and so on are minions and jungle creatures - so the clusters this
        builds are mostly waves that a nearby player kill then labels. It is
        still the only reading available for 3v3, where the mythic payouts
        differ and nothing has been identified yet.

        (The timestamp read at idx+9 is not the problem, in case that looks
        suspect next to _timestamp_at's pos-7. Both agree on all 4084 objective
        deaths in the corpus.)

        Map position does not improve this and it has been tried. Objective
        entities emit no position events of their own, so the only handle is
        where the players were, and locating the densest group of them within
        three seconds of the death finds nothing an arbitrary moment does not:
        the top three clusters hold 41% of real events against 46% for the same
        count placed at evenly spaced times. What that method finds is where
        players congregate, which a few spots on the map do all match regardless
        of what died there - and the clusters mix the two objective types rather
        than separating them. See vg/docs/POSITION_EVENTS_2026-08-10.md.
        """
        # Collect all objective deaths
        deaths = []
        pos = 0
        while True:
            idx = all_data.find(_DEATH_HEADER, pos)
            if idx == -1:
                break
            pos = idx + 1
            if idx + 13 > len(all_data):
                continue
            if (all_data[idx + 3:idx + 5] != b'\x00\x00' or
                    all_data[idx + 7:idx + 9] != b'\x00\x00'):
                continue
            eid = struct.unpack_from(">H", all_data, idx + 5)[0]
            ts = struct.unpack_from(">f", all_data, idx + 9)[0]
            if eid > eid_threshold and 0 < ts < 5000:
                deaths.append((ts, eid, idx))

        if not deaths:
            return []

        deaths.sort(key=lambda x: x[0])

        # Cluster by time window
        clusters: List[List[tuple]] = []
        cur: List[tuple] = []
        for d in deaths:
            if not cur or d[0] - cur[-1][0] <= cluster_window:
                cur.append(d)
            else:
                clusters.append(cur)
                cur = [d]
        if cur:
            clusters.append(cur)

        # Classify each cluster
        events = []
        for cluster in clusters:
            ts = cluster[0][0]
            eids = [d[1] for d in cluster]
            offsets = [d[2] for d in cluster]
            n = len(cluster)

            player_kill = self._has_player_kill_nearby(all_data, offsets)

            if n == 1 and not player_kill:
                event_type = "GHOSTWING_CAPTURE" if is_5v5 else "GOLD_MINE_CAPTURE"
            elif n == 1 and player_kill:
                event_type = "BLACKCLAW_DEATH" if is_5v5 else "KRAKEN_DEATH"
            elif n > 1 and player_kill:
                event_type = "BLACKCLAW_WAVE" if is_5v5 else "KRAKEN_WAVE"
            else:
                event_type = "MINION_WAVE"

            events.append(ObjectiveEvent(
                timestamp=round(ts, 2),
                event_type=event_type,
                entity_count=n,
                entity_ids=eids,
            ))

        return events

    @staticmethod
    def _has_player_kill_nearby(
        data: bytes, offsets: List[int], window: int = 500
    ) -> bool:
        """Check if any player kill [18 04 1C] exists within window bytes."""
        for off in offsets:
            s = max(0, off - window)
            e = min(len(data), off + window)
            region = data[s:e]
            pk = 0
            while True:
                kidx = region.find(_KILL_HEADER, pk)
                if kidx == -1:
                    break
                pk = kidx + 1
                if kidx + 7 > len(region):
                    continue
                killer = struct.unpack_from(">H", region, kidx + 5)[0]
                if killer in _PLAYER_EID_RANGE:
                    return True
        return False

    def _detect_crystal_death(
        self,
        all_data: bytes,
        duration_est: Optional[float],
    ) -> Tuple[Optional[float], Optional[int]]:
        """
        Detect Vain Crystal destruction via death header for eid 2000-2005.
        The crystal death timestamp closely matches game duration.

        Returns:
            (crystal_death_ts, crystal_death_eid) or (None, None).
        """
        crystal_deaths = []
        pos = 0
        while True:
            pos = all_data.find(_DEATH_HEADER, pos)
            if pos == -1:
                break
            if pos + 13 > len(all_data):
                pos += 1
                continue
            if (all_data[pos + 3:pos + 5] != b'\x00\x00' or
                    all_data[pos + 7:pos + 9] != b'\x00\x00'):
                pos += 1
                continue

            eid = struct.unpack_from(">H", all_data, pos + 5)[0]
            ts = struct.unpack_from(">f", all_data, pos + 9)[0]

            if 2000 <= eid <= 2005 and 60 < ts < 2400:
                crystal_deaths.append((ts, eid))

            pos += 1

        if not crystal_deaths:
            return None, None

        # The crystal death is the one with the latest timestamp
        # (closest to game end). Filter: must be within ±60s of
        # duration estimate if available.
        crystal_deaths.sort(key=lambda x: x[0], reverse=True)

        if duration_est is not None:
            for ts, eid in crystal_deaths:
                if abs(ts - duration_est) < 60:
                    return ts, eid

        # No duration estimate: return latest crystal death
        return crystal_deaths[0]

    def _load_truth(self, truth_path: str, replay_name: str) -> Optional[Dict]:
        """Load truth data for a specific replay."""
        try:
            with open(truth_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            for m in data.get("matches", []):
                if m.get("replay_name") == replay_name:
                    return m
            return None
        except (FileNotFoundError, json.JSONDecodeError):
            return None


def main():
    import argparse

    arg_parser = argparse.ArgumentParser(
        description='Unified VGR Replay Decoder - decode all match data from replay files'
    )
    arg_parser.add_argument(
        'path',
        help='Path to replay folder or .0.vgr file'
    )
    arg_parser.add_argument(
        '--truth',
        help='Path to tournament_truth.json for comparison'
    )
    arg_parser.add_argument(
        '--items',
        action='store_true',
        help='(Legacy flag, items are now always detected per-player)'
    )
    arg_parser.add_argument(
        '-o', '--output',
        help='Output JSON file path (default: stdout)'
    )

    args = arg_parser.parse_args()

    decoder = UnifiedDecoder(args.path)
    if args.truth:
        match = decoder.decode_with_truth(args.truth)
    else:
        match = decoder.decode(detect_items=args.items)

    output = match.to_json()

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"Result saved to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == '__main__':
    main()
