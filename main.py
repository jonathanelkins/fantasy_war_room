from src.config import SEASONS, LEAGUE_SETTINGS
from src.loaders import NFLDataLoader
from src.feature_store import FeatureStore
from src.projection_engine import ProjectionEngine
from src.value_engine import ValueEngine


loader = NFLDataLoader(SEASONS)

weekly = loader.load_weekly()
rosters = loader.load_rosters()
schedules = loader.load_schedules()

store = FeatureStore(weekly, rosters, schedules)
features = store.build()

latest_season = features["season"].max()

projection_features = features[
    features["position"].isin(["QB", "RB", "WR", "TE"])
].copy()

projection_engine = ProjectionEngine(projection_features, LEAGUE_SETTINGS)

projections = projection_engine.build()

value_engine = ValueEngine(projections, LEAGUE_SETTINGS)

projected_values = value_engine.calculate_war()

projected_values = projected_values.sort_values(
    "draft_value_score",
    ascending=False,
)

print(
    projected_values[
        [
            "war_rank",
            "position_rank",
            "player_display_name",
            "position",
            "team",
            "projected_ppr_per_game",
            "replacement_ppg",
            "fantasy_war",
            "value_tier",
            "draft_value_score",
        ]
    ]
    .head(40)
    .to_string(index=False)
)