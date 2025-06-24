import requests
from bs4 import BeautifulSoup
import logging
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
		try:
			# Go to list category (this can be generalized out later)
			response = requests.get(f"{self.base_url}/the-list", headers=self.headers, timeout=10)
			response.raise_for_status()

			soup = BeautifulSoup(response.text, 'html.parser')

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
		
if __name__ == "__main__":
	scraper = PLScraper()

	testing = scraper._find_latest_list()

	if testing is not None:
		print("Latest article: ", testing)
	else:
		print("Failed")