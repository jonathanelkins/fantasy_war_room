import pandas as pd


class RoleEngine:

    def __init__(self, projections):
        self.projections = projections.copy()

    def build(self):
        roles = self.projections.copy()

        roles = self.add_role_scores(roles)
        roles = self.add_position_depth_ranks(roles)
        roles = self.add_role_labels(roles)
        roles = self.apply_qb_opportunity_shares(roles)

        return roles
    
    def add_role_scores(self, roles):
        roles = roles.copy()

        roles["role_score"] = (
            roles["projected_targets"].fillna(0)
            + roles["projected_carries"].fillna(0)
            + roles["projected_pass_attempts"].fillna(0)
        )

        return roles
    
    def add_position_depth_ranks(self, roles):
        roles = roles.copy()

        roles["team_position_rank"] = (
            roles
            .groupby(["team", "position"])["role_score"]
            .rank(method="first", ascending=False)
            .astype(int)
        )

        return roles
    
    def add_role_labels(self, roles):
        roles = roles.copy()

        roles["role_label"] = roles["position"] + roles["team_position_rank"].astype(str)

        roles.loc[
            roles["projection_active"] == False,
            "role_label"
        ] = "Inactive"

        return roles
    
    def apply_qb_opportunity_shares(self, roles):

        roles = roles.copy()

        qb_mask = roles["position"] == "QB"

        roles.loc[qb_mask, "qb_pass_attempt_share"] = 0.0

        roles.loc[
            qb_mask & (roles["team_position_rank"] == 1),
            "qb_pass_attempt_share"
        ] = 0.98

        roles.loc[
            qb_mask & (roles["team_position_rank"] == 2),
            "qb_pass_attempt_share"
        ] = 0.02

        roles.loc[
            qb_mask & (roles["team_position_rank"] == 3),
            "qb_pass_attempt_share"
        ] = 0.00

        return roles
    
