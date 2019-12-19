
import requests
import requests_cache
import json
import arrow

class Helpers(object):

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
