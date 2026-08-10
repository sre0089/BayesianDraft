from scripts.common import DEFAULT_LEAGUE_CONFIG_PATH, default_cli_league_config_path


def test_default_cli_league_config_prefers_local_override() -> None:
    assert default_cli_league_config_path().name in {
        "espn_2026.yaml",
        "espn_2026.local.yaml",
    }


def test_default_draft_state_config_stays_public_safe() -> None:
    assert DEFAULT_LEAGUE_CONFIG_PATH.name == "espn_2026.yaml"
