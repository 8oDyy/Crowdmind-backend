import csv
import io
import random
from typing import Any

from faker import Faker

from app.core.config import Settings
from app.domain.entities.dataset import Dataset, DatasetVersion
from app.infrastructure.llm.ollama_client import OllamaClient, OllamaConfig
from app.infrastructure.storage.storage_client import StorageClient
from app.repositories.dataset_repo import DatasetRepository, DatasetVersionRepository

SYSTEM_PROMPT_BATCH = (
    "Tu es un générateur de données d'entraînement pour un modèle de classification. "
    "Génère exactement {count} phrases courtes (1-2 phrases chacune) "
    "qui représentent le point de vue d'un archétype. "
    "Chaque phrase doit être sur une ligne séparée, sans numérotation ni tirets. "
    "Les phrases doivent être variées, naturelles et cohérentes avec la description."
)

VARIATION_PREFIXES = [
    "", "Je pense que ", "À mon avis, ", "Selon moi, ", "Il me semble que ",
    "Je crois que ", "Pour moi, ", "D'après moi, ", "Personnellement, ",
    "En ce qui me concerne, ", "De mon point de vue, ", "Je suis convaincu que ",
]

VARIATION_SUFFIXES = [
    "", " C'est ma conviction.", " Voilà ce que je pense.", " C'est important.",
    " C'est essentiel.", " C'est évident.", " C'est une certitude.",
]


