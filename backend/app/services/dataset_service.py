import csv
import io
import json
import random
from typing import Any, Generator

from faker import Faker

from app.domain.entities.dataset import Dataset, DatasetRow
from app.domain.enums.common import ExportFormat
from app.repositories.dataset_repo import DatasetRepository


class DatasetService:
    def __init__(self, repo: DatasetRepository):
        self._repo = repo

    def create_dataset(
        self,
        name: str,
        version: str = "1.0",
        labels: list[str] | None = None,
        schema_def: dict[str, Any] | None = None,
    ) -> Dataset:
        return self._repo.create_dataset(
            name=name,
            version=version,
            schema_def=schema_def,
            labels=labels,
        )

    def get_dataset(self, dataset_id: str) -> Dataset:
        return self._repo.get_dataset(dataset_id)

    def generate_rows(
        self,
        dataset_id: str,
        n: int = 100,
        seed: int | None = None,
    ) -> int:
        dataset = self._repo.get_dataset(dataset_id)

        fake = Faker()
        if seed is not None:
            Faker.seed(seed)
            random.seed(seed)

        labels = dataset.labels or ["positive", "negative", "neutral"]
        rows: list[dict[str, Any]] = []

        for _ in range(n):
            input_data = {
                "text": fake.sentence(nb_words=random.randint(5, 20)),
                "user_id": fake.uuid4(),
                "timestamp": fake.iso8601(),
                "source": random.choice(["web", "mobile", "api"]),
                "metadata": {
                    "ip": fake.ipv4(),
                    "user_agent": fake.user_agent(),
                },
            }
            label = random.choice(labels)
            rows.append({
                "input_data": input_data,
                "label": label,
                "meta": {"generated": True, "seed": seed},
            })

        return self._repo.insert_rows(dataset_id, rows)

    def export_dataset(
        self,
        dataset_id: str,
        format: ExportFormat = ExportFormat.JSONL,
        batch_size: int = 500,
    ) -> Generator[bytes, None, None]:
        offset = 0
        first_batch = True

        while True:
            rows = self._repo.list_rows(dataset_id, limit=batch_size, offset=offset)
            if not rows:
                break

            if format == ExportFormat.JSONL:
                for row in rows:
                    line = json.dumps(self._row_to_dict(row)) + "\n"
                    yield line.encode("utf-8")
            elif format == ExportFormat.CSV:
                output = io.StringIO()
                writer = csv.DictWriter(
                    output,
                    fieldnames=["id", "dataset_id", "input_data", "label", "meta", "created_at"],
                )
                if first_batch:
                    writer.writeheader()
                    first_batch = False
                for row in rows:
                    writer.writerow(self._row_to_dict(row))
                yield output.getvalue().encode("utf-8")

            offset += batch_size

    def _row_to_dict(self, row: DatasetRow) -> dict[str, Any]:
        return {
            "id": row.id,
            "dataset_id": row.dataset_id,
            "input_data": row.input_data,
            "label": row.label,
            "meta": row.meta,
            "created_at": row.created_at.isoformat(),
        }
