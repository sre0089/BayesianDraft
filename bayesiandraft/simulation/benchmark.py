from time import perf_counter

from pydantic import BaseModel

from bayesiandraft.draft import DraftState
from bayesiandraft.rankings import RankingRow
from bayesiandraft.simulation.draft import simulate_remaining_draft


class SimulationBenchmarkResult(BaseModel):
    seed: int
    completed_pick_count: int
    elapsed_seconds: float
    stopped_reason: str


def benchmark_remaining_draft(
    draft_state: DraftState,
    rankings: list[RankingRow],
    *,
    seed: int = 1,
) -> SimulationBenchmarkResult:
    started = perf_counter()
    simulated = simulate_remaining_draft(draft_state, rankings, seed=seed)
    elapsed = perf_counter() - started
    return SimulationBenchmarkResult(
        seed=seed,
        completed_pick_count=len(simulated.completed_picks),
        elapsed_seconds=round(elapsed, 6),
        stopped_reason=simulated.stopped_reason,
    )
