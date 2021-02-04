from flask import Flask, render_template, send_from_directory

from Helpers import *
import requests
import requests_cache
import json
import arrow
import subprocess
import os

#requests_cache.install_cache('hockey_cache', expire_after=300)
app = Flask(__name__)
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int("5000"), threaded=True)

# version display stuff
#APP_VERSION = subprocess.check_output(["git","rev-parse","HEAD"]).strip().decode("utf-8")
APP_VERSION = "1.2"
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
        'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/slick')
def slick():
    hockeyHelp = Helpers()
    teams = hockeyHelp.get_all_teams()
    games_data = hockeyHelp.games_to_date()
    last_game_data = games_data[len(games_data)-2]
    return render_template('slick.html', games=games_data,last_game=last_game_data,all_teams=teams)

@app.route('/player/<player_id>')
def player(player_id):
    hockeyHelp = Helpers()
    teams = hockeyHelp.get_all_teams()

    url = 'https://statsapi.web.nhl.com/api/v1/people/'+player_id
    r = requests.get(url).json()
    player_info = r['people'][0]

    return render_template('player.html', player=player_info,all_teams=teams,version=APP_VERSION)

@app.route('/')
def show_playoffs():
        h = get_headlines()
        hockeyHelp = Helpers()
        teams = hockeyHelp.get_all_teams()
        sid = hockeyHelp.get_current_season()

        games_data = hockeyHelp.games_to_date()
        last_game_data = games_data[len(games_data)-2]

        if get_season_status() == "P":
            url = 'https://statsapi.web.nhl.com/api/v1/tournaments/playoffs?site=en_nhl&expand=round.series,schedule.game.seriesSummary,schedule.game&season='+str(sid)
            r = requests.get(url).json()
            playoff_msg = []
            current_round = r['defaultRound']
            for series in r['rounds'][current_round]['series']:
                    playoff_msg.append({'matchup': series['names']['matchupShortName'], 'status': series['currentGame']['seriesSummary']['seriesStatus']})
            return render_template('index.html', last_game=last_game_data,games=games_data,matches=playoff_msg, playoff_round=current_round,headlines=h,all_teams=teams,version=APP_VERSION)
        else:
            return render_template('index.html', last_game=last_game_data, games=games_data, headlines=h,all_teams=teams,version=APP_VERSION)

# game.types [ P = Playoffs, PR = Preasons, R = Regular , N = NO HOCKEY]
def get_season_status():
    api_resource = 'https://statsapi.web.nhl.com/api/v1/seasons/current'

    results = requests.get(api_resource).json()
    result = results['seasons'][0]

    regularSeasonStart = result['regularSeasonStartDate']
    regularSeasonEnd = result['regularSeasonEndDate']
    seasonEnd = result['seasonEndDate']

    goat = arrow.utcnow()

    arrow_regularSeasonStart = arrow.get(regularSeasonStart).timestamp
    arrow_regularSeasonEnd = arrow.get(regularSeasonEnd).timestamp
    arrow_seasonEnd = arrow.get(seasonEnd).timestamp

    if goat.timestamp > arrow_seasonEnd:
        # no hockey
        return "N"
    elif goat.timestamp > arrow_regularSeasonEnd and goat.timestamp < arrow_seasonEnd:
        # playoffs
        return "P"
    elif goat.timestamp > arrow_regularSeasonStart and goat.timestamp < arrow_regularSeasonEnd:
        # regular season
        return "R"
    else:
        pass

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
    return render_template('index.html', skater_points=points, skater_assists=assists,version=APP_VERSION)

