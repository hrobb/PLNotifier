import json
import logging
from pathlib import Path

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


	def _load_config(self):
		with open(self.config_file, 'r') as f:
			config = json.load(f)

		return config
	
	def run_check(self):
		logging.info("Running upgrade check")

		# check for upgrades


def main():
	assistant = FantasyBaseballAssistant()

	assistant.run_check()

if __name__ == "__main__":
	main()