from flask import Flask, render_template
import requests
import requests_cache
import json
import arrow

requests_cache.install_cache('hockey_cache', expire_after=300)

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
def show_playoffs():
	url = 'https://statsapi.web.nhl.com/api/v1/tournaments/playoffs?site=en_nhl&expand=round.series,schedule.game.seriesSummary,schedule.game&season=20182019'

	r = requests.get(url).json()
	playoff_msg = []
	current_round = r['defaultRound']
	for series in r['rounds'][current_round-1]['series']:
		playoff_msg.append({'matchup': series['names']['matchupShortName'], 'status': series['currentGame']['seriesSummary']['seriesStatus']})
	return render_template('index.html', matches=playoff_msg, playoff_round=current_round)

def get_leaders():
	# gather the league leaders data
	url = 'http://www.nhl.com/stats/rest/leaders?season=20182019&gameType=2'
	records = requests.get(url).json()

	# goalie - 0 -> GAA, 1 -> save %, 2 -> wins, 3 -> shutout
	# skater - 0 -> points, 1 -> goals, 2 -> assists, 3 -> plusMinus

	goalie = records['goalie']
	skater = records['skater']

	g_gaa = goalie[0]
	g_sv = goalie[1]
	g_win = goalie[2]
	g_shut = goalie[3]

	s_point = skater[0]
	s_goal = skater[1]
	s_assist = skater[2]
	s_plus = skater[3]

	points = []
	for player in s_point['leaders']:
		player_name = player['fullName']
		player_value = player['value']
		#print("%s - %s" % (player_name, player_value))
		player_data = {'player_name':player_name, 'value': player_value}
		points.append(player_data)
	assists = []		
	for player in s_point['leaders']:
		player_name = player['fullName']
		player_value = player['value']
		#print("%s - %s" % (player_name, player_value))
		player_data = {'player_name':player_name, 'value': player_value}
		assists.append(player_data)
	return render_template('index.html', skater_points=points, skater_assists=assists)

@app.route('/game/<game_id>')
def get_game_details(game_id):
	# first we must check if this game is even started before doing anything useful
	url = 'https://statsapi.web.nhl.com/api/v1/schedule?gamePk='+game_id
	r = requests.get(url).json()
	game_status = r['dates'][0]['games'][0]['status']

	# we need team_id values for both home and away, it gets used later
	home_id = r['dates'][0]['games'][0]['teams']['home']['team']['id']
	away_id = r['dates'][0]['games'][0]['teams']['away']['team']['id']
	home_abbr = getTeamAbbr(home_id)
	away_abbr = getTeamAbbr(away_id)

	if game_status['abstractGameState'] == 'Preview':
		# lets do preview type things
		msg = 'Game has not yet started'
		return render_template('game_details.html', gamePk=game_id, m=msg)
	else:
		# game is either done or in-progress, do everything else
		msg = ''
		url = 'https://statsapi.web.nhl.com/api/v1/game/'+game_id+'/linescore'
		r = requests.get(url).json()
		linescore_data = r['periods']

		# goals by period
		goals = {}
		for period in r['periods']:
			period_num = period['num']
			goals['p'+str(period_num)+'_home'] = linescore_data[period_num - 1]['home']['goals']
			goals['p'+str(period_num)+'_away'] = linescore_data[period_num - 1]['away']['goals']

		# shots by period
		shots = {}
		for period in r['periods']:
			period_num = period['num']
			shots['p'+str(period_num)+'_home'] = linescore_data[period_num - 1]['home']['shotsOnGoal']
			shots['p'+str(period_num)+'_away'] = linescore_data[period_num - 1]['away']['shotsOnGoal']

		# now lets find who got goals
		url = 'https://statsapi.web.nhl.com/api/v1/game/'+game_id+'/feed/live'
		r = requests.get(url).json()

		scoring_plays = r['liveData']['plays']['scoringPlays']

		goal_details = []

		for play in scoring_plays:
			play_data = r['liveData']['plays']['allPlays'][play]
			play_description = play_data['result']['description']
			play_period = play_data['about']['period']
			play_time = play_data['about']['periodTime']
			play_team = play_data['team']['triCode']
			play_details = {
					'period':play_period,
					'time':play_time,
					'team':play_team,
					'desc':play_description
					}
			goal_details.append(play_details)

		# pentalty plays 

		penalty_plays = r['liveData']['plays']['penaltyPlays']

		penalties = []

		for play in penalty_plays:
			penalty_data = r['liveData']['plays']['allPlays'][play]
			penalty_description = penalty_data['result']['description']
			penalty_period = penalty_data['about']['period']
			penalty_time = penalty_data['about']['periodTime']
			penalty_team = penalty_data['team']['triCode']
			penalty_details = {
					'period':penalty_period,
					'time':penalty_time,
					'team':penalty_team,
					'desc':penalty_description
					}
			penalties.append(penalty_details)
		return render_template('game_details.html', gamePk=game_id, away_team=away_abbr, home_team=home_abbr,  m=msg, sog=shots, goal=goals, goal_scoring=goal_details, penalty=penalties)

