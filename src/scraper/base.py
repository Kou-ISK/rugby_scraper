from abc import ABC, abstractmethod
import json
from datetime import datetime
from pathlib import Path

class BaseScraper(ABC):
    def __init__(self):
        self.output_dir = Path("data/matches")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    @abstractmethod
    def scrape(self):
        pass
    
    def save_to_json(self, data: dict, filename: str):
        timestamp = datetime.utcnow().strftime("%Y%m%d")
        output_path = self.output_dir / f"{filename}_{timestamp}.json"
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, ensure_ascii=False, indent=2, fp=f) 