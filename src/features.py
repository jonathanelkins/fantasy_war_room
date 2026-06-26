import pandas as pd

class FeatureBuilder:

    def __init__(self, weekly, rosters=None, schedules=None):
        self.weekly = weekly.copy()
        self.rosters = rosters.copy() if rosters is not None else None
        self.schedules = schedules.copy() if schedules is not None else None

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
    
    def build_player_metadata(self):
        if self.rosters is None:
            return None
        
        metadata = self.rosters[
            [
                "season",
                "team",
                "gsis_id",
                "full_name",
                "birth_date",
                "height",
                "weight",
                "college",
                "years_exp",
                "rookie_year",
                "draft_club",
                "draft_number",
            ]
        ].copy()

        metadata = metadata.drop_duplicates(
            subset=["season", "team", "gsis_id"]
        )

        metadata = metadata.rename(
            columns={
                "gsis_id": "player_id",
                "full_name": "roster_name",    
            }
        )

        metadata["birth_date"] = pd.to_datetime(
            metadata["birth_date"],
            errors="coerce",
        )

        metadata["season_start"] = pd.to_datetime(
            metadata["season"].astype(str) + "-09-01"
        )

        metadata["age"] = (
            (metadata["season_start"] - metadata["birth_date"]).dt.days / 365.25
        )

        return metadata

    def build_season_summary(self):
        weekly = self.clean_weekly()

        regular_season = weekly[weekly["season_type"] == "REG"].copy()

        regular_season["boom_game"] = regular_season["fantasy_points_ppr"] >= 25
        regular_season["solid_game"] = regular_season["fantasy_points_ppr"].between(12, 24.99)
        regular_season["bust_game"] = regular_season["fantasy_points_ppr"] < 8

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
                boom_games=("boom_game", "sum"),
                solid_games=("solid_game", "sum"),
                bust_games=("bust_game", "sum"),
                ppr_std_dev=("fantasy_points_ppr", "std"),
                **{col: (col, "sum") for col in stat_columns}
            )
        )

        summary["fantasy_points_per_game"] = (
            summary["fantasy_points"] / summary["games"]
        )

        summary["fantasy_points_ppr_per_game"] = (
            summary["fantasy_points_ppr"] / summary["games"]
        )

        metadata = self.build_player_metadata()

        if metadata is not None:
            summary = summary.merge(
                metadata,
                on=["season", "team", "player_id"],
                how="left",
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

        summary["consistency_score"] = (
            1 - (summary["ppr_std_dev"] / summary["ppr_per_game"])
        )

        summary["consistency_score"] = summary["consistency_score"].clip(lower=0, upper=1)

        return summary
    
    