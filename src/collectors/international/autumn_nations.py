"""
Autumn Nations Series スクレイパー

World Rugby API から試合情報を取得
"""

from .world_rugby import WorldRugbyCompetitionScraper


class AutumnNationsSeriesScraper(WorldRugbyCompetitionScraper):
    """Autumn Nations Series のスクレイパー（World Rugby API）"""

    def __init__(self):
        super().__init__(
            include_patterns=[r"Autumn Nations Series"],
            competition_id="ans",
            source_url="https://www.world.rugby/fixtures",
            source_name="World Rugby",
        )
