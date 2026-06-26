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
                .sort_values("ppr_per_game", ascending=False)
                .copy()
            )

            replacement_player = position_players.iloc[replacement_rank - 1]

            values[position] = replacement_player["ppr_per_game"]

        return values
    
    def calculate_war(self):
        features = self.features.copy()

        replacement_values = self.get_replacement_values()

        features["replacement_ppg"] = features["position"].map(replacement_values)

        features["fantasy_war"] = (
            features["ppr_per_game"] - features["replacement_ppg"]
        )

        features["fantasy_war"] = features["fantasy_war"].clip(lower=0)

        return features
    





