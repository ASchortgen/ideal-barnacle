import numpy as np
import pandas as pd

from pydantic import BaseModel, Field
from typing import Union

from nba_api.stats.endpoints import teamgamelog, leaguegamelog, playergamelog, teamvsplayer
from nba_api.stats.static.players import get_active_players

from models import TeamName


class Player(BaseModel):
    name: str
    id: Union[int, None] = Field(None)

    def get_id(self):
        if not self.id:
            players = get_active_players()
            self.id = next(player["id"] for player in players if player["full_name"] == self.name)
        return self.id

    def get_season_games(self, season: str = "2025-26") -> pd.DataFrame:
        """
        This function returns the statistic for the player in the games he was listed as playing
        season: yyyy-yy ie 2025-26
        """
        data = playergamelog.PlayerGameLog(player_id=self.get_id(), season=season).get_data_frames()
        if data:
            return data[0]
        else:
            print(f"Player {self.name} did not play during season {season}")
    
    def get_ttfl_scores(self, season: str = "2025-26") -> pd.DataFrame:
        """
        This function calculates the TTFL score of the player for a given season
        """
        games_stats = self.get_season_games(season)

        if not games_stats.empty:
            games_stats['ttfl_score'] = games_stats.apply(lambda x: x['PTS'] + x['FGM'] - (x['FGA'] - x['FGM']) + x['STL'] + x['AST'] + x['BLK'] + x['REB'] - x['TOV'] + x['FTM'] - (x['FTA'] - x['FTM']) + x['FG3M'] - (x['FG3A'] - x['FG3M']), axis=1)
            games_stats[['team', 'opponent']] = games_stats.apply(lambda x: (x['MATCHUP'].split(' ')[0], x['MATCHUP'].split(' ')[2]), axis=1, result_type='expand')
            result = games_stats[['GAME_DATE', 'team', 'opponent', 'ttfl_score']]
        else:
            result = pd.DataFrame({'GAME_DATE':np.NaN, 'team':np.NaN, 'opponent':np.NaN, 'ttfl_score':np.NaN}, index=[0])
        return result
    
    def get_ttfl_stat_vs_team(self, team: str, season: str = "2025-26") -> tuple[float, pd.DataFrame]:
        """
        """
        ttfl_stats = self.get_ttfl_scores(season)
        if team in list(ttfl_stats['opponent']):
            vs_team = ttfl_stats[ttfl_stats['opponent'] == team]
            result = (vs_team["ttfl_score"].mean(), vs_team)
        else:
            print(f"No game played against {team}")
            result = (np.Nan, pd.DataFrame())
        return result

    def get_ttfl_averages(self, season: str = "2025-26"):
        ttfl_stats = self.get_ttfl_scores(season)
        temp = ttfl_stats.groupby('opponent').agg({'ttfl_score': 'mean', 'GAME_DATE': 'count'})
        return temp

player = Player(**{"name": "De'Aaron Fox"})
print(player.get_id())
print(player.get_ttfl_averages("2025-26"))