from app import app
from app import Helpers

import unittest
import json

class HockeyTestCase(unittest.TestCase):
	global team_ids
	team_ids = [15,2,5,12,29,4,3,1,14,6,10,8,13,7,17,9,18,52,19,25,21,16,30,20,28,54,53,23,24,22,26]

	# ROUTES
	
	# test index page http response code
	def test_index_http(self):
		tester = app.test_client(self)
		response = tester.get('/')
		self.assertEqual(response.status_code, 200)

	# test teams pages http response codes
	def test_teams_http(self):
		tester = app.test_client(self)
		for team in team_ids:
			response = tester.get('/team/'+str(team))
			self.assertEqual(response.status_code, 200)

	# test team playoffs http response code
	def test_teams_playoffs_http(self):
		tester = app.test_client(self)
		for team in team_ids:
			response = tester.get('/team/'+str(team)+'/playoffs')
			self.assertEqual(response.status_code, 200)

	# test scores http response code
	def test_scores_http(self):
		tester = app.test_client(self)
		response = tester.get('/scores')
		self.assertEqual(response.status_code, 200)

	# test standings http response code
	def test_standings_http(self):
		tester = app.test_client(self)
		response = tester.get('/standings')
		self.assertEqual(response.status_code, 200)

	# test schedule http response code
	def test_schedule_http(self):
		tester = app.test_client(self)
		response = tester.get('/schedule')
		self.assertEqual(response.status_code, 200)

	# test game http response code
	def test_game_http(self):
		tester = app.test_client(self)
		response = tester.get('/game/2017030415')
		self.assertEqual(response.status_code, 200)

	# FUNCTIONS

	def test_get_current_season(self):
		#tester = app.test_client(self)
		#response = self.get_current_season()
		halp = Helpers()
		result = halp.get_current_season()
		self.assertEqual(len(result), 8)

	if __name__ == '__main__':
		unittest.main()
