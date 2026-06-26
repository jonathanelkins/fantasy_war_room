from src.config import SEASONS
from src.loaders import NFLDataLoader
from src.player_profiles import PlayerProfile
from src.feature_store import FeatureStore


loader = NFLDataLoader(SEASONS)

weekly = loader.load_weekly()
rosters = loader.load_rosters()
schedules = loader.load_schedules()

store = FeatureStore(weekly, rosters, schedules)
season_summary = store.build()

latest_season = season_summary["season"].max()

rankings = (
    season_summary[
        (season_summary["season"] == latest_season)
        & (season_summary["position"].isin(["QB", "RB", "WR", "TE"]))
    ]
    .sort_values("fantasy_points_ppr", ascending=False)
    .copy()
)

player_name = "Ja'Marr Chase"

player_matches = rankings[
    rankings["player_display_name"].str.contains(
        player_name,
        case=False,
        na=False,
        regex=False,
    )
]

player_row = player_matches.iloc[0]

profile = PlayerProfile(player_row)

print(profile.format_card())