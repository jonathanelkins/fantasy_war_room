import pandas as pd

class FeatureStore:
    
    def __init__(self, weekly, rosters=None, schedules=None, current_rosters=None):
        self.weekly = weekly.copy()
        self.rosters = rosters.copy() if rosters is not None else None
        self.schedules = schedules.copy() if schedules is not None else None
        self.current_rosters = current_rosters.copy() if current_rosters is not None else None

    def build(self):
        """
        Master pipeline.

        Every feature in the project starts here.
        """

        print("Building feature store...")

        feature_store = self.build_player_features()

        print(f"Built {len(feature_store):,} player seasons.")

        return feature_store
    
    def clean_numeric_features(self, features):
        features = features.copy()

        numeric = features.select_dtypes(include="number").columns

        features[numeric] = (
            features[numeric]
            .replace([float('inf'), float("-inf")], 0)
            .fillna(0)
        )

        return features
    
    def add_percentile_scores(self, features):
        features = features.copy()

        features["opportunity_score"] = (
            features
            .groupby(["season", "position"])["opportunities_per_game"]
            .rank(pct=True)
            * 100
        )

        features["touch_score"] = (
            features
            .groupby(["season", "position"])["touches_per_game"]
            .rank(pct=True)
            * 100
        )

        features["fantasy_score"] = (
            features
            .groupby(["season", "position"])["ppr_per_game"]
            .rank(pct=True)
            * 100
        )

        features["reliability_score"] = (
            features
            .groupby(["season", "position"])["consistency_score"]
            .rank(pct=True)
            * 100
        )

        features["boom_score"] = (
            features
            .groupby(["season", "position"])["boom_games"]
            .rank(pct=True)
            * 100
        )

        features["bust_score"] = (
            100
            - (
                features
                .groupby(["season", "position"])["bust_games"]
                .rank(pct=True)
                * 100
            )
        )

        features["overall_player_score"] = (
            features["opportunity_score"] * 0.30
            + features["fantasy_score"] * 0.30
            + features["reliability_score"] * 0.20
            + features["boom_score"] * 0.10
            + features["bust_score"] * 0.10
        )

        return features

    
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
            "attempts",
            "completions",
            "passing_air_yards",
            "passing_tds",
            "passing_interceptions",
            "rushing_yards",
            "carries",
            "rushing_tds",
            "targets",
            "receptions",
            "receiving_air_yards",
            "receiving_yards_after_catch",
            "receiving_first_downs",
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
        team_features = self.build_team_features()

        features = features.merge(
            team_features,
            on=["season", "team"],
            how="left",
        )

        team_opportunity = self.build_team_opportunity_table()

        features = features.merge(
            team_opportunity[
                [
                    "season",
                    "team",
                    "returning_targets",
                    "returning_carries",
                    "returning_attempts",
                    "vacated_targets",
                    "vacated_carries",
                    "vacated_attempts",
                    "vacated_target_pct",
                    "vacated_carry_pct",
                    "vacated_pass_pct",
                ]
            ],
            on=["season", "team"],
            how="left"
        )

        features = self.add_player_shares(features)
        features = self.add_percentile_scores(features)

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
            "attempts",
            "completions",
            "passing_air_yards",
            "passing_tds",
            "passing_interceptions",
            "rushing_yards",
            "carries",
            "rushing_tds",
            "targets",
            "receptions",
            "receiving_air_yards",
            "receiving_yards_after_catch",
            "receiving_first_downs",
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

        features["carries_per_game"] = (
            features["carries"] / features["games"]
        )

        features["targets_per_game"] = (
            features["targets"] / features["games"]
        )

        features["attempts_per_game"] = (
            features["attempts"] / features["games"]
        )

        features["receptions_per_game"] = (
            features["receptions"] / features["games"]
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

        features["completion_pct"] = (
            features["completions"] / features["attempts"]
        )

        features["yards_per_attempt"] = (
            features["passing_yards"] / features["attempts"]
        )

        features["td_rate"] = (
            features["passing_tds"] / features["attempts"]
        )

        features["int_rate"] = (
            features["passing_interceptions"] / features["attempts"]
        )

        features["yards_per_carry"] = (
            features["rushing_yards"] / features["carries"]
        )

        features["catch_rate"] = (
            features["receptions"] / features["targets"]
        )

        features["yards_per_target"] = (
            features["receiving_yards"] / features["targets"]
        )

        features["yards_per_reception"] = (
            features["receiving_yards"] / features["receptions"]
        )

        features["yac_per_reception"] = (
            features["receiving_yards_after_catch"] /
            features["receptions"]
        )

        features["air_yards_per_target"] = (
            features["receiving_air_yards"] /
            features["targets"]
        )

        features["tds_per_game"] = (
            features["total_tds"] /
            features["games"]
        )

        features["first_downs_per_game"] = (
            features["receiving_first_downs"] /
            features["games"]
        )

        features = self.clean_numeric_features(features)

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
    
    def build_team_features(self):

        weekly = self.clean_weekly()
        regular_season = weekly[weekly["season_type"] == "REG"].copy()

        team_features = (
            regular_season
            .groupby(["season", "team"], as_index=False)
            .agg(
                team_pass_attempts=("attempts", "sum"),
                team_carries=("carries", "sum"),
                team_targets=("targets", "sum"),
                team_ppr=("fantasy_points_ppr", "sum"),
            )
        )

        team_features["team_total_opportunities"] = (
            team_features["team_carries"]
            + team_features["team_targets"]
        )

        team_features["team_pass_rate"] = (
            team_features["team_pass_attempts"]
            / (
                team_features["team_pass_attempts"]
                + team_features["team_carries"]
            )
        )

        return team_features
    
    def add_player_shares(self, features):

        features = features.copy()

        features["target_share"] = (
            features["targets"] / features["team_targets"]
        )

        features["rush_share"] = (
            features["carries"] / features["team_carries"]
        )

        features["opportunity_share"] = (
            features["opportunities"] / features["team_total_opportunities"]
        )

        features = self.clean_numeric_features(features)
        
        return features

    def build_team_opportunity_table(self):

        team = (
            self.weekly
            .groupby(["season", "team"])
            .agg(
                team_pass_attempts=("attempts","sum"),
                team_carries=("carries", "sum"),
                team_targets=("targets", "sum"),
            )
            .reset_index()
        )

        if self.current_rosters is not None:
            current_rosters = self.current_rosters[
                ["gsis_id", "team"]
            ].copy()
        else:
            current_rosters = (
                self.rosters
                .sort_values("season")
                .groupby("gsis_id", as_index=False)
                .tail(1)
                [["gsis_id", "team"]]
            )

        current_rosters = current_rosters.rename(
            columns={
                "gsis_id": "player_id",
                "team": "current_team",
            }
        )

        history = (
            self.weekly
            .groupby(
                ["season", "team", "player_id", "player_display_name"],
                as_index=False
            )
            .agg(
                targets=("targets", "sum"),
                carries=("carries", "sum"),
                attempts=("attempts", "sum"),
            )
        )    

        history = history.merge(
            current_rosters,
            on="player_id",
            how="left",
        )

        history["is_returning"] = (
            history["team"] == history["current_team"]
        )

        returning = (
            history[history["is_returning"]]
            .groupby(["season", "team"], as_index=False)
            .agg(
                returning_targets=("targets", "sum"),
                returning_carries=("carries", "sum"),
                returning_attempts=("attempts", "sum"),
            )
        )

        team = team.merge(
            returning,
            on=["season", "team"],
            how="left"
        )

        team = team.fillna(0)

        team["vacated_targets"] = (
            team["team_targets"] - team["returning_targets"]
        )

        team["vacated_carries"] = (
            team["team_carries"] - team["returning_carries"]
        )

        team["vacated_attempts"] = (
            team["team_pass_attempts"] - team["returning_attempts"]
        )

        team["vacated_target_pct"] = (
            team["vacated_targets"] / team["team_targets"]
        )

        team["vacated_carry_pct"] = (
            team["vacated_carries"] / team["team_carries"]
        )

        team["vacated_pass_pct"] = (
            team["vacated_attempts"] / team["team_pass_attempts"]
        )

        team = self.clean_numeric_features(team)

        return team
    
