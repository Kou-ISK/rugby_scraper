import sys
from src.scraper.epcr import EPCRChallengeCupScraper, EPCRChampionsCupScraper
from src.scraper.league_one import LeagueOneScraper
from src.scraper.six_nations import SixNationsScraper
from src.scraper.top14 import Top14Scraper

def main():
    if len(sys.argv) != 2:
        print("Usage: python main.py <scraper-type>")
        sys.exit(1)
    
    scraper_type = sys.argv[1]
    scrapers = {
        "six-nations": SixNationsScraper(),
        "epcr-challenge": EPCRChallengeCupScraper(),
        "epcr-champions": EPCRChampionsCupScraper(),
        "top14": Top14Scraper(),
        "league-one": LeagueOneScraper(),
    }
    
    if scraper_type not in scrapers:
        print(f"Unknown scraper type: {scraper_type}")
        sys.exit(1)
    
    scraper = scrapers[scraper_type]
    matches = scraper.scrape()
    scraper.save_to_json(matches, scraper_type)

if __name__ == "__main__":
    main() 