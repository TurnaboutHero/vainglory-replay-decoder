#!/usr/bin/env python3
"""
Replay Extractor - Unified API for Vainglory replay data extraction.

Combines player parsing, hero matching, and truth data merging
into a single cohesive extraction pipeline.
"""

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from vg.core.legacy_inputs import prepare_legacy_inputs
from vg.core.replay_input import replay_sections
from vg.core.vgr_truth import load_truth_data

# Local imports
try:
    from vgr_parser import VGRParser
    from hero_matcher import HeroMatcher, match_heroes
    from confidence_model import ConfidenceScorer, ConfidenceLevel
    from vgr_mapping import normalize_hero_name
except ImportError:
    from .vgr_parser import VGRParser
    from .hero_matcher import HeroMatcher, match_heroes
    from .confidence_model import ConfidenceScorer, ConfidenceLevel
    from .vgr_mapping import normalize_hero_name


@dataclass
class ExtractedPlayer:
    """Player data with confidence information."""
    name: str
    uuid: Optional[str] = None
    team: str = "unknown"
    entity_id: Optional[int] = None
    position: int = 0
    # Hero info
    hero_name: str = "Unknown"
    hero_id: Optional[int] = None
    hero_confidence: float = 0.0
    hero_source: str = "unknown"  # "extracted", "truth", "inferred"
    # Stats (populated from truth if available)
    kills: Optional[int] = None
    deaths: Optional[int] = None
    assists: Optional[int] = None
    gold: Optional[int] = None
    minion_kills: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ExtractedMatch:
    """Complete extracted match data."""
    replay_name: str
    replay_file: str
    game_mode: str
    game_mode_friendly: str
    map_name: str
    team_size: int
    total_frames: int
    # Teams
    left_team: List[ExtractedPlayer] = field(default_factory=list)
    right_team: List[ExtractedPlayer] = field(default_factory=list)
    # Match result (from truth if available)
    winner: Optional[str] = None
    score_left: Optional[int] = None
    score_right: Optional[int] = None
    duration_seconds: Optional[int] = None
    # Metadata
    extraction_method: str = "binary"  # "binary", "truth", "hybrid"
    extraction_timestamp: str = ""
    truth_source: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["left_team"] = [p.to_dict() if hasattr(p, 'to_dict') else p for p in self.left_team]
        result["right_team"] = [p.to_dict() if hasattr(p, 'to_dict') else p for p in self.right_team]
        return result

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @property
    def all_players(self) -> List[ExtractedPlayer]:
        return self.left_team + self.right_team


