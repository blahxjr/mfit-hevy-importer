from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.models import ExerciseMapping, ExerciseTemplate, NormalizedExercise, SourceExercise, SourceWorkout
from src.parsers.exercise_mapper import ExerciseMapper, MappingCandidate


class ExerciseMappingAgent:
    def __init__(self, db: Session):
        self.db = db

    def _confirmed(self):
        rows = self.db.scalars(select(ExerciseMapping).where(ExerciseMapping.confirmed_by_user.is_(True))).all()
        return {
            x.source_name: MappingCandidate(
                x.template_id, x.template.title if x.template else None, x.method, x.confidence, False
            )
            for x in rows
        }

    def map_import(self, import_id):
        rows = self.db.scalars(
            select(NormalizedExercise)
            .join(SourceExercise)
            .join(SourceWorkout)
            .where(SourceWorkout.import_id == import_id)
        ).all()
        mapper = ExerciseMapper(
            [{"id": x.id, "title": x.title} for x in self.db.scalars(select(ExerciseTemplate)).all()]
        )
        mappings_by_source = {
            mapping.source_name: mapping for mapping in self.db.scalars(select(ExerciseMapping)).all()
        }
        confirmed = self._confirmed()
        output = []
        for row in rows:
            source = row.source_exercise
            c = mapper.map_exercise(source.source_name, confirmed)
            item = mappings_by_source.get(source.source_name)
            if item is None:
                item = ExerciseMapping(source_name=source.source_name, method="manual")
                mappings_by_source[source.source_name] = item
            item.normalized_name = mapper._normalize_name(source.source_name)
            item.template_id = c.template_id
            item.confidence = c.confidence
            if not item.confirmed_by_user:
                item.method = c.method
            self.db.add(item)
            output.append(
                {
                    "source_exercise_id": source.id,
                    "source_name": source.source_name,
                    "template_id": c.template_id,
                    "template_title": c.template_title,
                    "method": c.method,
                    "confidence": c.confidence,
                    "needs_review": c.needs_review,
                }
            )
        self.db.commit()
        return {
            "import_id": import_id,
            "mapped_count": len(output),
            "needs_review_count": sum(x["needs_review"] for x in output),
            "no_match_count": sum(x["template_id"] is None for x in output),
            "mappings": output,
        }

    def confirm_mapping(self, mapping_id, template_id):
        mapping = self.db.get(ExerciseMapping, mapping_id)
        if not mapping or not self.db.get(ExerciseTemplate, template_id):
            return {"error": "Mapping or template not found"}
        mapping.template_id = template_id
        mapping.method = "manual"
        mapping.confirmed_by_user = True
        self.db.commit()
        return {"success": True, "mapping_id": mapping_id, "template_id": template_id}
