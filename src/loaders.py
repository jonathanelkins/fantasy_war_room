import nflreadpy as nfl
import pandas as pd

class NFLDataLoader:

    def __init__(self, seasons):
        self.seasons = seasons
    
    def load_weekly(self):
        weekly = nfl.load_player_stats(self.seasons)
        weekly = weekly.to_pandas()
        return weekly
    