"""Expand teams.json with comprehensive team master data.

新しいID体系: {competition_abbr}-{number}
例: m6n-1 (Men's Six Nations - England), jrlo-1 (League One - 埼玉)
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEAMS_JSON = ROOT / "data" / "teams.json"

# 大会ID・略称マッピング
COMPETITION_IDS = {
    "six-nations": "m6n",           # Men's Six Nations
    "six-nations-women": "w6n",     # Women's Six Nations
    "six-nations-u20": "u6n",       # U20 Six Nations
    "league-one": "jrlo",           # Japan Rugby League One
    "top14": "t14",                 # Top 14
    "gallagher-premiership": "gp",  # Gallagher Premiership
    "urc": "urc",                   # United Rugby Championship
    "epcr-champions": "ecc",        # EPCR Champions Cup
    "epcr-challenge": "ech",        # EPCR Challenge Cup
    "super-rugby-pacific": "srp",   # Super Rugby Pacific
    "rugby-championship": "trc",    # The Rugby Championship
    "autumn-nations-series": "ans", # Autumn Nations Series
    "world-rugby-internationals": "wri", # World Rugby Internationals
}

# 大会別チーム定義（新ID形式: {comp_abbr}-{number}）
COMPETITION_TEAMS = {
    "m6n": [
        {"num": 1, "name": "England", "name_ja": "イングランド", "short_name": "ENG", "country": "England"},
        {"num": 2, "name": "France", "name_ja": "フランス", "short_name": "FRA", "country": "France"},
        {"num": 3, "name": "Ireland", "name_ja": "アイルランド", "short_name": "IRE", "country": "Ireland"},
        {"num": 4, "name": "Italy", "name_ja": "イタリア", "short_name": "ITA", "country": "Italy"},
        {"num": 5, "name": "Scotland", "name_ja": "スコットランド", "short_name": "SCO", "country": "Scotland"},
        {"num": 6, "name": "Wales", "name_ja": "ウェールズ", "short_name": "WAL", "country": "Wales"},
    ],
    "w6n": [
        {"num": 1, "name": "England", "name_ja": "イングランド", "short_name": "ENG", "country": "England"},
        {"num": 2, "name": "France", "name_ja": "フランス", "short_name": "FRA", "country": "France"},
        {"num": 3, "name": "Ireland", "name_ja": "アイルランド", "short_name": "IRE", "country": "Ireland"},
        {"num": 4, "name": "Italy", "name_ja": "イタリア", "short_name": "ITA", "country": "Italy"},
        {"num": 5, "name": "Scotland", "name_ja": "スコットランド", "short_name": "SCO", "country": "Scotland"},
        {"num": 6, "name": "Wales", "name_ja": "ウェールズ", "short_name": "WAL", "country": "Wales"},
    ],
    "u6n": [
        {"num": 1, "name": "England", "name_ja": "イングランド", "short_name": "ENG", "country": "England"},
        {"num": 2, "name": "France", "name_ja": "フランス", "short_name": "FRA", "country": "France"},
        {"num": 3, "name": "Ireland", "name_ja": "アイルランド", "short_name": "IRE", "country": "Ireland"},
        {"num": 4, "name": "Italy", "name_ja": "イタリア", "short_name": "ITA", "country": "Italy"},
        {"num": 5, "name": "Scotland", "name_ja": "スコットランド", "short_name": "SCO", "country": "Scotland"},
        {"num": 6, "name": "Wales", "name_ja": "ウェールズ", "short_name": "WAL", "country": "Wales"},
    ],
    "jrlo": [
        {"num": 1, "name": "Saitama Wild Knights", "name_ja": "埼玉ワイルドナイツ", "short_name": "Wild Knights", "division": "Division 1"},
        {"num": 2, "name": "Tokyo Sungoliath", "name_ja": "東京サンゴリアス", "short_name": "Sungoliath", "division": "Division 1"},
        {"num": 3, "name": "Kubota Spears", "name_ja": "クボタスピアーズ船橋・東京ベイ", "short_name": "Spears", "division": "Division 1"},
        {"num": 4, "name": "Toyota Verblitz", "name_ja": "トヨタヴェルブリッツ", "short_name": "Verblitz", "division": "Division 1"},
        {"num": 5, "name": "Toshiba Brave Lupus Tokyo", "name_ja": "東芝ブレイブルーパス東京", "short_name": "Brave Lupus", "division": "Division 1"},
        {"num": 6, "name": "Yokohama Canon Eagles", "name_ja": "横浜キヤノンイーグルス", "short_name": "Eagles", "division": "Division 1"},
        {"num": 7, "name": "Kobelco Kobe Steelers", "name_ja": "コベルコ神戸スティーラーズ", "short_name": "Steelers", "division": "Division 1"},
        {"num": 8, "name": "Black Rams Tokyo", "name_ja": "ブラックラムズ東京", "short_name": "Black Rams", "division": "Division 1"},
        {"num": 9, "name": "Ricoh Black Rams Tokyo", "name_ja": "リコーブラックラムズ東京", "short_name": "Ricoh Black Rams", "division": "Division 1"},
        {"num": 10, "name": "Shizuoka Blue Revs", "name_ja": "静岡ブルーレヴズ", "short_name": "Blue Revs", "division": "Division 1"},
        {"num": 11, "name": "Mie Honda Heat", "name_ja": "三重ホンダヒート", "short_name": "Mie Honda", "division": "Division 1"},
        {"num": 12, "name": "Hanazono Kintetsu Liners", "name_ja": "花園近鉄ライナーズ", "short_name": "Liners", "division": "Division 1"},
    ],
    "trc": [
        {"num": 1, "name": "Argentina", "name_ja": "アルゼンチン", "short_name": "ARG", "country": "Argentina"},
        {"num": 2, "name": "Australia", "name_ja": "オーストラリア", "short_name": "AUS", "country": "Australia"},
        {"num": 3, "name": "New Zealand", "name_ja": "ニュージーランド", "short_name": "NZL", "country": "New Zealand"},
        {"num": 4, "name": "South Africa", "name_ja": "南アフリカ", "short_name": "RSA", "country": "South Africa"},
    ],
}

# Comprehensive team master data (旧形式 - 後方互換性のため残す)
TEAMS = {
    # Six Nations (Men's/Women's/U20)
    "eng": {"id": "eng", "name": "England", "short_name": "ENG", "country": "England"},
    "fra": {"id": "fra", "name": "France", "short_name": "FRA", "country": "France"},
    "ire": {"id": "ire", "name": "Ireland", "short_name": "IRE", "country": "Ireland"},
    "ita": {"id": "ita", "name": "Italy", "short_name": "ITA", "country": "Italy"},
    "sco": {"id": "sco", "name": "Scotland", "short_name": "SCO", "country": "Scotland"},
    "wal": {"id": "wal", "name": "Wales", "short_name": "WAL", "country": "Wales"},
    
    # Rugby Championship
    "arg": {"id": "arg", "name": "Argentina", "short_name": "ARG", "country": "Argentina"},
    "aus": {"id": "aus", "name": "Australia", "short_name": "AUS", "country": "Australia"},
    "nzl": {"id": "nzl", "name": "New Zealand", "short_name": "NZL", "country": "New Zealand"},
    "rsa": {"id": "rsa", "name": "South Africa", "short_name": "RSA", "country": "South Africa"},
    
    # Japan League One (representative teams - add more as needed)
    "toyota-verblitz": {"id": "toyota-verblitz", "name": "Toyota Verblitz", "short_name": "Verblitz", "country": "Japan"},
    "black-rams-tokyo": {"id": "black-rams-tokyo", "name": "ブラックラムズ東京", "short_name": "Black Rams", "country": "Japan"},
    "mie-honda-heat": {"id": "mie-honda-heat", "name": "三重ホンダヒート", "short_name": "Mie Honda", "country": "Japan"},
    "saitama-wild-knights": {"id": "saitama-wild-knights", "name": "埼玉ワイルドナイツ", "short_name": "Wild Knights", "country": "Japan"},
    "tokyo-sungoliath": {"id": "tokyo-sungoliath", "name": "東京サンゴリアス", "short_name": "Sungoliath", "country": "Japan"},
    "yokohama-canon-eagles": {"id": "yokohama-canon-eagles", "name": "横浜キヤノンイーグルス", "short_name": "Eagles", "country": "Japan"},
    "kubota-spears": {"id": "kubota-spears", "name": "クボタスピアーズ船橋・東京ベイ", "short_name": "Spears", "country": "Japan"},
    "toshiba-brave-lupus": {"id": "toshiba-brave-lupus", "name": "東芝ブレイブルーパス東京", "short_name": "Brave Lupus", "country": "Japan"},
    "kobelco-kobe-steelers": {"id": "kobelco-kobe-steelers", "name": "コベルコ神戸スティーラーズ", "short_name": "Steelers", "country": "Japan"},
    "ricoh-black-rams": {"id": "ricoh-black-rams", "name": "リコーブラックラムズ東京", "short_name": "Black Rams", "country": "Japan"},
    "shizuoka-blue-revs": {"id": "shizuoka-blue-revs", "name": "静岡ブルーレヴズ", "short_name": "Blue Revs", "country": "Japan"},
    "hanazono-kintetsu-liners": {"id": "hanazono-kintetsu-liners", "name": "花園近鉄ライナーズ", "short_name": "Liners", "country": "Japan"},
    
    # URC (representative teams)
    "benetton": {"id": "benetton", "name": "Benetton", "short_name": "BEN", "country": "Italy"},
    "bulls": {"id": "bulls", "name": "Bulls", "short_name": "BUL", "country": "South Africa"},
    "cardiff": {"id": "cardiff", "name": "Cardiff", "short_name": "CAR", "country": "Wales"},
    "connacht": {"id": "connacht", "name": "Connacht", "short_name": "CON", "country": "Ireland"},
    "dragons": {"id": "dragons", "name": "Dragons", "short_name": "DRA", "country": "Wales"},
    "edinburgh": {"id": "edinburgh", "name": "Edinburgh", "short_name": "EDI", "country": "Scotland"},
    "glasgow": {"id": "glasgow", "name": "Glasgow Warriors", "short_name": "GLA", "country": "Scotland"},
    "leinster": {"id": "leinster", "name": "Leinster", "short_name": "LEI", "country": "Ireland"},
    "lions": {"id": "lions", "name": "Lions", "short_name": "LIO", "country": "South Africa"},
    "munster": {"id": "munster", "name": "Munster", "short_name": "MUN", "country": "Ireland"},
    "ospreys": {"id": "ospreys", "name": "Ospreys", "short_name": "OSP", "country": "Wales"},
    "scarlets": {"id": "scarlets", "name": "Scarlets", "short_name": "SCA", "country": "Wales"},
    "sharks": {"id": "sharks", "name": "Sharks", "short_name": "SHA", "country": "South Africa"},
    "stormers": {"id": "stormers", "name": "Stormers", "short_name": "STO", "country": "South Africa"},
    "ulster": {"id": "ulster", "name": "Ulster", "short_name": "ULS", "country": "Ireland"},
    "zebre": {"id": "zebre", "name": "Zebre", "short_name": "ZEB", "country": "Italy"},
    
    # Gallagher Premiership (representative teams)
    "bath": {"id": "bath", "name": "Bath", "short_name": "BAT", "country": "England"},
    "bristol": {"id": "bristol", "name": "Bristol Bears", "short_name": "BRI", "country": "England"},
    "exeter": {"id": "exeter", "name": "Exeter Chiefs", "short_name": "EXE", "country": "England"},
    "gloucester": {"id": "gloucester", "name": "Gloucester", "short_name": "GLO", "country": "England"},
    "harlequins": {"id": "harlequins", "name": "Harlequins", "short_name": "HAR", "country": "England"},
    "leicester": {"id": "leicester", "name": "Leicester Tigers", "short_name": "LEI", "country": "England"},
    "newcastle": {"id": "newcastle", "name": "Newcastle Falcons", "short_name": "NEW", "country": "England"},
    "northampton": {"id": "northampton", "name": "Northampton Saints", "short_name": "NOR", "country": "England"},
    "sale": {"id": "sale", "name": "Sale Sharks", "short_name": "SAL", "country": "England"},
    "saracens": {"id": "saracens", "name": "Saracens", "short_name": "SAR", "country": "England"},
    
    # Top 14 (representative teams)
    "bayonne": {"id": "bayonne", "name": "Aviron Bayonnais", "short_name": "BAY", "country": "France"},
    "bordeaux": {"id": "bordeaux", "name": "Union Bordeaux Bègles", "short_name": "BOR", "country": "France"},
    "castres": {"id": "castres", "name": "Castres Olympique", "short_name": "CAS", "country": "France"},
    "clermont": {"id": "clermont", "name": "ASM Clermont Auvergne", "short_name": "CLE", "country": "France"},
    "lyon": {"id": "lyon", "name": "Lyon OU", "short_name": "LYO", "country": "France"},
    "montpellier": {"id": "montpellier", "name": "Montpellier HR", "short_name": "MHR", "country": "France"},
    "pau": {"id": "pau", "name": "Section Paloise", "short_name": "PAU", "country": "France"},
    "perpignan": {"id": "perpignan", "name": "USA Perpignan", "short_name": "USP", "country": "France"},
    "racing-92": {"id": "racing-92", "name": "Racing 92", "short_name": "R92", "country": "France"},
    "la-rochelle": {"id": "la-rochelle", "name": "Stade Rochelais", "short_name": "SRO", "country": "France"},
    "stade-francais": {"id": "stade-francais", "name": "Stade Français", "short_name": "SFP", "country": "France"},
    "toulouse": {"id": "toulouse", "name": "Stade Toulousain", "short_name": "TOU", "country": "France"},
    "toulon": {"id": "toulon", "name": "RC Toulon", "short_name": "RCT", "country": "France"},
    "vannes": {"id": "vannes", "name": "RC Vannes", "short_name": "VAN", "country": "France"},
    
    # Super Rugby Pacific (representative teams)
    "blues": {"id": "blues", "name": "Blues", "short_name": "BLU", "country": "New Zealand"},
    "brumbies": {"id": "brumbies", "name": "Brumbies", "short_name": "BRU", "country": "Australia"},
    "chiefs": {"id": "chiefs", "name": "Chiefs", "short_name": "CHI", "country": "New Zealand"},
    "crusaders": {"id": "crusaders", "name": "Crusaders", "short_name": "CRU", "country": "New Zealand"},
    "drua": {"id": "drua", "name": "Fijian Drua", "short_name": "DRU", "country": "Fiji"},
    "force": {"id": "force", "name": "Western Force", "short_name": "FOR", "country": "Australia"},
    "highlanders": {"id": "highlanders", "name": "Highlanders", "short_name": "HIG", "country": "New Zealand"},
    "hurricanes": {"id": "hurricanes", "name": "Hurricanes", "short_name": "HUR", "country": "New Zealand"},
    "moana-pasifika": {"id": "moana-pasifika", "name": "Moana Pasifika", "short_name": "MP", "country": "New Zealand"},
    "reds": {"id": "reds", "name": "Queensland Reds", "short_name": "RED", "country": "Australia"},
    "rebels": {"id": "rebels", "name": "Melbourne Rebels", "short_name": "REB", "country": "Australia"},
    "waratahs": {"id": "waratahs", "name": "NSW Waratahs", "short_name": "WAR", "country": "Australia"},
    
    # Other international teams
    "fiji": {"id": "fiji", "name": "Fiji", "short_name": "FIJ", "country": "Fiji"},
    "geo": {"id": "geo", "name": "Georgia", "short_name": "GEO", "country": "Georgia"},
    "jpn": {"id": "jpn", "name": "Japan", "short_name": "JPN", "country": "Japan"},
    "por": {"id": "por", "name": "Portugal", "short_name": "POR", "country": "Portugal"},
    "rom": {"id": "rom", "name": "Romania", "short_name": "ROM", "country": "Romania"},
    "sam": {"id": "sam", "name": "Samoa", "short_name": "SAM", "country": "Samoa"},
    "ton": {"id": "ton", "name": "Tonga", "short_name": "TON", "country": "Tonga"},
    "uru": {"id": "uru", "name": "Uruguay", "short_name": "URU", "country": "Uruguay"},
    "usa": {"id": "usa", "name": "USA", "short_name": "USA", "country": "United States"},
}

def main():
    """Generate unified teams.json with new ID system"""
    teams = {}
    
    # 新ID形式でチームマスタを生成
    for comp_id, team_list in COMPETITION_TEAMS.items():
        for team_data in team_list:
            team_id = f"{comp_id}-{team_data['num']}"
            teams[team_id] = {
                "id": team_id,
                "competition_id": comp_id,
                "name": team_data["name"],
                "name_ja": team_data.get("name_ja", ""),
                "short_name": team_data["short_name"],
                "country": team_data.get("country", ""),
                "division": team_data.get("division", ""),
                "logo_url": "",
                "badge_url": "",
            }
    
    with open(TEAMS_JSON, "w", encoding="utf-8") as f:
        json.dump(teams, f, ensure_ascii=False, indent=2)
        f.write("\n")
    
    print(f"Generated {len(teams)} teams in {TEAMS_JSON}")
    print("\n例:")
    for team_id in list(teams.keys())[:10]:
        team = teams[team_id]
        print(f"  {team_id}: {team['name']} ({team['name_ja']})")

if __name__ == "__main__":
    main()
