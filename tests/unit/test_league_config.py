from pathlib import Path

import pytest
import yaml

from bayesiandraft.config import LeagueConfigError, load_league_config

CONFIG_PATH = Path("configs/leagues/espn_2026.yaml")


def test_loads_espn_2026_league_config() -> None:
    config = load_league_config(CONFIG_PATH)

    assert config.platform == "ESPN"
    assert config.season == 2026
    assert config.league.team_count == 14
    assert config.league.user_manager_id == "user_manager"
    assert config.league.user_draft_position == 8
    assert config.draft_order[7].name == "Manager 08"
    assert config.scoring.receiving.reception == 1


def test_rejects_missing_user_manager(tmp_path: Path) -> None:
    raw_config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))
    raw_config["league"]["user_manager_id"] = "missing_manager"
    config_path = tmp_path / "league.yaml"
    config_path.write_text(yaml.safe_dump(raw_config), encoding="utf-8")

    with pytest.raises(LeagueConfigError, match="Invalid league config"):
        load_league_config(config_path)
