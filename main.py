from src.config import SEASONS, LEAGUE_SETTINGS, CURRENT_SEASON
from src.loaders import NFLDataLoader
from src.feature_store import FeatureStore
from src.projection_engine import ProjectionEngine
from src.value_engine import ValueEngine
from src.draft_engine import DraftEngine
import os


loader = NFLDataLoader(SEASONS)

weekly = loader.load_weekly()
rosters = loader.load_rosters()
historical_rosters = rosters.copy()
current_loader = NFLDataLoader([CURRENT_SEASON])
current_rosters = current_loader.load_rosters()
schedules = loader.load_schedules()

store = FeatureStore(weekly, rosters, schedules, current_rosters,)
features = store.build()

latest_season = features["season"].max()

projection_features = features[
    features["position"].isin(["QB", "RB", "WR", "TE"])
].copy()

projection_engine = ProjectionEngine(
    projection_features,
    LEAGUE_SETTINGS,
    current_rosters,
)

projections = projection_engine.build()

value_engine = ValueEngine(projections, LEAGUE_SETTINGS)

projected_values = value_engine.calculate_war()

projected_values = projected_values[
    projected_values["projection_active"]
].copy()

projected_values = projected_values.sort_values(
    "draft_value_score",
    ascending=False,
)

EXPORT_DIR = "exports"

os.makedirs(EXPORT_DIR, exist_ok=True)

projected_values.to_csv(
    os.path.join(EXPORT_DIR, "projected_draft_values.csv"),
    index=False,
)

inspect = projected_values[
    projected_values["player_display_name"].isin(
        ["Jaxon Smith-Njigba", "Puka Nacua", "Amon-Ra St. Brown"]
    )
].copy()

print(
    inspect[
        [
            "player_display_name",
            "team",
            "position",
            "projected_targets",
            "target_scale_factor",
            "projected_team_player_targets",
            "projected_team_targets",
            "projected_receptions",
            "projected_receiving_yards",
            "projected_receiving_tds",
            "projected_ppr_per_game",
            "fantasy_war",
            "draft_value_score",
        ]
    ]
    .sort_values("draft_value_score", ascending=False)
    .to_string(index=False)
)