class ReplayExtractor:
    """
    Unified replay extraction API.

    Usage:
        extractor = ReplayExtractor(replay_path)
        match = extractor.extract()

        # Or with truth data:
        match = extractor.extract_with_truth(truth_path)
    """

    def __init__(self, replay_path: str):
        """
        Initialize extractor with replay path.

        Args:
            replay_path: Path to replay folder or .0.vgr file
        """
        self.replay_path = Path(replay_path)
        self.confidence_scorer = ConfidenceScorer()

    def extract(self) -> ExtractedMatch:
        """
        Extract all available data from replay binary.

        Returns:
            ExtractedMatch with binary-extracted data
        """
        # Parse basic data using VGRParser
        parser = VGRParser(
            str(self.replay_path),
            detect_heroes=False,  # We'll use our own hero detection
            auto_truth=False
        )
        parsed = parser.parse()

        # Get replay name and frames
        replay_name = parsed.get("replay_name", "")
        frame_dir = Path(parsed['replay_file']).parent

        # Read all frames for hero matching
        all_data = self._read_all_frames(frame_dir, replay_name)

        # Extract players from parsed data
        team_size = parsed.get("match_info", {}).get("team_size", 3)
        left_players = self._convert_players(parsed.get("teams", {}).get("left", []))
        right_players = self._convert_players(parsed.get("teams", {}).get("right", []))

        # Match heroes to players
        all_players = left_players + right_players
        if all_data:
            self._match_heroes_to_players(all_players, all_data, team_size)

        # Build result
        match_info = parsed.get("match_info", {})
        parser.report_inputs.recheck()
        return ExtractedMatch(
            replay_name=replay_name,
            replay_file=parsed.get("replay_file", str(self.replay_path)),
            game_mode=match_info.get("mode", "Unknown"),
            game_mode_friendly=match_info.get("mode_friendly", "Unknown"),
            map_name=match_info.get("map_name", "Unknown"),
            team_size=match_info.get("team_size", 3),
            total_frames=match_info.get("total_frames", 0),
            left_team=left_players,
            right_team=right_players,
            extraction_method="binary",
            extraction_timestamp=datetime.now().isoformat()
        )

    def extract_with_truth(self, truth_path: str) -> ExtractedMatch:
        """
        Extract data and merge with truth/OCR data.

        Args:
            truth_path: Path to tournament_truth.json or similar

        Returns:
            ExtractedMatch with hybrid (binary + truth) data
        """
        replay, inputs = prepare_legacy_inputs(str(self.replay_path), truth_path)
        match = self.extract()

        # Load truth data
        truth_data = load_truth_data(truth_path, match.replay_name, replay_file=str(replay.absolute()))

        # Merge truth data
        self._apply_truth(match, truth_data)
        match.extraction_method = "hybrid"
        match.truth_source = truth_path
        inputs.recheck()
        return match

    def _read_all_frames(self, frame_dir: Path, replay_name: str) -> bytes:
        """Read all replay frames in order."""
        return b"".join(path.read_bytes() for _, path in replay_sections(frame_dir / f'{replay_name}.0.vgr'))

    def _convert_players(self, player_dicts: List[Dict]) -> List[ExtractedPlayer]:
        """Convert parser player dicts to ExtractedPlayer objects."""
        return [
            ExtractedPlayer(
                name=p.get("name", "Unknown"),
                uuid=p.get("uuid"),
                team=p.get("team", "unknown"),
                entity_id=p.get("entity_id"),
                position=p.get("position", 0),
                hero_name=p.get("hero_name", "Unknown"),
                hero_id=p.get("hero_id"),
            )
            for p in player_dicts
        ]

    def _match_heroes_to_players(
        self,
        players: List[ExtractedPlayer],
        data: bytes,
        team_size: int
    ) -> None:
        """Run hero matching and update players in place."""
        # Run binary hero matching using the currently supported HeroMatcher API.
        matcher = HeroMatcher(data, team_size)
        candidates = matcher.detect_heroes()

        # Update players with matched heroes
        for i, player in enumerate(players):
            if i < len(candidates):
                hero = candidates[i]
                if hero.hero_name != "Unknown" or hero.hero_id is not None:
                    player.hero_name = hero.hero_name
                    player.hero_id = hero.hero_id
                    player.hero_confidence = hero.confidence
                    player.hero_source = hero.source or "binary"
                    continue
            if player.hero_name != "Unknown" or player.hero_id is not None:
                player.hero_confidence = max(player.hero_confidence, 1.0 if player.hero_id is not None else 0.0)
                player.hero_source = "binary"
            else:
                player.hero_source = "unknown"

    def _load_truth(self, truth_path: str, replay_name: str) -> Optional[Dict]:
        """Load truth data for specific replay."""
        return load_truth_data(truth_path, replay_name)

    def _apply_truth(self, match: ExtractedMatch, truth: Dict) -> None:
        """Apply truth data to extracted match."""
        # Apply match-level info
        match_info = truth.get("match_info", {})
        match.winner = match_info.get("winner")
        match.score_left = match_info.get("score_left")
        match.score_right = match_info.get("score_right")
        match.duration_seconds = match_info.get("duration_seconds")

        # Apply player-level info
        truth_players = truth.get("players", {})
        for player in match.all_players:
            player_truth = truth_players.get(player.name, {})
            if player_truth:
                # Hero info from truth (overrides binary detection)
                truth_hero = player_truth.get("hero_name")
                if truth_hero:
                    player.hero_name = normalize_hero_name(truth_hero)
                    player.hero_confidence = 1.0
                    player.hero_source = "truth"

                # Stats from truth
                player.kills = player_truth.get("kills")
                player.deaths = player_truth.get("deaths")
                player.assists = player_truth.get("assists")
                player.gold = player_truth.get("gold")
                player.minion_kills = player_truth.get("minion_kills")


def extract_replay(
    replay_path: str,
    truth_path: Optional[str] = None
) -> ExtractedMatch:
    """
    Convenience function for replay extraction.

    Args:
        replay_path: Path to replay
        truth_path: Optional truth data path

    Returns:
        ExtractedMatch
    """
    extractor = ReplayExtractor(replay_path)
    if truth_path:
        return extractor.extract_with_truth(truth_path)
    return extractor.extract()


def main(argv=None) -> int:
    import argparse
    import sys
    parser = argparse.ArgumentParser(description='Extract legacy replay metadata with optional supplied truth.')
    parser.add_argument('replay_path')
    parser.add_argument('truth_path', nargs='?')
    args = parser.parse_args(argv)
    try:
        match = extract_replay(args.replay_path, args.truth_path)
        print(match.to_json())
    except (OSError, ValueError) as error:
        print(f'extract-replay: {error}', file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
