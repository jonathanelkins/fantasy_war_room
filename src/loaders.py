import nflreadpy as nfl
import pandas as pd

class NFLDataLoader:

    def __init__(self, seasons):
        self.seasons = seasons
    
    def load_weekly(self):
        weekly = nfl.load_player_stats(self.seasons)
        return weekly.to_pandas()
    
    def load_rosters(self):
        rosters = nfl.load_rosters(self.seasons)
        return rosters.to_pandas()
    
    def load_schedules(self):
        schedules = nfl.load_schedules(self.seasons)
        return schedules.to_pandas()
   
    