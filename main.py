from src.config import SEASONS, LEAGUE_SETTINGS
from src.loaders import NFLDataLoader
from src.feature_store import FeatureStore
from src.projection_engine import ProjectionEngine
from src.value_engine import ValueEngine
from src.draft_engine import DraftEngine
import os


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

EXPORT_DIR = "exports"

os.makedirs(EXPORT_DIR, exist_ok=True)

projected_values.to_csv(
    os.path.join(EXPORT_DIR, "projected_draft_values.csv"),
    index=False,
)

draft_engine = DraftEngine(projected_values, LEAGUE_SETTINGS)

board = draft_engine.build_board()

display_board = draft_engine.best_available(board, n=15).copy()

display_board[
    [
        "projected_ppr_per_game",
        "fantasy_war",
        "draft_value_score",
    ]
] = display_board[
    [
        "projected_ppr_per_game",
        "fantasy_war",
        "draft_value_score",
    ]
].round(2)

print(
    display_board[
        [
            "available_rank",
            "overall_rank",
            "player_display_name",
            "position",
            "team",
            "value_tier",
            "projected_ppr_per_game",
            "fantasy_war",
            "draft_value_score",
        ]
    ].to_string(index=False)
)

print(draft_engine.recommend_pick(board))