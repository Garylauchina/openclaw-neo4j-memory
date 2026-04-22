from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable, List, Sequence, Tuple


@dataclass
class Entity:
    name: str


@dataclass
class Relation:
    source: str
    relation_type: str
    target: str


CAPITALIZED_PATTERN = re.compile(r"\b[A-Z][a-zA-Z0-9_-]{2,}\b")
PREFERENCE_PATTERN = re.compile(r"\b(prefers?|likes?|wants?)\b", re.IGNORECASE)
ABOUT_PATTERN = re.compile(r"\babout\b", re.IGNORECASE)


def extract_entities(content: str) -> List[Entity]:
    names = []
    seen = set()
    stopwords = {"user", "this", "that", "the"}
    for match in CAPITALIZED_PATTERN.findall(content):
        if match.lower() in stopwords:
            continue
        if match not in seen:
            seen.add(match)
            names.append(Entity(name=match))
    return names


def extract_relations(content: str, entities: Sequence[Entity]) -> List[Relation]:
    relations: List[Relation] = []
    names = [entity.name for entity in entities]

    if len(names) >= 2:
        for left, right in zip(names, names[1:]):
            if ABOUT_PATTERN.search(content):
                relations.append(Relation(source=left, relation_type="about", target=right))
            else:
                relations.append(Relation(source=left, relation_type="related_to", target=right))

    lowered = content.lower()
    for name in names:
        if PREFERENCE_PATTERN.search(lowered):
            relations.append(Relation(source="User", relation_type="preference_of", target=name))

    return relations


def extract_structure(content: str) -> Tuple[List[Entity], List[Relation]]:
    entities = extract_entities(content)
    relations = extract_relations(content, entities)
    return entities, relations


def entity_overlap(query: str, entities: Iterable[Entity]) -> int:
    lowered = query.lower()
    return sum(1 for entity in entities if entity.name.lower() in lowered)
