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
    print(f"Starting scraper for: {scraper_type}")
    matches = scraper.scrape()
    
    if matches:
        print(f"✓ Scraped {len(matches)} matches")
        if len(matches) > 0:
            sample = matches[0]
            print(f"✓ Sample match structure:")
            print(f"  - match_id: {sample.get('match_id', 'MISSING')}")
            print(f"  - competition_id: {sample.get('competition_id', 'MISSING')}")
            print(f"  - home_team_id: {sample.get('home_team_id', 'MISSING')}")
            print(f"  - away_team_id: {sample.get('away_team_id', 'MISSING')}")
            
            # 新ディレクトリ構造: {comp_id}/{season}
            comp_id = sample.get('competition_id', scraper_type)
            season = sample.get('season', 'unknown')
            save_path = f"{comp_id}/{season}"
        else:
            # フォールバック: 旧形式
            save_path = scraper_type
        
        scraper.save_to_json(matches, save_path)
        print(f"✓ Saved to data/matches/{save_path}.json")
    else:
        print(f"✗ No matches found or scraping failed")
        sys.exit(1)

if __name__ == "__main__":
    main() 