@app.route('/game/<game_id>')
def get_game_details(game_id):
    hockeyHelp = Helpers()
    teams = hockeyHelp.get_all_teams()
    # first we must check if this game is even started before doing anything useful
    url = 'https://statsapi.web.nhl.com/api/v1/schedule?gamePk='+game_id
    r = requests.get(url).json()
    game_status = r['dates'][0]['games'][0]['status']

    # we need team_id values for both home and away, it gets used later
    home_id = r['dates'][0]['games'][0]['teams']['home']['team']['id']
    away_id = r['dates'][0]['games'][0]['teams']['away']['team']['id']
    home_abbr = hockeyHelp.get_team_abbr(home_id)
    away_abbr = hockeyHelp.get_team_abbr(away_id)

    game_date = get_game_date(game_id)

    if game_status['abstractGameState'] == 'Preview':
        # lets do preview type things
        msg = 'Game has not yet started'
        # last10 away
        away_team_last_ten = get_last_ten(away_id)
        print("away_team_last_ten:",away_team_last_ten)
        away = "%s [L10: %s]" % (away_abbr, away_team_last_ten)
        # last10 home
        home_team_last_ten = get_last_ten(home_id)
        home = "%s [L10: %s]" % (home_abbr, home_team_last_ten)
        #home = home_abbr + ' [L10: ' + home_team_last_ten + ']'

        return render_template('game_details.html', gamePk=game_id, m=msg, m2=game_date, away_team=away, home_team=home, all_teams=teams, version=APP_VERSION)
    else:
        # game is either done or in-progress, do everything else
        msg = ''
        url = 'https://statsapi.web.nhl.com/api/v1/game/'+game_id+'/linescore'
        r = requests.get(url).json()
        linescore_data = r['periods']

        url = 'https://statsapi.web.nhl.com/api/v1/game/'+game_id+'/boxscore'
        r2 = requests.get(url).json()
        boxscore = r2['teams']

        away_box_stats = boxscore['away']['teamStats']['teamSkaterStats']
        home_box_stats = boxscore['home']['teamStats']['teamSkaterStats']
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
        return render_template('game_details.html', gamePk=game_id, away_team=away_abbr, home_team=home_abbr,  m=msg, m2=game_date, sog=shots, goal=goals, goal_scoring=goal_details, penalty=penalties, away_box=away_box_stats, home_box=home_box_stats, all_teams=teams, version=APP_VERSION)

@app.route('/team/<team_id>')
def get_team(team_id):
    # TODO: implement ID check that doesn't rely upon an API query
    hockeyHelp = Helpers()
    teams = hockeyHelp.get_all_teams()
    sid = hockeyHelp.get_current_season()
    fid = hockeyHelp.team_to_franchise(team_id)
    # first we gather the regular standings
    url = 'https://statsapi.web.nhl.com/api/v1/teams/'+team_id+'?hydrate=franchise(roster(season='+str(sid)+',person(name,stats(splits=[statsSingleSeason]))))'
    records = requests.get(url).json()
    # desired stats: GP, G, A, P, +/-, PIM, PPG, PPP, SHG, SHP, GWG, OTG, S and S%
    roster = records['teams'][0]['franchise']['roster']['roster']
    ps = []
    for player in roster:
        player_name = player['person']['fullName']
        player_id = player['person']['id']
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
                statline = {'ID': player_id, 'NAME':player_name,'POSITION': player_position,'GP':stats_gp,'G':stats_g,'A':stats_a,'P':stats_p,'PLUS':stats_plusMinus,'PIM':stats_pim, 'PPG': stats_ppg, 'S': stats_s}    
                ps.append(statline)
        except:
            # no stats found
            pass
    team_scores = get_team_scores(team_id)
    
    # now we do goalie stats

    url = 'https://api.nhle.com/stats/rest/en/goalie/summary?isAggregate=false&isGame=false&sort=%5B%7B%22property%22:%22wins%22,%22direction%22:%22DESC%22%7D,%7B%22property%22:%22savePct%22,%22direction%22:%22DESC%22%7D%5D&start=0&limit=50&factCayenneExp=gamesPlayed%3E=1&cayenneExp=franchiseId%3D'+str(fid)+'%20and%20gameTypeId=2%20and%20seasonId%3C='+str(sid)+'%20and%20seasonId%3E='+str(sid)
    records = requests.get(url).json()
    # desired stats: S/C(Shoots/Catches), GP, GS, W, L, OT (Overtime Losses), SA (Shots Against), Svs (Saves), GA (Goals Against), Sv% (Save %) GAA (Goals-Against-Avg), TOI, PIM
    roster = records['data']
    gs = []
    for goalie in roster:
        stats_gp = goalie['gamesPlayed']
        stats_gs = goalie['gamesStarted']
        stats_w = goalie['wins']
        stats_l = goalie['losses']
        stats_ot = goalie['otLosses']
        stats_sa = goalie['shotsAgainst']
        stats_svs = goalie['saves']
        if goalie['savePct'] == None:
            stats_svp = 0
        else:
            stats_svp = goalie['savePct']
        stats_sc = goalie['shootsCatches']
        stats_ga = goalie['goalsAgainst']
        stats_gaa = goalie['goalsAgainstAverage']
        stats_toi = goalie['timeOnIce']
        stats_pim = goalie['penaltyMinutes']
        statline = {
        'NAME': goalie['goalieFullName'],
        'SC': stats_sc,
        'GP': stats_gp,
        'GS': stats_gs,
        'W': stats_w,
        'L': stats_l,
        'OT': stats_ot,
        'SA': stats_sa,
        'SVS': stats_svs,
        'SVP': round(stats_svp,2),
        'GA': stats_ga,
        'GAA': round(stats_gaa,2),
        'TOI': round(stats_toi/60),
        'PIM': stats_pim
        }
        gs.append(statline)
    return render_template('team.html', t=team_id, roster_stats=ps, goalie_stats=gs, g=team_scores, all_teams=teams, version=APP_VERSION)

