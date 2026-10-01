"""
Nations Championship スクレイパー

World Rugby API から試合情報を取得
"""

from .world_rugby import WorldRugbyCompetitionScraper


class NationsChampionshipScraper(WorldRugbyCompetitionScraper):
    """Nations Championship のスクレイパー（World Rugby API）"""

    def __init__(self):
        super().__init__(
            include_patterns=[r"^Nations Championship(?:\s+\d{4})?$"],
            competition_id="nc",
            source_url="https://www.world.rugby/fixtures",
            source_name="World Rugby",
        )
