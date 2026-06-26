import pandas as pd

class FeatureBuilder:

    def __init__(self, weekly):
        self.weekly = weekly.copy()

    def clean_weekly(self):
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
            "passing_interceptions",
            "rushing_yards",
            "carries",
            "rushing_tds",
            "receptions",
            "targets",
            "receiving_yards",
            "receiving_tds",
            "sack_fumbles_lost",
            "rushing_fumbles_lost",
            "receiving_fumbles_lost",
            "fantasy_points",
            "fantasy_points_ppr",
        ]

        return self.weekly[columns].copy()
    
    def build_season_summary(self):
        weekly = self.clean_weekly()

        regular_season = weekly[weekly["season_type"] == "REG"].copy()

        stat_columns = [
            "passing_yards",
            "passing_tds",
            "passing_interceptions",
            "carries",
            "rushing_yards",
            "rushing_tds",
            "receptions",
            "targets",
            "receiving_yards",
            "receiving_tds",
            "sack_fumbles_lost",
            "rushing_fumbles_lost",
            "receiving_fumbles_lost",
            "fantasy_points",
            "fantasy_points_ppr",
        ]

        summary = (
            regular_season
            .groupby(
                [
                    "player_id",
                    "player_display_name",
                    "position",
                    "season",
                    "team",
                ],
                as_index=False
            )
            .agg(
                games=("week", "nunique"),
                **{col: (col, "sum") for col in stat_columns}
            )
        )

        summary["fantasy_points_per_game"] = (
            summary["fantasy_points"] / summary["games"]
        )

        summary["fantasy_points_ppr_per_game"] = (
            summary["fantasy_points_ppr"] / summary["games"]
        )

        summary = summary.sort_values(
            ["season", "fantasy_points_ppr"],
            ascending=[False, False]
        )

        summary["total_touches"] = (
            summary["carries"] + summary["receptions"]
        )

        summary["opportunities"] = (
            summary["carries"] + summary["targets"]
        )

        summary["total_yards"] = (
            summary["passing_yards"] 
            + summary["rushing_yards"]
            + summary["receiving_yards"]
        )

        summary["total_tds"] = (
            summary["passing_tds"] 
            + summary["rushing_tds"]
            + summary["receiving_tds"]
        )

        summary["ppr_per_game"] = (
            summary["fantasy_points_ppr"] / summary["games"]
        )

        summary["opportunities_per_game"] = (
            summary["opportunities"] / summary["games"]
        )

        summary["touches_per_game"] = (
            summary["total_touches"] / summary["games"]
        )

        summary["ppr_per_opportunity"] = (
            summary["fantasy_points_ppr"] / summary["opportunities"]
        )

        return summary