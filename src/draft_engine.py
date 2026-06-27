import pandas as pd

class DraftEngine:

    def __init__(self, draft_board, league_settings):
        self.board = draft_board.copy()
        self.league_setting = league_settings

    def build_board(self):

        board = self.board.copy()

        board = board.sort_values(
            "draft_value_score",
            ascending=False,
        )

        board["overall_rank"] = range(1, len(board) + 1)

        board["available"] = True

        board["drafted_by"] = None

        return board
    
    def draft_player(self, board, player_name, manager):

        board = board.copy()

        mask = (
            board["player_display_name"]
            == player_name
        )

        board.loc[mask, "available"] = False
        board.loc[mask, "drafted_by"] = manager

        return board
    
    def best_available(self, board, n=10):
    
        available = (
            board[board["available"]]
            .sort_values("draft_value_score", ascending=False)
            .copy()
        )
    
        available["available_rank"] = range(1, len(available) + 1)
    
        return available.head(n)