@app.route('/team/<team_id>/playoffs')
def get_team_playoffs(team_id):
    # first we gather the regular standings
    hockeyHelp = Helpers()
    teams = hockeyHelp.get_all_teams()
    sid = hockeyHelp.get_current_season()
    fid = hockeyHelp.team_to_franchise(team_id)
    url = 'https://statsapi.web.nhl.com/api/v1/teams/'+team_id+'?hydrate=franchise(roster(season='+str(sid)+',person(name,stats(splits=[statsSingleSeasonPlayoffs]))))'

    team_playoff_status = check_team_playoffs_stats(team_id, str(sid))
    if team_playoff_status == 0:
        # no stats to show
        return render_template('team-playoffs.html', all_teams=teams, version=APP_VERSION)
    else:
        # stats to show
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
                    statline = {'NAME':player_name,'GP':stats_gp,'G':stats_g,'A':stats_a,'P':stats_p,'PLUS':stats_plusMinus,'PIM':stats_pim, 'PPG': stats_ppg, 'S': stats_s, 'POSITION': player_position}    
                    ps.append(statline)
            except:
                # no stats found
                pass
        
        # now lets do goalies
        url = 'https://api.nhle.com/stats/rest/en/goalie/summary?isAggregate=false&isGame=false&sort=%5B%7B%22property%22:%22wins%22,%22direction%22:%22DESC%22%7D,%7B%22property%22:%22savePct%22,%22direction%22:%22DESC%22%7D%5D&start=0&limit=50&factCayenneExp=gamesPlayed%3E=1&cayenneExp=franchiseId%3D'+str(fid)+'%20and%20gameTypeId=3%20and%20seasonId%3C='+str(sid)+'%20and%20seasonId%3E='+str(sid)
        records = requests.get(url).json()
        # desired stats: S/C(Shoots/Catches), GP, GS, W, L, OT (Overtime Losses), SA (Shots Against), Svs (Saves), GA (Goals Against), Sv% (Save %) GAA (Goals-Against-Avg), TOI, PIM
        roster = records['data']
        gs = []
        for goalie in roster:
            stats_gp = goalie['gamesPlayed']
            stats_gs = goalie['gamesStarted']
            stats_w = goalie['wins']
            stats_l = goalie['losses']
            stats_ot = goalie['otLosses']
            stats_sa = goalie['shotsAgainst']
            stats_svs = goalie['saves']
            if goalie['savePct'] == None:
                stats_svp = 0
            else:
                stats_svp = goalie['savePct']
            stats_sc = goalie['shootsCatches']
            stats_ga = goalie['goalsAgainst']
            stats_gaa = goalie['goalsAgainstAverage']
            stats_toi = goalie['timeOnIce']
            stats_pim = goalie['penaltyMinutes']
            statline = {
            'NAME': goalie['goalieFullName'],
            'SC': stats_sc,
            'GP': stats_gp,
            'GS': stats_gs,
            'W': stats_w,
            'L': stats_l,
            'OT': stats_ot,
            'SA': stats_sa,
            'SVS': stats_svs,
            'SVP': round(stats_svp,2),
            'GA': stats_ga,
            'GAA': round(stats_gaa,2),
            'TOI': round(stats_toi/60),
            'PIM': stats_pim
            }
            gs.append(statline)
        return render_template('team-playoffs.html', t=team_id, roster_stats=ps, goalie_stats=gs, all_teams=teams, version=APP_VERSION)

