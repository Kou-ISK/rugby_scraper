import sys
from src.scraper.epcr import EPCRChallengeCupScraper, EPCRChampionsCupScraper
from src.scraper.league_one import LeagueOneScraper
from src.scraper.six_nations import (
    SixNationsScraper,
    SixNationsWomensScraper,
    SixNationsU20Scraper,
)
from src.scraper.rugbyviz import (
    GallagherPremiershipScraper,
    UnitedRugbyChampionshipScraper,
)
from src.scraper.super_rugby import SuperRugbyPacificScraper
from src.scraper.top14 import Top14Scraper
from src.scraper.world_rugby import WorldRugbyInternationalsScraper
from src.scraper.rugby_championship import RugbyChampionshipScraper
from src.scraper.autumn_nations import AutumnNationsSeriesScraper

def main():
    if len(sys.argv) != 2:
        print("Usage: python main.py <scraper-type>")
        sys.exit(1)
    
    scraper_type = sys.argv[1]
    scrapers = {
        "six-nations": SixNationsScraper(),
        "six-nations-women": SixNationsWomensScraper(),
        "six-nations-u20": SixNationsU20Scraper(),
        "epcr-challenge": EPCRChallengeCupScraper(),
        "epcr-champions": EPCRChampionsCupScraper(),
        "top14": Top14Scraper(),
        "league-one": LeagueOneScraper(),
        "gallagher-premiership": GallagherPremiershipScraper(),
        "urc": UnitedRugbyChampionshipScraper(),
        "super-rugby-pacific": SuperRugbyPacificScraper(),
        "world-rugby-internationals": WorldRugbyInternationalsScraper(),
        "rugby-championship": RugbyChampionshipScraper(),
        "autumn-nations-series": AutumnNationsSeriesScraper(),
    }
    
    if scraper_type not in scrapers:
        print(f"Unknown scraper type: {scraper_type}")
        sys.exit(1)
    
    scraper = scrapers[scraper_type]
    matches = scraper.scrape()
    scraper.save_to_json(matches, scraper_type)

if __name__ == "__main__":
    main() 
