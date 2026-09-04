"""Parser determinístico para PDFs de prescrição exportados pelo MFIT."""

import re
from dataclasses import dataclass, field
from pathlib import Path

import pymupdf


@dataclass
class ParsedExercise:
    source_name: str
    order: int
    sets_raw: str | None = None
    reps_raw: str | None = None
    load_raw: str | None = None
    rest_raw: str | None = None
    notes_raw: str | None = None
    techniques: list[str] = field(default_factory=list)
    group_id: int | None = None
    source_location: str = ""
    confidence: float = 0.0
    warnings: list[str] = field(default_factory=list)


@dataclass
class ParsedWorkout:
    source_name: str
    order: int
    exercises: list[ParsedExercise] = field(default_factory=list)


@dataclass
class ParsedMfitPDF:
    filename: str
    pages: int
    workouts: list[ParsedWorkout]
    warnings: list[str] = field(default_factory=list)


class MFITParser:
    workout_pattern = re.compile(r"^([A-Z])\s*[-–—]\s*(.+)$")
    label_pattern = re.compile(r"^(Séries|Carga|Intervalo):\s*(.*)$", re.IGNORECASE)

    def __init__(self, pdf_path: str | Path):
        self.pdf_path = Path(pdf_path)
        self.filename = self.pdf_path.name

    def parse(self) -> ParsedMfitPDF:
        if not self.pdf_path.is_file():
            raise FileNotFoundError(self.pdf_path)
        workouts: list[ParsedWorkout] = []
        warnings: list[str] = []
        group_id: int | None = None
        next_group = 1
        document = pymupdf.open(self.pdf_path)
        pages = document.page_count
        try:
            for page_number, page in enumerate(document, 1):
                lines = [line.strip() for line in page.get_text("text").splitlines() if line.strip()]
                workout, index = self._workout_from_page(lines, len(workouts))
                if workout is None:
                    warnings.append(f"Página {page_number}: treino não identificado")
                    continue
                workouts.append(workout)
                while index < len(lines):
                    line = lines[index]
                    if "Exercícios combinados" in line:
                        group_id, next_group = next_group, next_group + 1
                        index += 1
                        continue
                    if line.lower().startswith("altere esses exercícios"):
                        index += 1
                        continue
                    if self.label_pattern.match(line) or line.startswith(("Rotina:", "Hipertrofia", "Adaptação")):
                        index += 1
                        continue
                    exercise, index = self._read_exercise(lines, index, page_number, len(workout.exercises), group_id)
                    if exercise:
                        workout.exercises.append(exercise)
                    else:
                        index += 1
        finally:
            document.close()
        return ParsedMfitPDF(self.filename, pages, workouts, warnings)

    def _workout_from_page(self, lines: list[str], order: int) -> tuple[ParsedWorkout | None, int]:
        for index, line in enumerate(lines):
            match = self.workout_pattern.match(line)
            if match:
                return ParsedWorkout(f"{match.group(1)} - {match.group(2)}", order), index + 1
        return None, len(lines)

    def _read_exercise(self, lines, index, page, order, group_id):
        name_parts = [lines[index]]
        index += 1
        while index < len(lines) and not lines[index].lower().startswith("séries:"):
            if self.workout_pattern.match(lines[index]) or "Exercícios combinados" in lines[index]:
                return None, index
            name_parts.append(lines[index])
            index += 1
        if index >= len(lines):
            return None, index
        sets = lines[index].split(":", 1)[1].strip()
        index += 1
        values, notes = {"Carga": None, "Intervalo": None}, [sets]
        current = "Séries"
        while (
            index < len(lines)
            and not self.workout_pattern.match(lines[index])
            and "Exercícios combinados" not in lines[index]
        ):
            if index + 1 < len(lines) and lines[index + 1].lower().startswith("séries:"):
                break
            label = self.label_pattern.match(lines[index])
            if label:
                current, value = label.group(1).title(), label.group(2)
                if current in values:
                    values[current] = value
                else:
                    notes.append(value)
            elif current == "Séries":
                notes.append(lines[index])
            else:
                notes.append(lines[index])
            index += 1
        raw_notes = " ".join(filter(None, notes))
        reps = self._reps(sets)
        return (
            ParsedExercise(
                " ".join(name_parts),
                order,
                sets,
                reps,
                values["Carga"],
                values["Intervalo"],
                raw_notes,
                self._techniques(raw_notes),
                group_id,
                f"page {page}",
                0.9,
            ),
            index,
        )

    @staticmethod
    def _reps(value: str) -> str | None:
        match = re.search(r"(\d+)\s*[xX]\s*(\d+(?:\s*-\s*\d+)?)", value)
        if match:
            return match.group(2).replace(" ", "")
        if re.search(r"\d+\s*(?:s|seg|minutos?)", value, re.I):
            return value
        return None

    @staticmethod
    def _techniques(text: str) -> list[str]:
        lower = text.lower()
        rules = {
            "dropset": ("dropset", "drop-set", "diminui"),
            "isometria": ("isometria", "isométrica"),
            "rest-pause": ("rest-pause", "rest pause"),
            "8x8": ("8x8",),
            "serie_por_tempo": ("minutos", "60s", "50s"),
        }
        return [name for name, markers in rules.items() if any(marker in lower for marker in markers)]