@app.route('/standings')
def get_standings():
    # first we gather the regular standings
    hockeyHelp = Helpers()
    teams = hockeyHelp.get_all_teams()
    sid = hockeyHelp.get_current_season()
    url = 'https://statsapi.web.nhl.com/api/v1/standings/byDivision?season='+sid
    records = requests.get(url).json()
    # 0 -> metro, 1-> atlantic, 2 -> central 3-> pacific
    standings = []
    master = []
    for r in records['records']:
        conference_name = r['conference']['name']
        division_name = r['division']['name']
        for team in r['teamRecords']:
            division_name = r['division']['name']
            team_id = team['team']['id']
            team_name = team['team']['name']
            team_points = team['points']
            team_rank_division = team['divisionRank']
            team_rank_wildcard = team['wildCardRank']
            team_last_ten = get_last_ten(team_id)
            team_standings = {'team_id':team_id,'team_name':team_name,'team_points':team_points,'team_rank_division':team_rank_division,'team_rank_wildcard':team_rank_wildcard,'division':division_name, 'last_ten':team_last_ten}
            standings.append(team_standings)
        master.append(standings)
        standings = []
    east = master[0]
    east += master[1]
    west = master[2]
    west += master[3]
    '''
        The NHL has altered the playoff format right now because of Covid19 and now
        there are no wildcards for this one-off playoff version they are doing.  The
        easiest solution here is a simple if/else that checks if the normal standings 
        endpoint is zero across all times and then just skips the wildcard data completely.
    '''
    if check_wildcard() == 0:
        # handling one-off and not displaying WC info
        return render_template('standings.html',east_conf=east,west_conf=west,standings=standings,all_teams=teams, version=APP_VERSION)
    else:
        # WC is present, render it normally
        url = 'https://statsapi.web.nhl.com/api/v1/standings/wildCard'
        records = requests.get(url).json()
        (eastern, western) = records['records']
        wc_teams = []
        for i in [0,1]:
                wc_teams.append(eastern['teamRecords'][i]['team']['name'])
                wc_teams.append(western['teamRecords'][i]['team']['name'])
        return render_template('standings.html',east_conf=east,west_conf=west,standings=standings,wc=wc_teams,all_teams=teams, version=APP_VERSION)

@app.route('/scores')
def get_scores():
    #scores = {'away_team':'FLA','away_score':'4','home_team':'TOR','home_score':'7'}
    hockeyHelp = Helpers()
    teams = hockeyHelp.get_all_teams()
    local = arrow.utcnow()
    td = local.to('US/Eastern').format('YYYY-MM-DD')
    url = 'https://statsapi.web.nhl.com/api/v1/schedule?expand=schedule.linescore&date='+td
    games = requests.get(url).json()
    game_data = [] 
    if games['totalItems'] == 0:
        # no games found
        return render_template('scores.html',msg="no games today :(", all_teams=teams, version=APP_VERSION)
    else:
        for g in games['dates'][0]['games']:
            game_id = g['gamePk']
            away_team = hockeyHelp.get_team_abbr(g['teams']['away']['team']['id'])
            home_team = hockeyHelp.get_team_abbr(g['teams']['home']['team']['id'])
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
        return render_template('scores.html',scores=game_data, all_teams=teams, version=APP_VERSION)

#@app.route('/scores/<team_id>')
def get_team_scores(team_id):
    hockeyHelp = Helpers()
    url = 'http://statsapi.web.nhl.com/api/v1/seasons/current'

    season_info = requests.get(url).json()

    start_date = season_info['seasons'][0]['regularSeasonStartDate']

    today = arrow.now().format('YYYY-MM-DD')
    url = 'http://statsapi.web.nhl.com/api/v1/schedule?teamId='+team_id+'&endDate='+today+'&startDate='+start_date

    season_games = requests.get(url).json()

    holder = []

    for game in season_games['dates']:
        game_id = game['games'][0]['gamePk']
        game_date = game['games'][0]['gameDate']
        temp_utc = arrow.get(game_date)
        game_start = temp_utc.to('US/Eastern').format('MM-DD-YYYY hh:mm A ZZZ')
        game_status = game['games'][0]['status']['abstractGameState']
        away_team = game['games'][0]['teams']['away']
        home_team = game['games'][0]['teams']['home']

        away_team_id = away_team['team']['id']
        away_team_score = away_team['score']
        home_team_id = home_team['team']['id']
        home_team_score = home_team['score']
       
        away_abbr = hockeyHelp.get_team_abbr(away_team_id)
        home_abbr = hockeyHelp.get_team_abbr(home_team_id)
        line_data = {
                'game_id': game_id,
                'game_date': game_start,
                'away_team': away_abbr,
                'away_team_id': away_team_id,
                'away_team_score': away_team_score,
                'home_team': home_abbr,
                'home_team_id': home_team_id,
                'home_team_score': home_team_score
                }
        holder.append(line_data)
    holder.reverse()
    #return render_template('team_scores.html',data=holder)
    return holder

