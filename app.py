from flask import Flask, render_template
import requests
import json
import arrow
app = Flask(__name__)
if __name__ == "__main__":
	app.run(host="0.0.0.0", port=int("5000"))
# get team abbreviation from ID
def getTeamAbbr(ID):
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

@app.route('/')
def hello_world():
	return render_template('index.html')

@app.route('/standings')
def get_standings():
	# first we gather the regular standings
	url = 'https://statsapi.web.nhl.com/api/v1/standings'
	records = requests.get(url).json()
	standings = []
	for r in records['records']:
		division_name = r['division']['name']
			
		for team in r['teamRecords']:
			team_name = team['team']['name']
			team_points = team['points']
			team_rank_division = team['divisionRank']
			team_rank_wildcard = team['wildCardRank']
			team_standings = {'team_name':team_name,'team_points':team_points,'team_rank_division':team_rank_division,'team_rank_wildcard':team_rank_wildcard,'division':division_name}
			standings.append(team_standings)
	# now to collect wildcard info
	url = 'https://statsapi.web.nhl.com/api/v1/standings/wildCard'
	records = requests.get(url).json()
	(eastern, western) = records['records']
	wc_teams = []
	for i in [0,1]:
		wc_teams.append(eastern['teamRecords'][i]['team']['name'])
		wc_teams.append(western['teamRecords'][i]['team']['name'])

	return render_template('standings.html',standings=standings,wc=wc_teams)

@app.route('/scores')
def get_scores():
	#scores = {'away_team':'FLA','away_score':'4','home_team':'TOR','home_score':'7'}

	url = 'https://statsapi.web.nhl.com/api/v1/schedule?expand=schedule.linescore'
	games = requests.get(url).json()
	game_data = [] 
	for g in games['dates'][0]['games']:
		away_team = getTeamAbbr(g['teams']['away']['team']['id'])
		home_team = getTeamAbbr(g['teams']['home']['team']['id'])
		away_score = g['teams']['away']['score']
		home_score = g['teams']['home']['score']
		game_state = ''
		if g['status']['abstractGameState'] == 'Final':
			# final score
			game_state = 'Final'
		elif g['status']['abstractGameState'] == 'Live':
			game_state = g['linescore']['currentPeriodOrdinal'] + ' ' + g['linescore']['currentPeriodTimeRemaining']
		elif g['status']['abstractGameState'] == 'Preview':
			utc = arrow.get(g['gameDate'])
			print(utc.to('US/Eastern').format('HH:mm ZZZ'))
			game_state = utc.to('US/Eastern').format('HH:mm ZZZ')
		game_details = {'away_team':away_team,'away_score':away_score,'home_team':home_team,'home_score':home_score,'game_state':game_state}
		game_data.append(game_details)
	return render_template('scores.html',scores=game_data)
