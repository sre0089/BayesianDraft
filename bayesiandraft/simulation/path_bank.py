from collections import defaultdict
from collections.abc import Callable
from hashlib import sha256
from pathlib import Path

from pydantic import BaseModel, Field, PositiveInt

from bayesiandraft import __version__
from bayesiandraft.config import LeagueConfig
from bayesiandraft.draft import DraftState
from bayesiandraft.rankings import RankingRow
from bayesiandraft.simulation.draft import DraftSimulationConfig, simulate_remaining_draft

PATH_BANK_SCHEMA_VERSION = "1.0"
VALUE_POSITIONS = ("QB", "RB", "WR", "TE", "DST", "K")
PathBankProgressCallback = Callable[[int, int, int, str], None]


class PathBankPick(BaseModel):
    overall_pick: int
    manager_id: str
    player_id: str
    position: str


class DraftPath(BaseModel):
    path_id: str
    seed: int
    stopped_reason: str
    picks: list[PathBankPick]


class PathBankMetadata(BaseModel):
    schema_version: str = PATH_BANK_SCHEMA_VERSION
    bayesiandraft_version: str = __version__
    snapshot_id: str
    league_config_hash: str
    simulation_count: int
    seed: int
    candidate_limit: int


class DraftPathBank(BaseModel):
    metadata: PathBankMetadata
    paths: list[DraftPath]
    player_availability_by_pick: dict[str, dict[str, float]] = Field(default_factory=dict)
    position_value_by_pick: dict[str, dict[str, float]] = Field(default_factory=dict)
    position_dropoff_by_pick: dict[str, dict[str, float]] = Field(default_factory=dict)

    def save(self, path: str | Path) -> None:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(self.model_dump_json(indent=2) + "\n", encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "DraftPathBank":
        return cls.model_validate_json(Path(path).read_text(encoding="utf-8"))


def build_path_bank(
    draft_state: DraftState,
    rankings: list[RankingRow],
    *,
    snapshot_id: str,
    simulation_count: PositiveInt,
    seed: int,
    candidate_limit: PositiveInt,
    progress_callback: PathBankProgressCallback | None = None,
) -> DraftPathBank:
    paths: list[DraftPath] = []
    draft_config = DraftSimulationConfig(
        simulation_count=simulation_count,
        seed=seed,
        candidate_limit=candidate_limit,
    )
    ranking_by_id = {ranking.player_id: ranking for ranking in rankings}

    for offset in range(simulation_count):
        path_seed = seed + offset
        simulated = simulate_remaining_draft(
            draft_state,
            rankings,
            seed=path_seed,
            config=draft_config.model_copy(update={"seed": path_seed}),
        )
        picks = [
            PathBankPick(
                overall_pick=pick.overall_pick,
                manager_id=pick.manager_id,
                player_id=pick.player_id,
                position=ranking_by_id[pick.player_id].position.value,
            )
            for pick in simulated.completed_picks
            if pick.player_id in ranking_by_id
        ]
        paths.append(
            DraftPath(
                path_id=f"path_{offset + 1:06}",
                seed=path_seed,
                stopped_reason=simulated.stopped_reason,
                picks=picks,
            )
        )
        if progress_callback is not None:
            progress_callback(
                offset + 1,
                simulation_count,
                path_seed,
                simulated.stopped_reason,
            )

    if progress_callback is not None:
        progress_callback(
            simulation_count,
            simulation_count,
            seed + simulation_count - 1,
            "indexing",
        )
    return DraftPathBank(
        metadata=PathBankMetadata(
            snapshot_id=snapshot_id,
            league_config_hash=league_config_hash(draft_state.league_config),
            simulation_count=simulation_count,
            seed=seed,
            candidate_limit=candidate_limit,
        ),
        paths=paths,
        player_availability_by_pick=_player_availability_by_pick(paths),
        position_value_by_pick=_position_value_by_pick(paths, rankings),
        position_dropoff_by_pick=_position_dropoff_by_pick(paths, rankings),
    )


def league_config_hash(league_config: LeagueConfig) -> str:
    encoded = league_config.model_dump_json().encode("utf-8")
    return sha256(encoded).hexdigest()[:16]


def _player_availability_by_pick(paths: list[DraftPath]) -> dict[str, dict[str, float]]:
    if not paths:
        return {}

    pick_numbers = sorted({pick.overall_pick for path in paths for pick in path.picks})
    counts: dict[int, defaultdict[str, int]] = {
        pick_number: defaultdict(int) for pick_number in pick_numbers
    }
    for path in paths:
        drafted_before_pick: set[str] = set()
        picks_by_number = {pick.overall_pick: pick for pick in path.picks}
        for pick_number in pick_numbers:
            pick = picks_by_number.get(pick_number)
            if pick is not None:
                counts[pick_number][pick.player_id] += 0
            for player_id in _available_ids(path, drafted_before_pick):
                counts[pick_number][player_id] += 1
            if pick is not None:
                drafted_before_pick.add(pick.player_id)

    total = len(paths)
    return {
        str(pick_number): {
            player_id: round(count / total, 4)
            for player_id, count in sorted(player_counts.items())
        }
        for pick_number, player_counts in counts.items()
    }


def _position_value_by_pick(
    paths: list[DraftPath],
    rankings: list[RankingRow],
) -> dict[str, dict[str, float]]:
    return _position_summary_by_pick(paths, rankings, dropoff=False)


def _position_dropoff_by_pick(
    paths: list[DraftPath],
    rankings: list[RankingRow],
) -> dict[str, dict[str, float]]:
    return _position_summary_by_pick(paths, rankings, dropoff=True)


def _position_summary_by_pick(
    paths: list[DraftPath],
    rankings: list[RankingRow],
    *,
    dropoff: bool,
) -> dict[str, dict[str, float]]:
    if not paths:
        return {}

    ranking_by_id = {ranking.player_id: ranking for ranking in rankings}
    pick_numbers = sorted({pick.overall_pick for path in paths for pick in path.picks})
    values: dict[int, dict[str, list[float]]] = {
        pick_number: {position: [] for position in VALUE_POSITIONS}
        for pick_number in pick_numbers
    }
    for path in paths:
        drafted_before_pick: set[str] = set()
        picks_by_number = {pick.overall_pick: pick for pick in path.picks}
        for pick_number in pick_numbers:
            available_rankings = [
                ranking_by_id[player_id]
                for player_id in _available_ids(path, drafted_before_pick)
                if player_id in ranking_by_id
            ]
            for position in VALUE_POSITIONS:
                position_rows = [
                    ranking
                    for ranking in available_rankings
                    if ranking.position.value == position
                ]
                if not position_rows:
                    values[pick_number][position].append(0)
                    continue
                best_vorp = position_rows[0].vorp
                if not dropoff:
                    values[pick_number][position].append(best_vorp)
                    continue
                fifth_index = min(len(position_rows) - 1, 4)
                values[pick_number][position].append(best_vorp - position_rows[fifth_index].vorp)
            pick = picks_by_number.get(pick_number)
            if pick is not None:
                drafted_before_pick.add(pick.player_id)

    return {
        str(pick_number): {
            position: round(_mean(position_values), 4)
            for position, position_values in position_map.items()
        }
        for pick_number, position_map in values.items()
    }


def _available_ids(path: DraftPath, drafted_before_pick: set[str]) -> list[str]:
    return [
        pick.player_id
        for pick in path.picks
        if pick.player_id not in drafted_before_pick
    ]


def _mean(values: list[float]) -> float:
    if not values:
        return 0
    return sum(values) / len(values)
