from pathlib import Path

from bayesiandraft_api.main import create_app
from fastapi.testclient import TestClient


def test_api_exposes_league_players_and_rankings() -> None:
    client = TestClient(create_app())

    league = client.get("/league")
    players = client.get("/players")
    rankings = client.get("/rankings")

    assert league.status_code == 200
    assert league.json()["league"]["team_count"] == 14
    assert players.status_code == 200
    assert len(players.json()) == 12
    assert rankings.status_code == 200
    assert rankings.json()[0]["overall_rank"] == 1


def test_api_manual_draft_workflow() -> None:
    client = TestClient(create_app())

    created = client.post("/drafts", json={"draft_id": "api_test"}).json()
    assert created["current_overall_pick"] == 1
    assert created["manager_on_clock"] == "manager_01"

    after_pick = client.post("/drafts/api_test/picks", json={"player_id": "rb_001"}).json()
    assert after_pick["current_overall_pick"] == 2
    assert "rb_001" not in after_pick["available_player_ids"]

    user_roster = client.get("/drafts/api_test/rosters/user")
    assert user_roster.status_code == 200

    undone = client.post("/drafts/api_test/undo").json()
    assert undone["current_overall_pick"] == 1
    assert "rb_001" in undone["available_player_ids"]

    redone = client.post("/drafts/api_test/redo").json()
    assert redone["current_overall_pick"] == 2


def test_api_returns_recommendations_for_draft() -> None:
    client = TestClient(create_app())
    client.post("/drafts", json={"draft_id": "api_recs"})

    response = client.get("/drafts/api_recs/recommendations")

    assert response.status_code == 200
    body = response.json()
    assert body["primary"]["player_id"] == "rb_001"
    assert body["primary"]["explanation"]
    assert len(body["alternatives"]) == 3


def test_api_returns_candidate_rollouts_when_user_is_on_clock() -> None:
    client = TestClient(create_app())
    client.post("/drafts", json={"draft_id": "api_rollouts"})
    for player_id in ["rb_001", "wr_001", "qb_001", "rb_002", "wr_002", "te_001", "wr_003"]:
        client.post("/drafts/api_rollouts/picks", json={"player_id": player_id})

    response = client.get("/drafts/api_rollouts/candidate-rollouts?limit=2&simulation_count=4")

    assert response.status_code == 200
    body = response.json()
    assert body["simulation_count"] == 4
    assert body["primary"]["player_id"]
    assert len(body["alternatives"]) == 1


def test_api_rejects_invalid_pick() -> None:
    client = TestClient(create_app())
    client.post("/drafts", json={"draft_id": "api_bad_pick"})

    response = client.post(
        "/drafts/api_bad_pick/picks",
        json={"player_id": "missing_player"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "unknown player_id"


def test_api_save_and_load_draft(tmp_path: Path) -> None:
    client = TestClient(create_app())
    save_path = tmp_path / "draft.json"
    client.post("/drafts", json={"draft_id": "api_save"})
    client.post("/drafts/api_save/picks", json={"player_id": "rb_001"})

    save_response = client.post("/drafts/api_save/save", json={"path": str(save_path)})
    load_response = client.post("/drafts/load", json={"path": str(save_path)})

    assert save_response.status_code == 200
    assert load_response.status_code == 200
    assert load_response.json()["draft_id"] == "api_save"
    assert load_response.json()["current_overall_pick"] == 2