class DatasetService:
    def __init__(
        self,
        dataset_repo: DatasetRepository,
        version_repo: DatasetVersionRepository,
        storage: StorageClient,
        settings: Settings,
        ollama_client: OllamaClient | None = None,
    ):
        self._dataset_repo = dataset_repo
        self._version_repo = version_repo
        self._storage = storage
        self._settings = settings
        self._ollama = ollama_client or OllamaClient(
            OllamaConfig(
                host=getattr(settings, "OLLAMA_HOST", "http://localhost:11434"),
                model=getattr(settings, "OLLAMA_MODEL", "qwen2.5:latest"),
            )
        )

    def create_dataset(
        self,
        name: str,
        dataset_type: str,
        created_by: str,
        description: str | None = None,
    ) -> Dataset:
        return self._dataset_repo.create_dataset(
            name=name,
            dataset_type=dataset_type,
            created_by=created_by,
            description=description,
        )

    def get_dataset(self, dataset_id: str) -> Dataset:
        return self._dataset_repo.get_dataset(dataset_id)

    def list_datasets(self, limit: int = 100, offset: int = 0) -> list[Dataset]:
        return self._dataset_repo.list_datasets(limit=limit, offset=offset)

    def create_version(
        self,
        dataset_id: str,
        version: str,
        file_bytes: bytes,
        format: str,
        content_type: str = "application/octet-stream",
        schema: dict[str, Any] | None = None,
        stats: dict[str, Any] | None = None,
    ) -> DatasetVersion:
        self._dataset_repo.get_dataset(dataset_id)

        path = f"datasets/{dataset_id}/{version}.{format}"
        meta = self._storage.upload_bytes(
            path=path,
            content=file_bytes,
            content_type=content_type,
        )

        size_kb = meta.size // 1024

        return self._version_repo.create_version(
            dataset_id=dataset_id,
            version=version,
            file_path=meta.path,
            format=format,
            checksum=meta.checksum,
            size_kb=size_kb,
            schema=schema,
            stats=stats,
        )

    def get_version(self, version_id: str) -> DatasetVersion:
        return self._version_repo.get_version(version_id)

    def list_versions(
        self,
        dataset_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[DatasetVersion]:
        return self._version_repo.list_versions(
            dataset_id=dataset_id,
            limit=limit,
            offset=offset,
        )

    def _generate_base_templates(
        self,
        archetype_name: str,
        archetype_description: str,
        topics: list[str],
        templates_per_topic: int = 10,
    ) -> list[str]:
        """Génère des templates de base via Ollama pour un archétype."""
        all_templates = []

        for topic in topics:
            prompt = (
                f"Archétype: {archetype_name}\n"
                f"Description: {archetype_description}\n\n"
                f"Génère {templates_per_topic} opinions sur '{topic}' "
                f"du point de vue de cet archétype."
            )
            system = SYSTEM_PROMPT_BATCH.format(count=templates_per_topic)

            response = self._ollama.generate(
                prompt=prompt,
                system_prompt=system,
                temperature=0.9,
                max_tokens=1500,
            )

            lines = [line.strip() for line in response.strip().split("\n") if line.strip()]
            lines = [line.lstrip("0123456789.-) ") for line in lines]
            all_templates.extend(lines)

        return all_templates

    def _vary_text(self, base_text: str) -> str:
        """Applique des variations à un texte de base."""
        prefix = random.choice(VARIATION_PREFIXES)
        suffix = random.choice(VARIATION_SUFFIXES)

        if prefix and base_text[0].isupper():
            text = prefix + base_text[0].lower() + base_text[1:]
        else:
            text = prefix + base_text

        if suffix and not text.endswith((".", "!", "?")):
            text += "."

        if suffix:
            text = text.rstrip(".") + suffix

        return text

    def generate_archetype_dataset(
        self,
        dataset_id: str,
        version: str,
        archetype_1_name: str,
        archetype_1_description: str,
        archetype_2_name: str,
        archetype_2_description: str,
        n_per_archetype: int = 5000,
        seed: int | None = None,
        topics: list[str] | None = None,
    ) -> DatasetVersion:
        """Génère un dataset d'entraînement pour 2 archétypes.

        Utilise une approche hybride :
        1. Génère ~100-200 templates de base par archétype via Ollama
        2. Varie ces templates avec Faker pour créer n_per_archetype lignes

        Args:
            dataset_id: ID du dataset parent
            version: Version du dataset (ex: "v1.0")
            archetype_1_name: Nom du premier archétype
            archetype_1_description: Description du premier archétype
            archetype_2_name: Nom du deuxième archétype
            archetype_2_description: Description du deuxième archétype
            n_per_archetype: Nombre d'exemples par archétype (peut être 10 000+)
            seed: Seed pour reproductibilité
            topics: Liste optionnelle de sujets pour varier les opinions
        """
        self._dataset_repo.get_dataset(dataset_id)

        fake = Faker("fr_FR")
        if seed is not None:
            Faker.seed(seed)
            random.seed(seed)

        default_topics = [
            "l'économie", "l'environnement", "l'éducation", "la santé",
            "l'immigration", "la sécurité", "la culture", "le travail",
            "la famille", "la technologie",
        ]
        topics = topics or default_topics

        templates_per_topic = max(10, n_per_archetype // (len(topics) * 10))
        templates_per_topic = min(templates_per_topic, 20)

        archetypes = [
            {"name": archetype_1_name, "description": archetype_1_description},
            {"name": archetype_2_name, "description": archetype_2_description},
        ]

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["text", "topic", "age", "region", "archetype"])

        for arch in archetypes:
            base_templates = self._generate_base_templates(
                archetype_name=arch["name"],
                archetype_description=arch["description"],
                topics=topics,
                templates_per_topic=templates_per_topic,
            )

            if not base_templates:
                base_templates = [f"Opinion de {arch['name']} sur divers sujets."]

            for i in range(n_per_archetype):
                base_text = base_templates[i % len(base_templates)]
                text = self._vary_text(base_text)
                topic = topics[i % len(topics)]
                age = random.randint(18, 80)
                region = fake.region()

                writer.writerow([text, topic, age, region, arch["name"]])

        content = output.getvalue().encode("utf-8")

        archetype_names = [archetype_1_name, archetype_2_name]
        label_dist = {name: n_per_archetype for name in archetype_names}
        stats = {
            "row_count": 2 * n_per_archetype,
            "archetypes": [
                {"name": archetype_1_name, "description": archetype_1_description},
                {"name": archetype_2_name, "description": archetype_2_description},
            ],
            "n_per_archetype": n_per_archetype,
            "label_distribution": label_dist,
            "generator": "ollama+faker",
            "model": self._ollama._config.model,
            "base_templates_per_archetype": len(topics) * templates_per_topic,
        }

        return self.create_version(
            dataset_id=dataset_id,
            version=version,
            file_bytes=content,
            format="csv",
            content_type="text/csv",
            schema={
                "features": ["text", "topic", "age", "region"],
                "label_column": "archetype",
                "archetypes": archetype_names,
            },
            stats=stats,
        )

    def get_download_url(self, version_id: str, expires_seconds: int = 3600) -> str:
        version = self._version_repo.get_version(version_id)
        return self._storage.get_download_url(version.file_path, expires_seconds)
