"""Client Groq pour la génération de textes via LLM cloud."""

from dataclasses import dataclass

from groq import Groq


@dataclass
class GroqConfig:
    """Configuration pour le client Groq."""

    api_key: str = ""
    model: str = "llama-3.3-70b-versatile"
    timeout: float = 60.0


class GroqClient:
    """Client pour interagir avec l'API Groq."""

    def __init__(self, config: GroqConfig | None = None):
        self._config = config or GroqConfig()
        self._client = Groq(api_key=self._config.api_key)

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

        response = self._client.chat.completions.create(
            model=self._config.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return response.choices[0].message.content or ""

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
        """Vérifie si l'API Groq est disponible."""
        try:
            self._client.models.list()
            return True
        except Exception:
            return False

    def list_models(self) -> list[str]:
        """Liste les modèles disponibles."""
        try:
            response = self._client.models.list()
            return [model.id for model in response.data]
        except Exception:
            return []
