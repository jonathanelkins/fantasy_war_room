import pandas as pd

class FeatureStore:
    
    def __init__(self, weekly, rosters=None, schedules=None):
        self.weekly = weekly.copy()
        self.rosters = rosters.copy() if rosters is not None else None
        self.schedules = schedules.copy() if schedules is not None else None

    def build(self):
        """
        Master pipeline.

        Every feature in the project starts here.
        """

        print("Building feature store...")

        feature_store = self.build_player_features()

        print(f"Built {len(feature_store):,} player seasons.")

        return feature_store
    
    def build_player_features(self):
        """
        Build one row per player-season.
        """

        weekly = self.clean_weekly()

        regular_season = weekly[weekly["season_type"] == "REG"].copy()

        regular_season["boom_game"] = regular_season["fantasy_points_ppr"] >= 25
        regular_season["solid_game"] = regular_season["fantasy_points_ppr"].between(12, 24.99)
        regular_season["bust_game"] = regular_season["fantasy_points_ppr"] < 8

        stat_columns = [
            "passing_yards",
            "passing_tds",
            "passing_interceptions",
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

        features = (
            regular_season
            .groupby(
                [
                    "player_id",
                    "player_display_name",
                    "position",
                    "season",
                    "team",
                ],
                as_index=False,
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

        features = self.add_volume_features(features)
        features = self.add_efficiency_features(features)
        features = self.add_consistency_features(features)
        features = self.add_player_metadata(features)

        features = features.sort_values(
            ["season", "fantasy_points_ppr"],
            ascending=[False,False],
        )

        return features
    
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

        return self.weekly[columns].copy()
    
    def add_volume_features(self, features):
        features = features.copy()

        features["total_touches"] = (
            features["carries"] + features["receptions"]
        )

        features["opportunities"] = (
            features["carries"] + features["targets"]
        )

        features["ppr_per_game"] = (
            features["fantasy_points_ppr"] / features["games"]
        )

        features["opportunities_per_game"] = (
            features["opportunities"] / features["games"]
        )

        features["touches_per_game"] = (
            features["total_touches"] / features["games"]
        )

        return features
    
    def add_efficiency_features(self, features):
        features = features.copy()

        features["total_yards"] = (
            features["passing_yards"]
            + features["rushing_yards"]
            + features["receiving_yards"]
        )

        features["total_tds"] = (
            features["passing_tds"]
            + features["rushing_tds"]
            + features["receiving_tds"]
        )

        features["ppr_per_opportunity"] = (
            features["fantasy_points_ppr"] / features["opportunities"]
        )

        return features

    def add_consistency_features(self, features):
        features = features.copy()

        features["consistency_score"] = (
            1 - (features["ppr_std_dev"] / features["ppr_per_game"])
        )

        features["consistency_score"] = features["consistency_score"].clip(
            lower=0,
            upper=1,
        )

        return features
    
    def add_player_metadata(self, features):
        if self.rosters is None:
            return features

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

        features = features.merge(
            metadata,
            on=["season", "team", "player_id"],
            how="left",
        )

        return features
