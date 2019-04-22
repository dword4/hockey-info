from app import app

import unittest
import json

class HockeyTestCase(unittest.TestCase):
	global team_ids
	team_ids = [15,2,5,12,29,4,3,1,14,6,10,8,13,7,17,9,18,52,19,25,21,16,30,20,28,54,53,23,24,22,26]
	
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

	if __name__ == '__main__':
		unittest.main()
