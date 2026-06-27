import pandas as pd


class ProjectionEngine:

    """
    Builds next-season fantasy football projections.

    The projection pipeline is intentionally broken into stages.
    Each stage modifies the projection table before passing it
    to the next stage.
    """

    def __init__(self, features, league_settings):

        self.features = features.copy()
        self.league_settings = league_settings
        self.scoring = league_settings["scoring"]

    def weighted_average(
            self,
            history,
            column,
            weights=None
    ):
        """
        Calculates a weighted average across seasons.

        Most recent season receives the highest weight.
        """

        if weights is None:
            weights = [5, 3, 2]

        history = (
            history
            .sort_values("season", ascending=False)
        )

        history = history.dropna(subset=[column])

        values = history[column].head(len(weights)).tolist()

        if len(values) == 0:
            return 0
        
        weights = weights[:len(values)]

        numerator = sum(
            value * weight
            for value, weight in zip(values, weights)
        )

        denominator = sum(weights)

        return numerator / denominator

    def build(self):

        projections = self.initialize_projection_table()

        projections = self.project_games(projections)

        projections = self.project_volume(projections)

        projections = self.project_efficiency(projections)

        projections = self.project_touchdowns(projections)

        projections = self.apply_age_curve(projections)

        projections = self.apply_team_adjustments(projections)

        projections = self.apply_regression(projections)

        projections = self.calculate_fantasy_points(projections)

        projections = self.clean_projection_stats(projections)

        return projections
    
    def initialize_projection_table(self):

        features = self.features.copy()

        latest_season = features["season"].max()

        latest_players = features[
            features["season"] == latest_season
        ].copy()

        return latest_players
    
    def project_games(self, projections):

        projections = projections.copy()

        projections["projected_games"] = 16

        qb_mask = projections["position"] == "QB"

        projections.loc[qb_mask, "projected_games"] = 17

        return projections
    
    def project_volume(self, projections):

        projections = self.project_qb_volume(projections)
        projections = self.project_rb_volume(projections)
        projections = self.project_receiver_volume(projections)

        volume_columns = [
            "projected_pass_attempts",
            "projected_carries",
            "projected_targets",
        ]

        projections[volume_columns] = projections[volume_columns].fillna(0)

        projections = self.add_weighted_recency_volume(projections)

        return projections
    
    def project_qb_volume(self, projections):

        projections = projections.copy()

        qb_mask = projections["position"] == "QB"

        projections.loc[qb_mask, "projected_pass_attempts"] = (
            projections.loc[qb_mask, "attempts"]
        )

        return projections
    
    def project_rb_volume(self, projections):

        projections = projections.copy()

        rb_mask = projections["position"] == "RB"

        projections.loc[rb_mask, "projected_carries"] = (
            projections.loc[rb_mask, "carries"]
        )

        projections.loc[rb_mask, "projected_targets"] = (
            projections.loc[rb_mask, "targets"]
        )

        return projections
    
    def project_receiver_volume(self, projections):

        projections = projections.copy()

        receiver_mask = projections["position"].isin(["WR", "TE"])

        projections.loc[receiver_mask, "projected_targets"] = (
            projections.loc[receiver_mask, "targets"]
        )

        return projections
    
    def add_weighted_recency_volume(self, projections):
    
        projections = projections.copy()
        history = self.features.copy()
    
        for idx, row in projections.iterrows():
        
            player_history = history[
                history["player_id"] == row["player_id"]
            ]
    
            projections.loc[idx, "projected_pass_attempts_per_game"] = (
                self.weighted_average(player_history, "attempts_per_game")
            )
    
            projections.loc[idx, "projected_carries_per_game"] = (
                self.weighted_average(player_history, "carries_per_game")
            )
    
            projections.loc[idx, "projected_targets_per_game"] = (
                self.weighted_average(player_history, "targets_per_game")
            )
    
        projections["projected_pass_attempts"] = (
            projections["projected_pass_attempts_per_game"]
            * projections["projected_games"]
        )
    
        projections["projected_carries"] = (
            projections["projected_carries_per_game"]
            * projections["projected_games"]
        )
    
        projections["projected_targets"] = (
            projections["projected_targets_per_game"]
            * projections["projected_games"]
        )
    
        return projections

    def project_efficiency(self, projections):

        projections = projections.copy()
        history = self.features.copy()

        for idx, row in projections.iterrows():

            player_history = history[
                history["player_id"] == row["player_id"]
            ]

            projections.loc[idx, "projected_completion_pct"] = (
                self.weighted_average(player_history, "completion_pct")
            )

            projections.loc[idx, "projected_yards_per_attempt"] = (
                self.weighted_average(player_history, "yards_per_attempt")
            )

            projections.loc[idx, "projected_yards_per_carry"] = (
                self.weighted_average(player_history, "yards_per_carry")
            )

            projections.loc[idx, "projected_catch_rate"] = (
                self.weighted_average(player_history, "catch_rate")
            )

            projections.loc[idx, "projected_yards_per_target"] = (
                self.weighted_average(player_history, "yards_per_target")
            )

        return projections
    
    def project_touchdowns(self, projections):
    
        projections = projections.copy()
        history = self.features.copy()
    
        for idx, row in projections.iterrows():
        
            player_history = history[
                history["player_id"] == row["player_id"]
            ]
    
            projections.loc[idx, "projected_passing_td_rate"] = (
                self.weighted_average(player_history, "td_rate")
            )
    
            projections.loc[idx, "projected_rushing_td_per_carry"] = (
                self.weighted_average(player_history, "rushing_tds") /
                max(self.weighted_average(player_history, "carries"), 1)
            )
    
            projections.loc[idx, "projected_receiving_td_per_target"] = (
                self.weighted_average(player_history, "receiving_tds") /
                max(self.weighted_average(player_history, "targets"), 1)
            )
    
        projections["projected_passing_tds"] = (
            projections["projected_pass_attempts"]
            * projections["projected_passing_td_rate"]
        )
    
        projections["projected_rushing_tds"] = (
            projections["projected_carries"]
            * projections["projected_rushing_td_per_carry"]
        )
    
        projections["projected_receiving_tds"] = (
            projections["projected_targets"]
            * projections["projected_receiving_td_per_target"]
        )
    
        return projections
    
    def apply_age_curve(self, projections):

        return projections
    
    def apply_team_adjustments(self, projections):

        return projections
    
    def apply_regression(self, projections):

        return projections
    
    def calculate_fantasy_points(self, projections):

        scoring = self.scoring

        projections = projections.copy()

        projections["projected_completions"] = (
            projections["projected_pass_attempts"]
            * projections["projected_completion_pct"]
        )

        projections["projected_passing_yards"] = (
            projections["projected_pass_attempts"]
            * projections["projected_yards_per_attempt"]
        )

        projections["projected_rushing_yards"] = (
            projections["projected_carries"]
            * projections["projected_yards_per_carry"]
        )

        projections["projected_receptions"] = (
            projections["projected_targets"] 
            * projections["projected_catch_rate"]
        )

        projections["projected_receiving_yards"] = (
            projections["projected_targets"]
            * projections["projected_yards_per_target"]
        )

        projections["projected_fantasy_points_ppr"] = (
            projections["projected_passing_yards"] * scoring["passing_yard"]
            + projections["projected_passing_tds"] * scoring["passing_td"]
            + projections["projected_rushing_yards"] * scoring["rushing_yard"]
            + projections["projected_rushing_tds"] * scoring["rushing_td"]
            + projections["projected_receptions"] * scoring["reception"]
            + projections["projected_receiving_yards"] * scoring["receiving_yard"]
            + projections["projected_receiving_tds"] * scoring["receiving_td"]
        )

        projections["projected_ppr_per_game"] = (
            projections["projected_fantasy_points_ppr"]
            / projections["projected_games"]
        )

        return projections
    
    def clean_projection_stats(self, projections):

        projections = projections.copy()

        qb_mask = projections["position"] == "QB"
        rb_mask = projections["position"] == "RB"
        receiver_mask = projections["position"].isin(["WR", "TE"])

        projections.loc[~qb_mask, [
            "projected_pass_attempts",
            "projected_completions",
            "projected_passing_yards"
        ]] == 0

        projections.loc[~rb_mask, [
            "projected_carries",
            "projected_rushing_yards",
        ]] = projections.loc[~rb_mask, [
            "projected_carries",
            "projected_rushing_yards"
        ]].clip(lower=0)

        projections.loc[~receiver_mask & ~rb_mask, [
            "projected_targets",
            "projected_receptions",
            "projected_receiving_yards",
        ]] = 0

        numeric = projections.select_dtypes(include="number").columns

        projections[numeric] = (
            projections[numeric]
            .replace([float("inf"), float("-inf")], 0)
            .fillna(0)
        )

        non_qb_mask = projections["position"] != "QB"

        projections.loc[
            non_qb_mask,
            [
                "projected_pass_attempts",
                "projected_completions",
                "projected_passing_yards",
            ],
        ] = 0

        return projections


