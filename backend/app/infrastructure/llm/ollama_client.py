"""Client Ollama pour la génération de textes via LLM local."""

from dataclasses import dataclass

import ollama


@dataclass
class OllamaConfig:
    """Configuration pour le client Ollama."""

    host: str = "http://localhost:11434"
    model: str = "qwen2.5:latest"
    timeout: float = 60.0


class OllamaClient:
    """Client pour interagir avec Ollama en local."""

    def __init__(self, config: OllamaConfig | None = None):
        self._config = config or OllamaConfig()
        self._client = ollama.Client(host=self._config.host)

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 256,
    ) -> str:
        """Génère du texte avec le modèle configuré.

        Args:
            prompt: Le prompt utilisateur
            system_prompt: Instructions système optionnelles
            temperature: Contrôle la créativité (0.0-1.0)
            max_tokens: Nombre max de tokens en sortie

        Returns:
            Le texte généré
        """
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        response = self._client.chat(
            model=self._config.model,
            messages=messages,
            options={
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        )

        return response["message"]["content"]

    def generate_batch(
        self,
        prompts: list[str],
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 256,
    ) -> list[str]:
        """Génère du texte pour plusieurs prompts.

        Args:
            prompts: Liste de prompts
            system_prompt: Instructions système optionnelles
            temperature: Contrôle la créativité
            max_tokens: Nombre max de tokens par réponse

        Returns:
            Liste des textes générés
        """
        results = []
        for prompt in prompts:
            text = self.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            results.append(text)
        return results

    def is_available(self) -> bool:
        """Vérifie si Ollama est disponible."""
        try:
            self._client.list()
            return True
        except Exception:
            return False

    def list_models(self) -> list[str]:
        """Liste les modèles disponibles."""
        try:
            response = self._client.list()
            return [model["name"] for model in response.get("models", [])]
        except Exception:
            return []
