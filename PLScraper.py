import requests
from bs4 import BeautifulSoup
import pandas as pd
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class PLScraper:
	def __init__(self):
		self.base_url = "https://www.pitcherlist.com/category/fantasy"
		self.cache_dir = Path("cache")
		self.cache_dir.mkdir(exist_ok=True)

		self.headers = {
			"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0"
		}

	def _find_latest_list(self):
		"""
		Find and return the URL of the latest list article
		"""

		try:
			# Go to list category (this can be generalized out later)
			response = requests.get(f"{self.base_url}/the-list", headers=self.headers, timeout=10)
			response.raise_for_status()

			soup = BeautifulSoup(response.text, 'lxml')

			# Look for the latest title div
			articleTitle = soup.find('div', class_='title')

			# If it exists, find the associated link and return it
			if articleTitle:
				link = articleTitle.find('a')
				if link and link.has_attr('href'):
					latest = link['href']
					logging.info(f"Found latest link: {latest}")
					return latest
				else:
					logging.error("Div doesn't contain anchor or couldn't be found")
				return None
			else:
				logging.error("Article title class has changed or couldn't be found")
				return None
		
		except Exception as e:
			logging.error(f"Error finding URL: {e}")
			return None
		
	def get_pitcher_rankings(self, force_refresh=False):
		"""
		Scrape the latest rankings from the list
		
		Args:
			force_refresh (bool): If True, ignore cache and fetch fresh data
			
		Returns:
			DataFrame with pitcher rankings
		"""

		# Create daily cache file
		today = datetime.now().strftime("%Y-%m-%d")
		cache_file = self.cache_dir / f"pitcher_rankings_{today}.csv"

		# Check if cache exists for today
		if not force_refresh and cache_file.exists():
			logging.info(f"Loading cached rankings from {cache_file}")
			return pd.read_csv(cache_file)
		
		# Get latest list URL
		list_url = self._find_latest_list()
		if not list_url:
			logging.error("Failed to find latest list")
			return None
		
		try:
			# Go to list page
			logging.info(f"Fetching rankings from {list_url}")
			response = requests.get(list_url, headers=self.headers, timeout=15)
			response.raise_for_status()

			soup = BeautifulSoup(response.text, 'lxml')

			# Find the rankings table
			table = soup.find('table', class_='list')
			if table:
				try:
					# Read in the data
					df = pd.read_html(str(table), flavor='lxml')[0]
					
					# Provided data is present: clean, cache, and return it
					if not df.empty:
						logging.info(f"Found rankings table: {df.columns.tolist()}")

						# Add method for cleaning up the data (verify typing, drop badges, drop "tier" text)

						df.to_csv(cache_file, index=False)
						return df

				except Exception as e:
					logging.warning(f"Error parsing table {table}: {e}")
					return None

		except Exception as e:
			logging.error(f"Error scraping pitcher rankings: {e}")
			return None
		
	#def _clean_rankings_df

		
if __name__ == "__main__":
	scraper = PLScraper()

	testing = scraper.get_pitcher_rankings()

	if testing is not None:
		print("Latest list: \n", testing)
	else:
		print("Failed")