from pathlib import Path

from pydantic import BaseModel, Field

from bayesiandraft.draft.state import DraftState


class RehearsalPick(BaseModel):
    player_id: str


class RehearsalScenario(BaseModel):
    scenario_id: str
    name: str
    description: str
    picks: list[RehearsalPick] = Field(default_factory=list)


def apply_rehearsal_scenario(
    draft_state: DraftState,
    scenario: RehearsalScenario,
) -> DraftState:
    state = draft_state
    for pick in scenario.picks:
        state = state.record_pick(pick.player_id)
    return state


def load_rehearsal_scenario(path: str | Path) -> RehearsalScenario:
    return RehearsalScenario.model_validate_json(Path(path).read_text(encoding="utf-8"))
