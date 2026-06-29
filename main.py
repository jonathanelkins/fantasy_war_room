import os

from src.config import SEASONS, LEAGUE_SETTINGS, CURRENT_SEASON
from src.loaders import NFLDataLoader
from src.feature_store import FeatureStore
from src.projection_engine import ProjectionEngine
from src.role_engine import RoleEngine
from src.opportunity_engine import OpportunityEngine
from src.value_engine import ValueEngine
from src.quality_engine import QualityEngine


# -----------------------------
# Load data
# -----------------------------

loader = NFLDataLoader(SEASONS)

weekly = loader.load_weekly()
rosters = loader.load_rosters()
schedules = loader.load_schedules()

current_loader = NFLDataLoader([CURRENT_SEASON])
current_rosters = current_loader.load_rosters()


# -----------------------------
# Build features
# -----------------------------

store = FeatureStore(
    weekly,
    rosters,
    schedules,
    current_rosters,
)

features = store.build()

quality_engine = QualityEngine(features)
features, player_quality = quality_engine.build()

team_opportunity = store.build_team_opportunity_table()

projection_features = features[
    features["position"].isin(["QB", "RB", "WR", "TE"])
].copy()


# -----------------------------
# Build projections
# -----------------------------

projection_engine = ProjectionEngine(
    projection_features,
    LEAGUE_SETTINGS,
    current_rosters,
)

projections = projection_engine.build()

projections = projections.drop(
    columns=[
        col for col in ["quality_score", "quality_score_x", "quality_score_y"]
        if col in projections.columns
    ]
)

projections = projections.merge(
    player_quality,
    on="player_id",
    how="left",
)

projections["quality_score"] = projections["quality_score"].fillna(50)


# -----------------------------
# Build roles
# -----------------------------

role_engine = RoleEngine(projections)
projections = role_engine.build()


# -----------------------------
# Allocate opportunities
# -----------------------------

opportunity_engine = OpportunityEngine(
    projections,
    team_opportunity,
)

projections = opportunity_engine.build()


# -----------------------------
# Build fantasy values
# -----------------------------

value_engine = ValueEngine(
    projections,
    LEAGUE_SETTINGS,
)

projected_values = value_engine.calculate_war()

projected_values = projected_values[
    projected_values["projection_active"]
].copy()

projected_values = projected_values.sort_values(
    "draft_value_score",
    ascending=False,
)


# -----------------------------
# Export
# -----------------------------

EXPORT_DIR = "exports"

os.makedirs(EXPORT_DIR, exist_ok=True)

projected_values.to_csv(
    os.path.join(EXPORT_DIR, "projected_draft_values.csv"),
    index=False,
)

print("\nSaved exports/projected_draft_values.csv")


# -----------------------------
# Diagnostics: target weights
# -----------------------------



print("\nTarget Weight Check")
print("────────────────────────────")

target_weight_check = (
    projections[
        projections["position"].isin(["RB", "WR", "TE"])
        & projections["projection_active"]
    ]
    .groupby("team", as_index=False)
    .agg(
        total_normalized_target_weight=("normalized_target_weight", "sum"),
        active_pass_catchers=("player_display_name", "count"),
        projected_team_targets=("projected_team_targets", "max"),
        projected_player_targets=("projected_targets", "sum"),
    )
)

target_weight_check[
    [
        "total_normalized_target_weight",
        "projected_team_targets",
        "projected_player_targets",
    ]
] = target_weight_check[
    [
        "total_normalized_target_weight",
        "projected_team_targets",
        "projected_player_targets",
    ]
].round(3)

print(
    target_weight_check
    .sort_values("team")
    .to_string(index=False)
)


# -----------------------------
# Diagnostics: New England roles
# -----------------------------

print("\nNew England Role Check")
print("────────────────────────────")

inspect = projections[
    (projections["team"] == "NE")
    & (projections["position"].isin(["QB", "RB", "WR", "TE"]))
].copy()

round_cols = [
    "role_score",
    "normalized_target_weight",
    "projected_targets",
    "projected_carries",
    "projected_pass_attempts",
    "vacated_targets",
    "vacated_target_pct",
]

for col in round_cols:
    if col in inspect.columns:
        inspect[col] = inspect[col].round(3)

print(
    inspect[
        [
            "player_display_name",
            "position",
            "team",
            "role_score",
            "team_position_rank",
            "role_label",
            "projection_active",
            "normalized_target_weight",
            "vacated_targets",
            "vacated_target_pct",
            "projected_targets",
            "projected_carries",
            "projected_pass_attempts",
            "changed_teams",
        ]
    ]
    .sort_values(["position", "team_position_rank"])
    .to_string(index=False)
)


# -----------------------------
# Draft board
# -----------------------------

print("\nTop 60 Draft Board")
print("────────────────────────────")

draft_board = projected_values.copy()

draft_board = draft_board.sort_values(
    "draft_value_score",
    ascending=False,
)

draft_board["overall_rank"] = range(1, len(draft_board) + 1)
draft_board["round"] = ((draft_board["overall_rank"] - 1) // 12) + 1
draft_board["pick_in_round"] = ((draft_board["overall_rank"] - 1) % 12) + 1

display_board = draft_board.head(60).copy()

display_board[
    [
        "projected_ppr_per_game",
        "replacement_ppg",
        "fantasy_war",
        "draft_value_score",
    ]
] = display_board[
    [
        "projected_ppr_per_game",
        "replacement_ppg",
        "fantasy_war",
        "draft_value_score",
    ]
].round(2)

print(
    display_board[
        [
            "overall_rank",
            "round",
            "pick_in_round",
            "player_display_name",
            "position",
            "team",
            "value_tier",
            "projected_ppr_per_game",
            "replacement_ppg",
            "fantasy_war",
            "draft_value_score",
        ]
    ].to_string(index=False)
)

print(
    projections[
        projections["player_display_name"].isin(
            ["A.J. Brown", "Jaxon Smith-Njigba", "Puka Nacua", "Trey McBride"]
        )
    ][
        [
            "player_display_name",
            "team",
            "position",
            "quality_score",
            "base_target_weight",
            "adjusted_target_weight",
            "normalized_target_weight",
            "projected_targets",
        ]
    ]
    .sort_values("player_display_name")
    .to_string(index=False)
)