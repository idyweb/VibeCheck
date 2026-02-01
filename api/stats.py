import json
import os
from pathlib import Path

DATA_DIR = Path("/app/data")
STATS_FILE = DATA_DIR / "stats.json"

class StatsService:
    """Service to handle global stats persistence."""
    
    @staticmethod
    def _ensure_data_dir():
        """Ensure data directory and file exist."""
        if not DATA_DIR.exists():
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            
        if not STATS_FILE.exists():
            with open(STATS_FILE, "w") as f:
                json.dump({"total_vibes_checked": 0}, f)
    
    @classmethod
    def get_count(cls) -> int:
        """Get the current global count."""
        cls._ensure_data_dir()
        try:
            with open(STATS_FILE, "r") as f:
                data = json.load(f)
                return data.get("total_vibes_checked", 0)
        except Exception:
            return 0
            
    @classmethod
    def increment_count(cls) -> int:
        """Increment the global count by 1."""
        cls._ensure_data_dir()
        current = cls.get_count()
        new_count = current + 1
        
        try:
            with open(STATS_FILE, "w") as f:
                json.dump({"total_vibes_checked": new_count}, f)
        except Exception:
            pass  # Fail silently for stats
            
        return new_count
