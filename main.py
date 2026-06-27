from src.config import SEASONS, LEAGUE_SETTINGS
from src.loaders import NFLDataLoader
from src.feature_store import FeatureStore
from src.projection_engine import ProjectionEngine


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

projections = projections.sort_values(
    "projected_fantasy_points_ppr",
    ascending=False,
)

print(
    projections[
        [
            "player_display_name",
            "position",
            "team",
            "projected_games",
            "projected_carries",
            "projected_targets",
            "projected_receptions",
            "projected_rushing_yards",
            "projected_receiving_yards",
            "projected_pass_attempts",
            "projected_passing_yards",
            "projected_passing_tds",
            "projected_rushing_tds",
            "projected_receiving_tds",
            "projected_fantasy_points_ppr",
            "projected_ppr_per_game",
        ]
    ]
    .head(25)
    .to_string(index=False)
)