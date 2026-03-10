"""Agent profile generation with deterministic seeding.

Copied from CrowdMindAvis/survey_sim/agents.py to generate agent profiles
locally (same seed = same agents as the Pi).
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List


# --- Enumerations for demographic axes ---

EDUCATION_LEVELS = ["sans_diplome", "brevet", "bac", "bac+2", "bac+3", "bac+5", "doctorat"]
URBAN_RURAL = ["rural", "periurbain", "ville_moyenne", "grande_ville", "metropole"]
CLASSE_SOCIALE = ["populaire", "moyenne_inferieure", "moyenne", "moyenne_superieure", "aisee"]


@dataclass(frozen=True)
class AgentProfile:
    """Represents a single ideological agent."""

    id: int
    eco: float             # -1 (left/redistributive) … +1 (right/market)
    open: float            # -1 (conservative/identitarian) … +1 (cosmopolitan/progressive)
    trust: float           # 0 (distrust institutions) … 1 (trust institutions)
    temperament: float     # 0 (calme/réfléchi) … 1 (impulsif/tranché)
    age: int               # 18–85
    education: str         # one of EDUCATION_LEVELS
    urban_rural: str       # one of URBAN_RURAL
    classe_sociale: str    # one of CLASSE_SOCIALE
    background: str        # 1-2 sentence stable persona description


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _pick_education(rng: random.Random, classe: str, age: int) -> str:
    """Pick an education level correlated with social class and age."""
    if classe in ("aisee", "moyenne_superieure"):
        weights = [0.02, 0.03, 0.10, 0.15, 0.20, 0.35, 0.15]
    elif classe == "moyenne":
        weights = [0.05, 0.08, 0.20, 0.25, 0.22, 0.15, 0.05]
    elif classe == "moyenne_inferieure":
        weights = [0.10, 0.15, 0.30, 0.20, 0.15, 0.08, 0.02]
    else:  # populaire
        weights = [0.20, 0.25, 0.25, 0.15, 0.10, 0.04, 0.01]
    # Older generations: shift slightly toward lower education
    if age >= 60:
        weights[0] += 0.08
        weights[-1] = max(0.01, weights[-1] - 0.04)
        weights[-2] = max(0.01, weights[-2] - 0.04)
    return rng.choices(EDUCATION_LEVELS, weights=weights, k=1)[0]


def _pick_urban(rng: random.Random, classe: str) -> str:
    """Pick urban/rural setting correlated with social class."""
    if classe in ("aisee", "moyenne_superieure"):
        weights = [0.08, 0.12, 0.15, 0.30, 0.35]
    elif classe == "moyenne":
        weights = [0.12, 0.20, 0.25, 0.25, 0.18]
    else:
        weights = [0.25, 0.25, 0.22, 0.18, 0.10]
    return rng.choices(URBAN_RURAL, weights=weights, k=1)[0]


def _pick_classe(rng: random.Random, eco: float) -> str:
    """Pick social class loosely correlated with economic axis."""
    base = [0.18, 0.22, 0.28, 0.20, 0.12]
    shift = eco * 0.08
    base[0] -= shift
    base[4] += shift
    weights = [max(0.02, w) for w in base]
    return rng.choices(CLASSE_SOCIALE, weights=weights, k=1)[0]


def _build_background(
    eco: float, opn: float, trust: float, temperament: float,
    age: int, education: str, classe: str, urban: str,
) -> str:
    """Derive a 1-2 sentence stable persona description from agent axes."""
    parts: List[str] = []

    if eco < -0.4:
        parts.append("attaché à la justice sociale et à la redistribution")
    elif eco > 0.4:
        parts.append("favorable à la liberté d'entreprendre et au marché")
    else:
        parts.append("pragmatique sur les questions économiques")

    if opn > 0.4:
        parts.append("ouvert à la diversité culturelle")
    elif opn < -0.4:
        parts.append("attaché aux traditions et à l'identité nationale")

    if trust < 0.3:
        parts.append("sceptique envers les élites et les médias")
    elif trust > 0.7:
        parts.append("confiant dans le fonctionnement des institutions")

    if temperament < 0.3:
        style = "S'exprime de manière posée et nuancée."
    elif temperament > 0.7:
        style = "S'exprime de manière directe et affirmée."
    else:
        style = "S'exprime de manière équilibrée."

    sentence1 = "Citoyen " + ", ".join(parts) + "."
    return f"{sentence1} {style}"


def generate_agents(n: int, seed: int) -> List[AgentProfile]:
    """Generate *n* agents with a realistic multivariate distribution.

    Uses a seeded RNG so results are fully reproducible.
    Same seed + same n = identical agents as the Pi.
    """
    rng = random.Random(seed)

    clusters = [
        # (weight, mean_eco, mean_open, std_eco, std_open, mean_trust, std_trust)
        (0.30, -0.30,  0.30, 0.25, 0.25, 0.55, 0.20),  # centre-gauche progressiste
        (0.25,  0.30, -0.20, 0.25, 0.25, 0.50, 0.20),  # centre-droite conservateur
        (0.10, -0.70,  0.50, 0.15, 0.20, 0.25, 0.15),  # gauche radicale
        (0.10,  0.70, -0.60, 0.15, 0.20, 0.30, 0.15),  # droite radicale
        (0.25,  0.00,  0.00, 0.45, 0.45, 0.45, 0.25),  # bruit uniforme / divers
    ]

    weights = [c[0] for c in clusters]

    agents: List[AgentProfile] = []
    for i in range(n):
        cluster = rng.choices(clusters, weights=weights, k=1)[0]
        _, m_eco, m_open, s_eco, s_open, m_trust, s_trust = cluster

        eco = _clamp(rng.gauss(m_eco, s_eco), -1.0, 1.0)
        opn = _clamp(rng.gauss(m_open, s_open), -1.0, 1.0)
        trust = _clamp(rng.gauss(m_trust, s_trust), 0.0, 1.0)

        temp_base = 0.5 - trust * 0.15
        temperament = _clamp(rng.gauss(temp_base, 0.22), 0.0, 1.0)

        age_base = 45 - opn * 8
        age = int(_clamp(rng.gauss(age_base, 15), 18, 85))

        classe = _pick_classe(rng, eco)
        education = _pick_education(rng, classe, age)
        urban = _pick_urban(rng, classe)

        bg = _build_background(eco, opn, trust, temperament, age, education, classe, urban)

        agents.append(AgentProfile(
            id=i,
            eco=round(eco, 3),
            open=round(opn, 3),
            trust=round(trust, 3),
            temperament=round(temperament, 3),
            age=age,
            education=education,
            urban_rural=urban,
            classe_sociale=classe,
            background=bg,
        ))

    return agents
