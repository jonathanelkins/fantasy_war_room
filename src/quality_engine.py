import pandas as pd


class QualityEngine:

    def __init__(self, features):
        self.features = features.copy()

    def build(self):
        quality = self.features.copy()

        quality = self.add_base_quality_score(quality)
        player_quality = self.build_player_quality_table(quality)

        return quality, player_quality
    
    def add_base_quality_score(slef, quality):
        quality = quality.copy()

        if "ppr_per_game" in quality.columns:
            score_col = "ppr_per_game"
        elif "fantasy_points_ppr_per_game" in quality.columns:
            score_col = "fantasy_points_ppr_per_game"
        elif "fantasy_points_ppr" in quality.columns and "games" in quality.columns:
            quality["fantasy_points_ppr_per_game"] = (
                quality["fantasy_points_ppr"] / quality["games"].replace(0, pd.NA)
            )
            score_col = "fantasy_points_ppr_per_game"
        else:
            quality["quality_score"] = 50.0
            return quality
        
        quality["raw_quality_score"] = quality[score_col].fillna(0)

        quality["quality_score"] = (
            quality
            .groupby("position")["raw_quality_score"]
            .rank(pct=True)
            * 100
        )

        quality["quality_score"] = quality["quality_score"].fillna(50)

        return quality
    
    def build_player_quality_table(self, quality):

        latest_quality = (
            quality
            .sort_values("season")
            .groupby("player_id", as_index=False)
            .tail(1)
            [
                [
                    "player_id",
                    "quality_score",
                ]
            ]
        )

        return latest_quality
    

