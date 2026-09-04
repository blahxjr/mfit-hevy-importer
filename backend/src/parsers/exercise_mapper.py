import unicodedata
from dataclasses import dataclass

from rapidfuzz import fuzz, process


@dataclass
class MappingCandidate:
    template_id: str | None
    template_title: str | None
    method: str
    confidence: float
    needs_review: bool


class ExerciseMapper:
    aliases = {
        "puxada articulada neutra": "lat pulldown",
        "crucifixo inverso peck deck": "reverse pec deck",
        "cadeira extensora": "leg extension",
        "cadeira flexora": "leg curl",
        "supino reto barra": "bench press",
        "agachamento livre": "squat",
        "levantamento terra": "deadlift",
    }

    def __init__(self, templates):
        self.templates = templates
        self.by_normalized = {self._normalize_name(t["title"]): t for t in templates}
        self.titles = list(self.by_normalized)

    def _normalize_name(self, name):
        return " ".join(
            "".join(
                c
                for c in unicodedata.normalize("NFKD", name.lower())
                if not unicodedata.combining(c) and (c.isalnum() or c.isspace())
            ).split()
        )

    def map_exercise(self, source, confirmed):
        name = self._normalize_name(source)
        if source in confirmed:
            item = confirmed[source]
            return MappingCandidate(item.template_id, item.template_title, "memory", item.confidence, False)
        method = (
            "exact"
            if name in self.by_normalized
            else "alias"
            if self.aliases.get(name) in self.by_normalized
            else "fuzzy"
        )
        target = name if method == "exact" else self.aliases[name] if method == "alias" else None
        if target is None and self.titles:
            match = process.extractOne(name, self.titles, scorer=fuzz.WRatio)
            target, score = match[0], match[1]
            if score < 75:
                return MappingCandidate(None, None, "manual", 0, True)
            confidence = score / 100
        elif target is not None:
            confidence = 1 if method == "exact" else 0.95
        else:
            return MappingCandidate(None, None, "manual", 0, True)
        template = self.by_normalized[target]
        return MappingCandidate(template["id"], template["title"], method, confidence, confidence < 0.92)

    def get_alternatives(self, source, limit=5):
        return [
            MappingCandidate(self.by_normalized[t]["id"], self.by_normalized[t]["title"], "fuzzy", s / 100, True)
            for t, s, _ in process.extract(self._normalize_name(source), self.titles, scorer=fuzz.WRatio, limit=limit)
        ]