@app.route('/schedule')
def get_schedule():
    # default is to check for games scheduled today
    hockeyHelp = Helpers()
    teams = hockeyHelp.get_all_teams()
    utc = arrow.utcnow()
    default_day = utc.format('YYYY-MM-DD')
    return render_template('schedule.html',defaultDay=default_day,all_teams=teams, version=APP_VERSION)

@app.route('/schedule/<team_id>')
def get_schedule_team(team_id):
    # default is to check for games scheduled today
    hockeyHelp = Helpers()
    teams = hockeyHelp.get_all_teams()
    utc = arrow.utcnow()
    default_day = utc.format('YYYY-MM-DD')
    return render_template('schedule.html',defaultDay=default_day,team=team_id,all_teams=teams, version=APP_VERSION)

@app.route('/mock')
def get_mock():
    hockeyHelp = Helpers()
    teams = hockeyHelp.get_all_teams()
    return render_template('mock.html', all_teams=teams)

# returns large json of the entire season schedule, consumed by the /schedule route
@app.route('/fs')
def schedule_full_season():
    things = []
    hockeyHelp = Helpers()
    sid = hockeyHelp.get_current_season()
    api_resource = 'https://statsapi.web.nhl.com/api/v1/schedule?season='+str(sid)
    data = requests.get(api_resource).json()
    for day in data['dates']:
        for game in day['games']:
            game_id = game['gamePk']
            game_date = game['gameDate']
            game_status = game['status']['statusCode']

            utc = arrow.get(game_date)
            game_start = utc.to('US/Eastern').format('hh:mm A ZZZ')

            away_team_id = game['teams']['away']['team']['id']
            away_team_name = game['teams']['away']['team']['name']

            home_team_id = game['teams']['home']['team']['id']
            home_team_name = game['teams']['home']['team']['name']
            #game_data = {'away_team_id':away_team_id,'away_team_name':away_team_name,'home_team_id':home_team_id,'home_team_name':home_team_name,'game_id':game_id,'start':game_date}
            
            # gather scores if game is over
            
            if game_status == "5" or game_status == "6" or game_status == "7":
                away_team_score = game['teams']['away']['score']
                home_team_score = game['teams']['home']['score']            
                game_title = "%s %s @ %s %s" % (hockeyHelp.get_team_abbr(away_team_id), away_team_score, hockeyHelp.get_team_abbr(home_team_id), home_team_score)
            else:
                # no scores for games that havent been played or finished yet
                game_title = "%s @ %s " % (hockeyHelp.get_team_abbr(away_team_id), hockeyHelp.get_team_abbr(home_team_id))
  
            game_data = {
                    'title': game_title,
                    'start': game_date,
                    'url': '/game/'+str(game_id)
                    }
            things.append(game_data)
    return json.dumps(things)

