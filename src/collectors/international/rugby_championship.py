"""
The Rugby Championship スクレイパー

World Rugby API から試合情報を取得
"""

from .world_rugby import WorldRugbyCompetitionScraper


class RugbyChampionshipScraper(WorldRugbyCompetitionScraper):
    """The Rugby Championship のスクレイパー（World Rugby API）"""

    def __init__(self):
        super().__init__(
            include_patterns=[r"^(?:The )?Rugby Championship(?:\s+\d{4})?$"],
            competition_id="trc",
            source_url="https://www.world.rugby/fixtures",
            source_name="World Rugby",
        )
