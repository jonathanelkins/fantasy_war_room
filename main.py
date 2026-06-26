from src.config import SEASONS, LEAGUE_SETTINGS
from src.loaders import NFLDataLoader
from src.feature_store import FeatureStore
from src.value_engine import ValueEngine


loader = NFLDataLoader(SEASONS)

weekly = loader.load_weekly()
rosters = loader.load_rosters()
schedules = loader.load_schedules()

store = FeatureStore(weekly, rosters, schedules)
features = store.build()

latest_season = features["season"].max()

latest_features = features[
    (features["season"] == latest_season)
    & (features["position"].isin(["QB", "RB", "WR", "TE"]))
].copy()

value_engine = ValueEngine(latest_features, LEAGUE_SETTINGS)

war = value_engine.calculate_war()

war = war.sort_values("fantasy_war", ascending=False)

print(
    war[
        [
            "player_display_name",
            "position",
            "team",
            "ppr_per_game",
            "replacement_ppg",
            "fantasy_war",
            "overall_player_score",
        ]
    ]
    .head(50)
    .to_string(index=False)
)