# returns full season schedule for a single team
@app.route('/fs/<team_id>')
def schedule_full_season_team(team_id):
    things = []
    hockeyHelp = Helpers()
    sid = hockeyHelp.get_current_season()
    api_resource = 'https://statsapi.web.nhl.com/api/v1/schedule?season='+str(sid)+'&teamId='+team_id
    data = requests.get(api_resource).json()
    for day in data['dates']:
        for game in day['games']:
            game_id = game['gamePk']
            game_date = game['gameDate']
            game_status = game['status']['statusCode']
            utc = arrow.get(game_date)
            game_start = utc.to('US/Eastern').format('hh:mm A ZZZ')

            away_team_id = game['teams']['away']['team']['id']
            away_team_name = game['teams']['away']['team']['name']
            

            home_team_id = game['teams']['home']['team']['id']
            home_team_name = game['teams']['home']['team']['name']
            

            # gather scores if game is over
            
            if game_status == "5" or game_status == "6" or game_status == "7":
                away_team_score = game['teams']['away']['score']
                home_team_score = game['teams']['home']['score']            
                game_title = "%s %s @ %s %s" % (hockeyHelp.get_team_abbr(away_team_id), away_team_score, hockeyHelp.get_team_abbr(home_team_id), home_team_score)
            else:
                # no scores for games that havent been played or finished yet
                game_title = "%s @ %s " % (hockeyHelp.get_team_abbr(away_team_id), hockeyHelp.get_team_abbr(home_team_id))
  
            #game_data = {'away_team_id':away_team_id,'away_team_name':away_team_name,'home_team_id':home_team_id,'home_team_name':home_team_name,'game_id':game_id,'start':game_date}

            game_data = {
                    'title': game_title,
                    'start': game_date,
                    'url': '/game/'+str(game_id)
                    }
            things.append(game_data)
    return json.dumps(things)


# returns the L10 value for a team id
def get_last_ten(team_id):
    res = 'https://statsapi.web.nhl.com/api/v1/standings?expand=standings.record'
    last_ten = ''
    data = requests.get(res).json()
    for conference in data['records']:
        for team in conference['teamRecords']:
            l10_data = team['records']['overallRecords'][3]
            (wins, losses, ot, recordType) = l10_data
            if team_id == int(team['team']['id']):
                last_ten = "%s-%s-%s" % (str(l10_data['wins']), l10_data['losses'], l10_data['ot'])
    return last_ten 

# returns the date/time for a game ID
def get_game_date(game_id):
    res = 'https://statsapi.web.nhl.com/api/v1/schedule?site=en_nhl&gamePk='+game_id+'&leaderGameTypes=&expand=schedule.broadcasts.all,schedule.radioBroadcasts,schedule.teams,schedule.ticket,schedule.game.content.media.epg'

    data = requests.get(res).json()

    venue_info = data['dates'][0]['games'][0]['venue']
    game_date = data['dates'][0]['games'][0]['gameDate']
    arrow_game_date = arrow.get(game_date)

    return arrow_game_date.to('US/Eastern').format('YYYY-MM-DD hh:mm A ZZZ')

# gets headlines (limit of 15 hardcoded for now)
def get_headlines():
    bulk_headlines = []
    res = 'http://site.api.espn.com/apis/site/v2/sports/hockey/nhl/news?limit=15'
    headlines = requests.get(res).json()
    for article in headlines['articles']:
        headline = article['headline']
        link = article['links']['web']['href']
        data = {'headline': headline, 'link': link}
        bulk_headlines.append(data)
    return bulk_headlines

# returns 0 if no wildcard data is found, 1 otherwise
def check_wildcard():
    url = 'http://statsapi.web.nhl.com/api/v1/standings'
    standings = requests.get(url).json()
    divisions = standings['records']

    wc_overall = 0

    for division in divisions:
        teams = division['teamRecords']
        for team in teams:
            team_name = team['team']['name']
            team_wc_rank = team['wildCardRank']
            if int(team_wc_rank) == 0:
                pass
            else:
                wc_overall += 1
    if wc_overall == 0:
        # no wildcard here boss
        return 0
    else:
        # wc detected, parse on!
        return 1

# returns 0 if there are no stats for that team/season in the playoffs or 1 if there is
def check_team_playoffs_stats(tid, sid):
    url = 'https://statsapi.web.nhl.com/api/v1/teams/'+tid+'?hydrate=franchise(roster(season='+sid+',person(name,stats(splits=[statsSingleSeasonPlayoffs]))))'

    data = requests.get(url).json()

    players = data['teams'][0]['franchise']['roster']['roster']
    zero_count = 0
    for person in players:
        fullName = person['person']['fullName']
        stats_split = person['person']['stats'][0]['splits']
        if len(stats_split) == 0:
            # no stats for this person in the current playoffs
            pass
        else:
            # some kind of stat, adding to the counter
            zero_count += 1
    if zero_count == 0:
        return 0 
    else:
        return 1

