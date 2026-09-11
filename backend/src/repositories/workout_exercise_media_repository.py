from sqlalchemy import select
from sqlalchemy.orm import Session

from src.domain.models import WorkoutExerciseMedia


class WorkoutExerciseMediaRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_import_and_index(self, import_id: str, exercise_index: int) -> WorkoutExerciseMedia | None:
        return self.db.scalar(
            select(WorkoutExerciseMedia).where(
                WorkoutExerciseMedia.import_id == import_id,
                WorkoutExerciseMedia.exercise_index == exercise_index,
            )
        )

    def upsert_verified_media(
        self,
        *,
        import_id: str,
        exercise_index: int,
        template_id: str | None,
        source: str,
        image_url: str | None,
        local_file_name: str | None,
        alt_text: str,
        is_verified: bool,
    ) -> WorkoutExerciseMedia:
        media = self.get_by_import_and_index(import_id, exercise_index)
        if media is None:
            media = WorkoutExerciseMedia(
                import_id=import_id,
                exercise_index=exercise_index,
                template_id=template_id,
                source=source,
                image_url=image_url,
                local_file_name=local_file_name,
                alt_text=alt_text,
                is_verified=is_verified,
            )
            self.db.add(media)
        else:
            media.template_id = template_id
            media.source = source
            media.image_url = image_url
            media.local_file_name = local_file_name
            media.alt_text = alt_text
            media.is_verified = is_verified
        self.db.commit()
        self.db.refresh(media)
        return media

    def get_media_for_import_exercises(self, import_id: str) -> list[WorkoutExerciseMedia]:
        return list(
            self.db.scalars(
                select(WorkoutExerciseMedia)
                .where(WorkoutExerciseMedia.import_id == import_id)
                .order_by(WorkoutExerciseMedia.exercise_index)
            ).all()
        )
