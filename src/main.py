import sys
from src.collectors.european import EPCRChallengeCupScraper, EPCRChampionsCupScraper, Top14Scraper, GallagherPremiershipScraper, UnitedRugbyChampionshipScraper
from src.collectors.domestic import LeagueOneDivisionsScraper, SuperRugbyPacificScraper
from src.collectors.international import (
    SixNationsScraper,
    SixNationsWomensScraper,
    SixNationsU20Scraper,
    RugbyChampionshipScraper,
    AutumnNationsSeriesScraper,
    WorldRugbyInternationalsScraper,
)

def scrape_command(scraper_type):
    """Execute scraping for a specific competition."""
    scrapers = {
        "m6n": SixNationsScraper(),
        "w6n": SixNationsWomensScraper(),
        "u6n": SixNationsU20Scraper(),
        "ecc": EPCRChallengeCupScraper(),
        "ech": EPCRChallengeCupScraper(),
        "t14": Top14Scraper(),
        "jrlo": LeagueOneDivisionsScraper(),
        "gp": GallagherPremiershipScraper(),
        "urc": UnitedRugbyChampionshipScraper(),
        "srp": SuperRugbyPacificScraper(),
        "wri": WorldRugbyInternationalsScraper(),
        "rc": RugbyChampionshipScraper(),
        "ans": AutumnNationsSeriesScraper(),
    }
    
    if scraper_type not in scrapers:
        print(f"Unknown scraper type: {scraper_type}")
        print(f"Available: {', '.join(scrapers.keys())}")
        sys.exit(1)
    
    scraper = scrapers[scraper_type]
    print(f"Starting scraper for: {scraper_type}")
    matches = scraper.scrape()
    
    if matches:
        # League Oneは辞書形式で返す（Division別）
        if isinstance(matches, dict):
            total_matches = sum(len(v) for v in matches.values() if isinstance(v, list))
            print(f"✓ Scraped {total_matches} matches")
            print("✓ Files saved by scraper (division-specific)")
        # EPCRは内部でsave済み
        elif scraper_type in ["ecc", "ech"]:
            print(f"✓ Scraped {len(matches)} matches")
            print("✓ Saved by scraper internally")
        else:
            # 通常のリスト形式
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

def extract_teams_command():
    """Extract and consolidate teams from all match data."""
    from src.services.team_service import main as extract_teams
    print("Extracting teams from all match data...")
    extract_teams()

def validate_duplicates_command():
    """Validate and detect duplicate teams."""
    from src.validators.team_validator import main as validate_duplicates
    print("Validating team duplicates...")
    validate_duplicates()

def generate_metadata_command():
    """Generate competition metadata."""
    from src.repositories.competition_repository import main as generate_metadata
    print("Generating competition metadata...")
    generate_metadata()

def update_team_logos_command():
    """既存チームのロゴURLをTheSportsDB APIから取得して更新"""
    from src.services.team_service import update_team_logos
    update_team_logos()

def main():
    if len(sys.argv) < 2:
        print("Usage: python -m src.main <command> [args]")
        print("\nCommands:")
        print("  <comp_id>           Scrape specific competition (m6n, gp, etc.)")
        print("  extract-teams       Extract teams from match data")
        print("  validate-duplicates Check for duplicate teams")
        print("  generate-metadata   Generate competitions.json")
        print("  update-logos        Update team logos from TheSportsDB API")
        sys.exit(1)
    
    command = sys.argv[1]
    
    # Service commands
    if command == "extract-teams":
        extract_teams_command()
    elif command == "validate-duplicates":
        validate_duplicates_command()
    elif command == "generate-metadata":
        generate_metadata_command()
    elif command == "update-logos":
        update_team_logos_command()
    else:
        # Assume it's a scraper type
        scrape_command(command)

if __name__ == "__main__":
    main() 
