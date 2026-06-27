import pandas as pd


class ValueEngine:

    def __init__(self, feature_store, league_settings):
        self.features = feature_store.copy()
        self.league_settings = league_settings

    def get_replacement_ranks(self):
        teams = self.league_settings["teams"]

        qb_rank = teams * self.league_settings["qb"]
        rb_rank = teams * self.league_settings["rb"]
        wr_rank = teams * self.league_settings["wr"]
        te_rank = teams * self.league_settings["te"]

        flex_spots = teams * self.league_settings["flex"]

        rb_rank += flex_spots // 2
        wr_rank += flex_spots // 2

        return {
            "QB": qb_rank,
            "RB": rb_rank,
            "WR": wr_rank,
            "TE": te_rank,
        }
    
    def get_replacement_values(self):
        replacement_ranks = self.get_replacement_ranks()

        values = {}

        for position, replacement_rank in replacement_ranks.items():
            position_players = (
                self.features[self.features["position"] == position]
                .sort_values("projected_ppr_per_game", ascending=False)
                .copy()
            )

            replacement_player = position_players.iloc[replacement_rank - 1]

            values[position] = replacement_player["projected_ppr_per_game"]

        return values
    
    def calculate_war(self):
        features = self.features.copy()

        replacement_values = self.get_replacement_values()

        features["replacement_ppg"] = features["position"].map(replacement_values)

        features["fantasy_war"] = (
            features["projected_ppr_per_game"] - features["replacement_ppg"]
        )

        features["fantasy_war"] = features["fantasy_war"].clip(lower=0)

        features["war_rank"] = (
            features["fantasy_war"]
            .rank(method="dense", ascending=False)
            .astype(int)
        )

        features["position_rank"] = (
            features
            .groupby("position")["fantasy_war"]
            .rank(method="dense", ascending=False)
            .astype(int)
        )

        features = self.add_value_tiers(features)

        features["draft_value_score"] = (
            features["projected_ppr_per_game"] * 0.5
            + features["fantasy_war"] * 5
        )

        return features
    
    def add_value_tiers(self, features):
    
        features = features.copy()
    
        features["value_tier"] = "Bench"
    
        features.loc[features["fantasy_war"] >= 1, "value_tier"] = "Depth"
        features.loc[features["fantasy_war"] >= 3, "value_tier"] = "Starter"
        features.loc[features["fantasy_war"] >= 5, "value_tier"] = "Difference Maker"
        features.loc[features["fantasy_war"] >= 7, "value_tier"] = "Elite"
        features.loc[features["fantasy_war"] >= 10, "value_tier"] = "League Winner"
    
        return features
    

    





