import json
from yahoofantasy import Context, League

class YahooFantasyInterface:
	def __init__(self, client_id, client_secret, league_id):

		self.client_id = client_id
		self.client_secret = client_secret
		self.league_id = league_id

		self.context = None
		self.league = None

		self._authenticate()

	def _authenticate(self):
		try:
			self.context = Context()
			print("Authentication successful")

			self.league = League(self.context, self.league_id)

		except Exception as e:
			print(f"Authentication failed: {e}")
			raise
	
	def get_my_team(self):
		if not self.league:
			raise ValueError("No league was pulled, please ensure a valid League ID")
		
		for team in self.league.teams():
			if hasattr(team, 'is_owned_by_current_login') and team.is_owned_by_current_login:
				return team

		raise ValueError("Team was not found")
	
	def get_my_roster(self):
		team = self.get_my_team()

		players = []
		for player in team.players():
			# Will only support pitchers initially, this may change later
			if player.position_type == "P":
				player_info = {
					"name": player.name.full,
					"position": player.display_position,
					"position_type": player.position_type
				}

				players.append(player_info)

		return players

	def get_available_players(self):
		if not self.league:
			raise ValueError("No league was pulled, please ensure a valid League ID")
		
		try:
			available_players = self.league.players('A')

			players = []
			for player in available_players:
				if player.position_type == "P":
					player_info = {
						"name": player.name.full,
						"position": player.display_position,
						"position_type": player.position_type
					}

					players.append(player_info)
			
			return players
		
		except AttributeError:
			print("Free agent method not working")
			return []

if __name__ == "__main__":
	with open("config.json", "r") as f:
		data = json.load(f)

	CLIENT_ID = data['yahooInterface']['client_id']
	CLIENT_SECRET = data['yahooInterface']['client_secret']
	LEAGUE_ID = data['yahooInterface']['league_id']

	yahoo = YahooFantasyInterface(CLIENT_ID, CLIENT_SECRET, LEAGUE_ID)

	team_info = yahoo.get_my_roster()
	for item in team_info:
		print(item)

	fa_info = yahoo.get_available_players()
	for player in fa_info:
		print(player)