import nflreadpy as nfl
import pandas as pd

def load_weekly_data(seasons):
    """
    Load weekly NFL player stats from nflverse.
    """
    weekly = nfl.load_player_stats(seasons)
    weekly = weekly.to_pandas()
    return weekly

def clean_weekly_data(weekly):
    """
    Keep the columns we need for fantasy projections.
    """
    columns = [
        "player_id",
        "player_display_name",
        "team",
        "season",
        "week",
        "season_type",
        "position",
        "passing_yards",
        "passing_tds",
        "interceptions",
        "rushing_yards",
        "carries",
        "rushing_tds",
        "targets",
        "receptions",
        "receiving_yards",
        "receiving_tds",
        "sack_fumbles_lost",
        "rushing_fumbles_lost",
        "receiving_fumbles_lost",
        "fantasy_points",
        "fantasy_points_ppr",
    ]

    existing_columns = [col for col in columns if col in weekly.columns]
    weekly = weekly[existing_columns].copy()
    return weekly

