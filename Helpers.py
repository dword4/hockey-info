
import requests
import requests_cache
import json
import arrow

class Helpers(object):
    # games-to-date 
    def games_to_date(self):
        today = arrow.utcnow().format('YYYY-MM-DD')
        url = 'https://statsapi.web.nhl.com/api/v1/seasons/current'

        data = requests.get(url).json()

        seasonStart = data['seasons'][0]['regularSeasonStartDate']

        url = 'https://statsapi.web.nhl.com/api/v1/schedule?startDate='+seasonStart+'&endDate='+today

        games_data = requests.get(url).json()

        previous_games = []

        for date in games_data['dates']:
            print(date['date'])
            games = date['games']
            for game in games:
                gameDate = date['date']
                gamePk = game['gamePk']
                gameStatus = int(game['status']['statusCode'])
                gameState = game['status']['abstractGameState']
                # away team
                if gameStatus >= 3 and gameStatus <= 7:
                    away_team_score = game['teams']['away']['score']
                else:
                    away_team_score = ""
                away_team_id = game['teams']['away']['team']['id']
                away_team_name = game['teams']['away']['team']['name']
                
            
                if gameStatus >= 3 and gameStatus <= 7:
                    home_team_score = game['teams']['home']['score']
                else:
                    home_team_score = ""
                home_team_id = game['teams']['home']['team']['id']
                home_team_name = game['teams']['home']['team']['name']

                # build data to return
                data = {
                    'gamePk':gamePk,
					'gameDate': gameDate,
                    'gameState': gameState,
                    'home_team_id':home_team_id,
                    'home_team_name':home_team_name,
                    'home_team_score':home_team_score,
					'home_team_abbr': self.get_team_abbr(home_team_id),
                    'away_team_id':away_team_id,
                    'away_team_name':away_team_name,
                    'away_team_score':away_team_score,
					'away_team_abbr': self.get_team_abbr(away_team_id)
                    }
                previous_games.append(data)
            d = { 'gamePk': 'none' }
            previous_games.append(d) 
        return previous_games
    # converts team_id value to franchise_id used by some endpoints
    def team_to_franchise(self, team_id):
        url = 'https://statsapi.web.nhl.com/api/v1/teams/'+str(team_id)+'?expand=team.franchise'
        team_data = requests.get(url).json()
        franchise_id = team_data['teams'][0]['franchise']['franchiseId']
        return franchise_id

    # returns current season id
    def get_current_season(self):
        api_resource = 'https://statsapi.web.nhl.com/api/v1/seasons'
        data = requests.get(api_resource).json()
        current_id = len(data['seasons']) - 1
        current_season_id = data['seasons'][current_id]['seasonId']
        return current_season_id
    
    # get all teams
    def get_all_teams(self):
        teams = {
                "NJD" : 1,
                "NYI" : 2,
                "NYR" : 3,
                "PHI" : 4,
                "PIT" : 5,
                "BOS" : 6,
                "BUF" : 7,
                "MTL" : 8,
                "OTT" : 9,
                "TOR" : 10,
                "CAR" : 12,
                "FLA" : 13,
                "TBL" : 14,
                "WSH" : 15,
                "CHI" : 16,
                "DET" : 17,
                "NSH" : 18,
                "STL" : 19,
                "CGY" : 20,
                "COL" : 21,
                "EDM" : 22,
                "VAN" : 23,
                "ANA" : 24,
                "DAL" : 25,
                "LAK" : 26,
                "SJS" : 28,
                "CBJ" : 29,
                "MIN" : 30,
                "WPG" : 52,
                "ARI" : 53,
                "VGK" : 54
                }
        return teams 
    # get team abbreviation from ID
    def get_team_abbr(self,ID):
        ret = False
        teams = {
                "NJD" : 1,
                "NYI" : 2,
                "NYR" : 3,
                "PHI" : 4,
                "PIT" : 5,
                "BOS" : 6,
                "BUF" : 7,
                "MTL" : 8,
                "OTT" : 9,
                "TOR" : 10,
                "CAR" : 12,
                "FLA" : 13,
                "TBL" : 14,
                "WSH" : 15,
                "CHI" : 16,
                "DET" : 17,
                "NSH" : 18,
                "STL" : 19,
                "CGY" : 20,
                "COL" : 21,
                "EDM" : 22,
                "VAN" : 23,
                "ANA" : 24,
                "DAL" : 25,
                "LAK" : 26,
                "SJS" : 28,
                "CBJ" : 29,
                "MIN" : 30,
                "WPG" : 52,
                "ARI" : 53,
                "VGK" : 54
                }
        for team, teamId in teams.items():
            if teamId == ID:
                ret = team
        if ret == False:
            sub_req = "https://statsapi.web.nhl.com/api/v1/teams/"+str(ID)
            sub_r = requests.get(sub_req)
            team_json = sub_r.text
            team_data = json.loads(team_json)
            ret = team_data['teams'][0]['abbreviation']
        return ret
