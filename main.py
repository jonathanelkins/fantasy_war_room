from src.config import SEASONS
from src.loaders import NFLDataLoader
from src.features import FeatureBuilder


loader = NFLDataLoader(SEASONS)

weekly_raw = loader.load_weekly()

features = FeatureBuilder(weekly_raw)

season_summary = features.build_season_summary()

latest_season = season_summary["season"].max()

rankings = (
    season_summary[
        (season_summary["season"] == latest_season)
        & (season_summary["position"].isin(["QB", "RB", "WR", "TE"]))
    ]
    .sort_values("fantasy_points_ppr", ascending=False)
    .copy()
)

rankings["overall_rank"] = range(1, len(rankings) + 1)

rankings["position_rank"] = (
    rankings
    .groupby("position")["fantasy_points_ppr"]
    .rank(ascending=False, method="first")
    .astype(int)
)

print(rankings[
    [
        "overall_rank",
        "position_rank",
        "player_display_name",
        "position",
        "team",
        "games",
        "fantasy_points_ppr",
        "ppr_per_game",
        "opportunities_per_game",
        "touches_per_game",
    ]
].head(50))

rankings.to_csv(
    "data/exports/latest_season_rankings.csv",
    index=False
)