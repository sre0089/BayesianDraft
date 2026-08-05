from scripts.pull_fantasypros_projections import _normalized_rows


def test_normalizes_fantasypros_projection_payload() -> None:
    payloads = {
        "RB": {
            "players": [
                {
                    "fpid": 17240,
                    "name": "Example RB",
                    "position_id": "RB",
                    "team_id": "AAA",
                    "stats": [
                        {
                            "points_ppr": 281.5,
                            "points": 220.0,
                            "rush_yds": 1100.5,
                            "rush_tds": 9.2,
                            "rec_rec": 55.0,
                            "rec_yds": 430.0,
                            "rec_tds": 3.0,
                        }
                    ],
                }
            ]
        },
        "DST": {
            "players": [
                {
                    "fpid": 9001,
                    "name": "Example Defense",
                    "position_id": "DST",
                    "team_id": "BBB",
                    "stats": {
                        "points": 118.0,
                        "def_td": 3,
                        "def_sack": 44,
                        "def_int": 15,
                        "def_fr": 9,
                        "def_safety": 1,
                    },
                }
            ]
        },
    }

    rows = _normalized_rows(payloads, scoring="PPR")

    assert rows[0]["player_id"] == "fp_17240"
    assert rows[0]["projected_points"] == "281.5"
    assert rows[0]["rushing_yards"] == "1100.5"
    assert rows[0]["receptions"] == "55.0"
    assert rows[1]["position"] == "DST"
    assert rows[1]["projected_points"] == "118.0"
    assert rows[1]["dst_sacks"] == "44"
