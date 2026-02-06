from dataclasses import dataclass


@dataclass
class ExperimentAgent:
    experiment_id: str
    agent_id: str
    model_version_id: str
