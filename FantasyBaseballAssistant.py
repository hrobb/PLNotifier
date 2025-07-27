import json
import logging
from pathlib import Path
from fuzzywuzzy import fuzz, process

from YahooFantasyInterface import YahooFantasyInterface
from PLScraper import PLScraper



class FantasyBaseballAssistant:
	def __init__(self, config_file="config.json"):
		"""
		Initialize the assistant.
		
		Args:
			config_file (str): Path to config file
		"""

		self.config_file = config_file
		self.config = self._load_config()
		self.cache_dir = Path(self.config.get("cache_dir", "cache"))
		self.cache_dir.mkdir(exist_ok=True)

		# Init the interface
		self.yahoo = YahooFantasyInterface(
			client_id=self.config["yahooInterface"]["client_id"],
			client_secret=self.config["yahooInterface"]["client_secret"],
			league_id=self.config["yahooInterface"]["league_id"]
		)

		# Init the scraper
		self.pl = PLScraper()

		# Init player mapping
		self.player_map_file = self.cache_dir / "name_mapping.json"
		self.player_map = self._load_player_map()


	def _load_config(self):
		with open(self.config_file, 'r') as f:
			config = json.load(f)

		return config
	
	def _load_player_map(self):
		if self.player_map_file.exists():
			with open(self.player_map_file, 'r') as f:
				return json.load(f)
		return {}
	
	def _save_player_map(self):
		with open(self.player_map_file, 'w') as f:
			json.dump(self.player_map, f, indent=4)

	def match_player_names(self, yahoo_name, pl_names, threshold):
		"""
		Match player names between Yahoo and Pitcherlist
		
		Args:
			yahoo_name (str): Player name from Yahoo
			pl_names (list): List of player names from PL
			threshold (int): Min similarity score
		
		Returns:
			Best matched name or None
		"""

		# Check cache
		if yahoo_name in self.player_map:
			return self.player_map[yahoo_name]
		
		# Match
		best_match, score = process.extractOne(yahoo_name, pl_names, scorer=fuzz.token_sort_ratio)

		if score >= threshold:
			self.player_map[yahoo_name] = best_match
			self._save_player_map()
			return best_match
		
		return None

	
	def check_for_upgrades(self):
		"""
		Check for available players that are ranked higher than current players
		
		Returns:
			Tuple of recommended pickups, myPitchers, and available pitchers
		"""
		logging.info("Checking for pitcher upgrades")

		# Get PL rankings, current roster
		rankings_df = self.pl.get_pitcher_rankings()
		if rankings_df is None or len(rankings_df) == 0:
			logging.error("Failed to retrieve from PL")
			return [], None, None
		logging.info(f"Got {len(rankings_df)} rankings from Pitcherlist")

		curr_roster = self.yahoo.get_my_roster()
		if not curr_roster:
			logging.error("Failed to get roster")
			return [], None, None
		
		starters = [p for p in curr_roster if "SP" in p["position"]]

		# Get available pitchers
		available_players = self.yahoo.get_available_players()
		if not available_players:
			logging.error("Failed to retrieve available players")
			return [], starters, None
		
		available_starters = [p for p in available_players if "SP" in p["position"]]

		# Process current starters
		ranked_pitchers_df = rankings_df.copy()
		all_ranked_sp = ranked_pitchers_df['Pitcher'].tolist()

		my_ranked_starters = []
		for pitcher in starters:
			yahoo_name = pitcher['name']
			matched_name = self.match_player_names(yahoo_name, all_ranked_sp, 90)

			if matched_name:
				rank = ranked_pitchers_df[ranked_pitchers_df["Pitcher"] == matched_name]['Rank'].iloc[0]
				my_ranked_starters.append({
					'yahoo_name': yahoo_name,
					'pl_name': matched_name,
					'rank': rank,
					'position': pitcher.get('position', '')
				})
			else:
				my_ranked_starters.append({
					'yahoo_name': yahoo_name,
					'pl_name': None,
					'rank': float('inf'),
					'position': pitcher.get('position', '')
				})

		my_ranked_starters.sort(key=lambda x: x['rank'])

		# Process available starters
		available_ranked_starters = []
		for pitcher in available_starters:
			yahoo_name = pitcher['name']
			matched_name = self.match_player_names(yahoo_name, all_ranked_sp, 90)

			if matched_name:
				rank = ranked_pitchers_df[ranked_pitchers_df['Pitcher'] == matched_name]['Rank'].iloc[0]
				available_ranked_starters.append({
					'yahoo_name': yahoo_name,
					'pl_name': matched_name,
					'rank': rank,
					'position': pitcher.get('position', '')
				})

		available_ranked_starters.sort(key=lambda x: x['rank'])

		# Find upgrades
		upgrades = []
		threshold = 0

		worst_ranked = [p for p in my_ranked_starters if p['rank'] != float('inf')]
		if worst_ranked:
			worst_rank = worst_ranked[-1]['rank']

			for starter in available_ranked_starters:
				if starter['rank'] + threshold <= worst_rank:
					upgrades.append({
						'available_pitcher': starter,
						'rank_difference': worst_rank - starter['rank'],
						'drop_candidates': [p for p in my_ranked_starters 
							if p['rank'] == float('inf') or p['rank'] >= starter['rank']]
					})

		return upgrades, my_ranked_starters, available_ranked_starters
	
	def run_check(self):
		logging.info("Running upgrade check")

		upgrades, myPitchers, availablePitchers = self.check_for_upgrades()
		for item in upgrades:
			print(item)
			print("\n")

		# TODO: Add additional filtering for incredibly close name matches
		#	Process upgrades to readable format
		#	Notification?


def main():
	assistant = FantasyBaseballAssistant()

	assistant.run_check()

if __name__ == "__main__":
	main()