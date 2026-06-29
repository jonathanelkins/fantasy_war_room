import pandas as pd


class OpportunityEngine:

    def __init__(self, projections, team_opportunity):
        self.projections = projections.copy()
        self.team_opportunity = team_opportunity.copy()

    def build(self):
        opportunities = self.projections.copy()

        opportunities = self.allocate_qb_opportunity(opportunities)
        opportunities = self.build_target_weights(opportunities)
        opportunities = self.merge_team_opportunity(opportunities)
        opportunities = self.adjust_target_weights(opportunities)
        opportunities = self.normalize_target_weights(opportunities)
        opportunities = self.allocate_target_opportunity(opportunities)
        opportunities = self.allocate_rushing_opportunity(opportunities)

        return opportunities
    
    def allocate_qb_opportunity(self, opportunities):
        opportunities = opportunities.copy()

        qb_mask = opportunities["position"] == "QB"

        if "qb_pass_attempt_share" not in opportunities.columns:
            opportunities["qb_pass_attempt_share"] = 0.0

        opportunities.loc[qb_mask, "projected_pass_attempts"] = (
            opportunities.loc[qb_mask, "team_pass_attempts"]
            * opportunities.loc[qb_mask, "qb_pass_attempt_share"]
        )

        return opportunities
    
    def allocate_target_opportunity(self, opportunities):
        opportunities = opportunities.copy()

        eligible_mask = (
            opportunities["projection_active"]
            & opportunities["position"].isin(["RB", "WR", "TE"])
        )

        opportunities.loc[eligible_mask, "projected_targets"] = (
            opportunities.loc[eligible_mask, "projected_team_targets"]
            * opportunities.loc[eligible_mask, "normalized_target_weight"]
        )

        opportunities.loc[~eligible_mask, "projected_targets"] = 0.0

        return opportunities
    
    def allocate_rushing_opportunity(self, opportunities):
        opportunities = opportunities.copy()
        return opportunities
    
    def build_target_weights(self, opportunities):

        opportunities = opportunities.copy()

        opportunities["base_target_weight"] = 0.0
        opportunities["adjusted_target_weight"] = 0.0
        opportunities["normalized_target_weight"] = 0.0

        eligible_mask = (
            opportunities["projection_active"]
            & opportunities["position"].isin(["RB", "WR", "TE"])
        )

        opportunities.loc[eligible_mask, "base_target_weight"] = (
            opportunities.loc[eligible_mask, "target_share"]
            .fillna(0)
        )

        opportunities.loc[eligible_mask, "adjusted_target_weight"] = (
            opportunities.loc[eligible_mask, "base_target_weight"]
        )

        return opportunities
    
    def merge_team_opportunity(self, opportunities):

        opportunities = opportunities.copy()

        drop_cols = [
            "vacated_targets",
            "vacated_target_pct",
            "vacated_targets_x",
            "vacated_targets_y",
            "vacated_target_pct_x",
            "vacated_target_pct_y",
        ]

        opportunities = opportunities.drop(
            columns=[col for col in drop_cols if col in opportunities.columns]
        )

        latest = (
            self.team_opportunity
            .sort_values("season")
            .groupby("team", as_index=False)
            .tail(1)
        )

        opportunities = opportunities.merge(
            latest[
                [
                    "team",
                    "vacated_targets",
                    "vacated_target_pct",
                ]
            ],
            on="team",
            how="left",
        )

        opportunities["vacated_targets"] = (
            opportunities["vacated_targets"]
            .fillna(0)
        )

        opportunities["vacated_target_pct"] = (
            opportunities["vacated_target_pct"]
            .fillna(0)
        )

        return opportunities
    
    def adjust_target_weights(self, opportunities):

        opportunities = opportunities.copy()

        if "changed_teams" not in opportunities.columns:
            opportunities["changed_teams"] = False

        mask = (
            opportunities["changed_teams"]
            & opportunities["projection_active"]
            & opportunities["position"].isin(["RB", "WR", "TE"])
        )

        opportunities.loc[mask, "adjusted_target_weight"] = (
            opportunities.loc[mask, "adjusted_target_weight"]
            * (
                1
                + opportunities.loc[mask, "vacated_target_pct"]
                * 0.35
            )
        )

        opportunities["quality_multiplier"] = (
            0.85
            + (
                opportunities["quality_score"].fillna(50) / 100
            ) * 0.30
        )

        eligible = (
            opportunities["projection_active"]
            & opportunities["position"].isin(["RB", "WR", "TE"])
        )

        opportunities.loc[eligible, "adjusted_target_weight"] = (
            opportunities.loc[eligible, "adjusted_target_weight"]
            * opportunities.loc[eligible, "quality_multiplier"]
        )

        return opportunities
    
    def normalize_target_weights(self, opportunities):

        opportunities = opportunities.copy()

        eligible = (
            opportunities["projection_active"]
            & opportunities["position"].isin(["RB", "WR", "TE"])
        )

        totals = (
            opportunities.loc[eligible]
            .groupby("team")["adjusted_target_weight"]
            .transform("sum")
        )

        opportunities["normalized_target_weight"] = 0.0

        opportunities.loc[eligible, "normalized_target_weight"] = (
            opportunities.loc[eligible, "adjusted_target_weight"]
            / totals
        )

        opportunities["normalized_target_weight"] = (
            opportunities["normalized_target_weight"]
            .fillna(0)
        )

        return opportunities


