import pandas as pd


class ProjectionEngine:

    """
    Builds next-season fantasy football projections.

    The projection pipeline is intentionally broken into stages.
    Each stage modifies the projection table before passing it
    to the next stage.
    """

    def __init__(self, features, league_settings, current_rosters=None):

        self.features = features.copy()
        self.league_settings = league_settings
        self.scoring = league_settings["scoring"]
        self.current_rosters = current_rosters.copy() if current_rosters is not None else None

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

        projections = self.apply_current_rosters(projections)

        projections = self.apply_excluded_players(projections)

        projections = self.apply_current_team_context(projections)

        projections = self.project_games(projections)

        projections = self.project_volume(projections)

        projections = self.apply_roster_cutoffs(projections)

        projections = self.apply_projection_active_flag(projections)

        projections = self.normalize_team_targets(projections)

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
    
    def apply_current_rosters(self, projections):

        projections = projections.copy()

        if self.current_rosters is None:
            projections["historical_team"] = projections["team"]
            projections["changed_teams"] = False
            return projections
        
        roster_cols = [
            "gsis_id",
            "team",
            "position",
            "status",
            "depth_chart_position",
            "years_exp",
        ]

        current = self.current_rosters[roster_cols].copy()

        current = current.rename(
            columns={
                "gsis_id": "player_id",
                "team": "current_team",
                "position": "current_position",
            }
        )

        current = current.drop_duplicates(subset=["player_id"])

        projections = projections.merge(
            current,
            on="player_id",
            how="left",
        )

        print(
            projections[
                projections["player_display_name"] == "A.J. Brown"
            ][
                [
                    "season",
                    "team",
                    "current_team",
                ]
            ]
            .sort_values("season")
            .to_string(index=False)
        )

        projections["historical_team"] = projections["team"]

        projections["team"] = projections["current_team"].fillna(projections["team"])
        projections["position"] = projections["current_position"].fillna(projections["position"])

        projections["changed_teams"] = (
            projections["historical_team"] != projections["team"]
        )

        return projections

    def apply_current_team_context(self, projections):

        projections = projections.copy()

        team_context_cols = [
            "season",
            "team",
            "team_pass_attempts",
            "team_carries",
            "team_targets",
            "team_ppr",
            "team_total_opportunities",
            "team_pass_rate",
        ]

        team_context = (
            self.features[team_context_cols]
            .drop_duplicates(subset=["season", "team"])
            .copy()
        )

        latest_season = self.features["season"].max()

        latest_team_context = team_context[
            team_context["season"] == latest_season
        ].copy()

        latest_team_context = latest_team_context.drop(columns=["season"])

        latest_team_context = latest_team_context.rename(
            columns={
                "team": "current_team_for_context",
                "team_pass_attempts": "current_team_pass_attempts",
                "team_carries": "current_team_carries",
                "team_targets": "current_team_targets",
                "team_ppr": "current_team_ppr",
                "team_total_opportunities": "current_team_total_opportunities",
                "team_pass_rate": "current_team_pass_rate",
            }
        )

        projections = projections.merge(
            latest_team_context,
            left_on="team",
            right_on="current_team_for_context",
            how="left"
        )

        projections["team_pass_attempts"] = projections[
            "current_team_pass_attempts"
        ].fillna(projections["team_pass_attempts"])

        projections["team_carries"] = projections[
            "current_team_carries"
        ].fillna(projections["team_carries"])

        projections["team_targets"] = projections[
            "current_team_targets"
        ].fillna(projections["team_targets"])

        projections["team_ppr"] = projections[
            "current_team_ppr"
        ].fillna(projections["team_ppr"])

        projections["team_total_opportunities"] = projections[
            "current_team_total_opportunities"
        ].fillna(projections["team_total_opportunities"])

        projections["team_pass_rate"] = projections[
            "current_team_pass_rate"
        ].fillna(projections["team_pass_rate"])

        drop_cols = [
            "current_team_for_context",
            "current_team_pass_attempts",
            "current_team_carries",
            "current_team_targets",
            "current_team_ppr",
            "current_team_total_opportunities",
            "current_team_pass_rate",
        ]

        projections = projections.drop(columns=drop_cols)

        return projections
    
    def apply_excluded_players(self, projections):

        projections = projections.copy()

        try:
            excluded = pd.read_csv("data/manual/excluded_players.csv")
        except FileNotFoundError:
            return projections
        
        excluded_names = excluded["player_display_name"].tolist()

        projections = projections[
            ~projections["player_display_name"].isin(excluded_names)
        ].copy()

        return projections

    def normalize_team_targets(self, projections):

        projections = projections.copy()

        team_target_totals = (
            projections[projections["position"].isin(["RB", "WR", "TE"])]
            .groupby("team", as_index=False)
            .agg(
                projected_team_player_targets=("projected_targets", "sum"),
                projected_team_targets=("team_targets", "max"),
            )
        )

        team_target_totals["target_scale_factor"] = (
            team_target_totals["projected_team_targets"]
            / team_target_totals["projected_team_player_targets"]
        )

        team_target_totals["target_scale_factor"] = (
            team_target_totals["target_scale_factor"]
            .replace([float("inf"), float("-inf")], 1)
            .fillna(1)
            .clip(lower=0.60, upper=1.25)
        )

        projections = projections.merge(
            team_target_totals[
                [
                    "team",
                    "projected_team_player_targets",
                    "projected_team_targets",
                    "target_scale_factor",
                ]
            ],
            on="team",
            how="left"
        )

        projections["projected_targets"] = (
            projections["projected_targets"]
            * projections["target_scale_factor"]
        )

        return projections
    
    def apply_roster_cutoffs(self, projections):

        projections = projections.copy()

        roster_limits = {
            "QB": 2,
            "RB": 4,
            "WR": 5,
            "TE": 3,
        }

        projections["temporary_role_score"] = (
            projections["projected_pass_attempts"]
            + projections["projected_carries"] 
            + projections["projected_targets"]
        )

        projections["projection_roster_rank"] = (
            projections
            .groupby(["team", "position"])["temporary_role_score"]
            .rank(method="first", ascending=False)
        )

        for position, limit in roster_limits.items():

            mask = (
                (projections["position"] == position)
                & (projections["projection_roster_rank"] > limit)
            )

            projections.loc[
                mask,
                [
                    "projected_pass_attempts",
                    "projected_carries",
                    "projected_targets",
                ],
            ] = 0

        return projections
    
    def apply_projection_active_flag(self, projections):

        projections = projections.copy()

        projection_columns = [
            "projected_pass_attempts",
            "projected_carries",
            "projected_targets",
        ]

        projections["projection_active"] = (
            projections[projection_columns].sum(axis=1) > 0
        )

        return projections
    
    
