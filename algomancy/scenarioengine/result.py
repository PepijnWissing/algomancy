from dataclasses import dataclass
from datetime import datetime


@dataclass
class ScenarioResult:
    master_data_id: str
    completed_at: datetime = datetime.now()

    def to_dict(self):
        return {
            "master_data_id": self.master_data_id,
            "completed_at": self.completed_at.isoformat()
        }
