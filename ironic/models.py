from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

class DeploymentStatus(Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    SUCCESSFUL = "SUCCESSFUL"
    FAILED = "FAILED"

class DeploymentStep:
    def __init__(self, name: str, service: str, host: str):
        self.name = name
        self.service = service
        self.host = host
        self.status = DeploymentStatus.PENDING
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.error_message: Optional[str] = None

    def start(self):
        self.status = DeploymentStatus.IN_PROGRESS
        self.start_time = datetime.now()

    def complete(self):
        self.status = DeploymentStatus.SUCCESSFUL
        self.end_time = datetime.now()

    def fail(self, error_message: str):
        self.status = DeploymentStatus.FAILED
        self.end_time = datetime.now()
        self.error_message = error_message

    @property
    def duration(self) -> Optional[float]:
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

class DeploymentTracker:
    def __init__(self):
        self.steps: List[DeploymentStep] = []
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None

    def add_step(self, step: DeploymentStep):
        self.steps.append(step)

    def complete(self):
        self.end_time = datetime.now()

    @property
    def status(self) -> DeploymentStatus:
        if any(step.status == DeploymentStatus.FAILED for step in self.steps):
            return DeploymentStatus.FAILED
        if all(step.status == DeploymentStatus.SUCCESSFUL for step in self.steps):
            return DeploymentStatus.SUCCESSFUL
        if any(step.status == DeploymentStatus.IN_PROGRESS for step in self.steps):
            return DeploymentStatus.IN_PROGRESS
        return DeploymentStatus.PENDING

    def generate_report(self) -> Dict:
        return {
            "overall_status": self.status.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "steps": [
                {
                    "name": step.name,
                    "service": step.service,
                    "host": step.host,
                    "status": step.status.value,
                    "duration": step.duration,
                    "error": step.error_message
                }
                for step in self.steps
            ]
        }