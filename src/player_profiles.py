class PlayerProfile:

    def __init__(self, player_row):
        self.player = player_row

    def format_number(self, value, decimals=1):
        if value is None:
            return "N/A"
        
        try:
            if value != value:
                return "N/A"
            
            return f"{value:.{decimals}f}"
        
        except Exception:
            return str(value)

    def format_card(self):
        name = self.player["player_display_name"]
        position = self.player["position"]
        team = self.player["team"]
        season = self.player["season"]

        age = self.player.get("age", None)
        height = self.player.get("height", None)
        weight = self.player.get("weight", None)
        college = self.player.get("college", None)
        draft_number = self.player.get("draft_number", None)
        years_exp = self.player.get("years_exp", None)

        ppr_pg = self.player["ppr_per_game"]
        position = self.player["position"]

        if position == "QB":
            if ppr_pg >= 22:
                tier = "Elite QB1"
            elif ppr_pg >= 18:
                tier = "Strong QB1"
            elif ppr_pg >= 15:
                tier = "Streamer / QB2"
            else:
                tier = "Depth QB"

        elif position == "RB":
            if ppr_pg >= 20:
                tier = "Elite RB1"
            elif ppr_pg >= 16:
                tier = "Strong RB1/RB2"
            elif ppr_pg >= 12:
                tier = "Flex / RB2"
            else:
                tier = "Depth RB"

        elif position == "WR":
            if ppr_pg >= 20:
                tier = "Elite WR1"
            elif ppr_pg >= 16:
                tier = "Strong WR1/WR2"
            elif ppr_pg >= 12:
                tier = "Flex / WR3"
            else:
                tier = "Depth WR"

        elif position == "TE":
            if ppr_pg >= 16:
                tier = "Elite TE"
            elif ppr_pg >= 12:
                tier = "Starter TE"
            else:
                tier = "Depth TE"

        else:
            tier = "Unclassified"

        card = f"""
══════════════════════════════════════════════

{name}
{team}
{position}

{season} Profile
────────────────────────────

Age..................{self.format_number(age, 1)}
Height...............{self.format_number(height, 0)}
Weight...............{self.format_number(weight, 0)}
College..............{college}
Years Exp............{self.format_number(years_exp, 0)}
Draft Pick...........{self.format_number(draft_number, 0)}

Games................{self.player["games"]}

Carries/Game.........{self.player["carries"] / self.player["games"]:.1f}
Targets/Game.........{self.player["targets"] / self.player["games"]:.1f}
Touches/Game.........{self.player["touches_per_game"]:.1f}
Opps/Game............{self.player["opportunities_per_game"]:.1f}

Rush Yards/Game......{self.player["rushing_yards"] / self.player["games"]:.1f}
Rec Yards/Game.......{self.player["receiving_yards"] / self.player["games"]:.1f}

PPR Points...........{self.player["fantasy_points_ppr"]:.1f}
PPR/Game.............{self.player["ppr_per_game"]:.1f}

Boom Games...........{self.player["boom_games"]}
Solid Games..........{self.player["solid_games"]}
Bust Games...........{self.player["bust_games"]}

Consistency..........{self.player["consistency_score"]:.0%}

Fantasy Tier.........{tier}

Opportunity Score....{self.player["opportunity_score"]:.1f}
Fantasy Score........{self.player["fantasy_score"]:.1f}
Reliability Score....{self.player["reliability_score"]:.1f}
Overall Score........{self.player["overall_player_score"]:.1f}

PPR/Opp..............{self.player["ppr_per_opportunity"]:.2f}

══════════════════════════════════════════════
"""
        return card