@app.route('/team/<team_id>')
def get_team(team_id):
	# TODO: implement ID check that doesn't rely upon an API query

	# first we gather the regular standings
	url = 'https://statsapi.web.nhl.com/api/v1/teams/'+team_id+'?hydrate=franchise(roster(season=20182019,person(name,stats(splits=[statsSingleSeason]))))'
	records = requests.get(url).json()
	# desired stats: GP, G, A, P, +/-, PIM, PPG, PPP, SHG, SHP, GWG, OTG, S and S%
	roster = records['teams'][0]['franchise']['roster']['roster']
	ps = []
	for player in roster:
		player_name = player['person']['fullName']
		player_position = player['person']['primaryPosition']['code']
		try:
			player_stats = player['person']['stats'][0]['splits'][0]['stat']
			if player_position != "G":
				stats_gp = player_stats['games']
				stats_g = player_stats['goals']
				stats_a = player_stats['assists']
				stats_p = player_stats['points']
				stats_plusMinus = player_stats['plusMinus']
				stats_pim = player_stats['penaltyMinutes']
				stats_ppg = player_stats['powerPlayGoals']
				stats_ppp = player_stats['powerPlayPoints']
				stats_shg = player_stats['shortHandedGoals']
				stats_shp = player_stats['shortHandedPoints']
				stats_gwg = player_stats['gameWinningGoals']
				stats_otg = player_stats['overTimeGoals']
				stats_s = player_stats['shots']
				stats_sp = player_stats['shotPct']
				statline = {'NAME':player_name,'GP':stats_gp,'G':stats_g,'A':stats_a,'P':stats_p,'PLUS':stats_plusMinus,'PIM':stats_pim, 'PPG': stats_ppg, 'S': stats_s}	
				ps.append(statline)
		except:
			# no stats found
			pass

	return render_template('team.html', t=team_id, roster_stats=ps)

@app.route('/team/<team_id>/playoffs')
def get_team_playoffs(team_id):
	# first we gather the regular standings
	url = 'https://statsapi.web.nhl.com/api/v1/teams/'+team_id+'?hydrate=franchise(roster(season=20182019,person(name,stats(splits=[statsSingleSeasonPlayoffs]))))'
	records = requests.get(url).json()
	# desired stats: GP, G, A, P, +/-, PIM, PPG, PPP, SHG, SHP, GWG, OTG, S and S%
	roster = records['teams'][0]['franchise']['roster']['roster']
	ps = []
	for player in roster:
		player_name = player['person']['fullName']
		player_position = player['person']['primaryPosition']['code']
		try:
			player_stats = player['person']['stats'][0]['splits'][0]['stat']
			if player_position != "G":
				stats_gp = player_stats['games']
				stats_g = player_stats['goals']
				stats_a = player_stats['assists']
				stats_p = player_stats['points']
				stats_plusMinus = player_stats['plusMinus']
				stats_pim = player_stats['penaltyMinutes']
				stats_ppg = player_stats['powerPlayGoals']
				stats_ppp = player_stats['powerPlayPoints']
				stats_shg = player_stats['shortHandedGoals']
				stats_shp = player_stats['shortHandedPoints']
				stats_gwg = player_stats['gameWinningGoals']
				stats_otg = player_stats['overTimeGoals']
				stats_s = player_stats['shots']
				stats_sp = player_stats['shotPct']
				statline = {'NAME':player_name,'GP':stats_gp,'G':stats_g,'A':stats_a,'P':stats_p,'PLUS':stats_plusMinus,'PIM':stats_pim, 'PPG': stats_ppg, 'S': stats_s}	
				ps.append(statline)
		except:
			# no stats found
			pass

	return render_template('team-playoffs.html', t=team_id, roster_stats=ps)
@app.route('/standings')
def get_standings():
	# first we gather the regular standings
	url = 'https://statsapi.web.nhl.com/api/v1/standings/byDivision'
	records = requests.get(url).json()
	# 0 -> metro, 1-> atlantic, 2 -> central 3-> pacific
	standings = []
	master = []
	for r in records['records']:
		conference_name = r['conference']['name']
		division_name = r['division']['name']
		print("%s - %s " %(conference_name, division_name))
		for team in r['teamRecords']:
			division_name = r['division']['name']
			team_id = team['team']['id']
			team_name = team['team']['name']
			team_points = team['points']
			team_rank_division = team['divisionRank']
			team_rank_wildcard = team['wildCardRank']
			team_standings = {'team_id':team_id,'team_name':team_name,'team_points':team_points,'team_rank_division':team_rank_division,'team_rank_wildcard':team_rank_wildcard,'division':division_name}
			standings.append(team_standings)
		master.append(standings)
		standings = []
	east = master[0]
	east += master[1]
	west = master[2]
	west += master[3]

	# now to collect wildcard info
	url = 'https://statsapi.web.nhl.com/api/v1/standings/wildCard'
	records = requests.get(url).json()
	(eastern, western) = records['records']
	wc_teams = []
	for i in [0,1]:
			wc_teams.append(eastern['teamRecords'][i]['team']['name'])
			wc_teams.append(western['teamRecords'][i]['team']['name'])
	return render_template('standings.html',east_conf=east,west_conf=west,standings=standings,wc=wc_teams)

@app.route('/scores')
def get_scores():
	#scores = {'away_team':'FLA','away_score':'4','home_team':'TOR','home_score':'7'}

	url = 'https://statsapi.web.nhl.com/api/v1/schedule?expand=schedule.linescore'
	games = requests.get(url).json()
	game_data = [] 
	if games['totalItems'] == 0:
		# no games found
		return render_template('scores.html',msg="no games today :(")
	else:
		for g in games['dates'][0]['games']:
			game_id = g['gamePk']
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
				game_state = utc.to('US/Eastern').format('hh:mm A ZZZ')
			game_details = {'away_team':away_team,'away_score':away_score,'home_team':home_team,'home_score':home_score,'game_state':game_state, 'game_id': game_id}
			game_data.append(game_details)
		return render_template('scores.html',scores=game_data)
