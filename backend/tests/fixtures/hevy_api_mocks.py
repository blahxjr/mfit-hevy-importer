"""
Fixtures para testes da API Hevy
Responses capturadas durante Fase 0 para testes sem chamar API real
"""

# Exemplo de response de exercise_templates
MOCK_EXERCISE_TEMPLATES = {
    "page": 1,
    "page_count": 1,
    "exercise_templates": [
        {
            "id": "template-001",
            "title": "Supino Reto",
            "type": "strength",
            "primary_muscle_group": "chest",
            "secondary_muscle_groups": ["triceps", "shoulders"],
            "equipment": "barbell",
            "is_custom": False,
        },
        {
            "id": "template-002",
            "title": "Agachamento",
            "type": "strength",
            "primary_muscle_group": "quadriceps",
            "secondary_muscle_groups": ["glutes", "hamstrings"],
            "equipment": "barbell",
            "is_custom": False,
        },
        {
            "id": "template-003",
            "title": "Rosca Direta",
            "type": "strength",
            "primary_muscle_group": "biceps",
            "secondary_muscle_groups": [],
            "equipment": "barbell",
            "is_custom": False,
        },
    ]
}

# Exemplo de response de routine_folders
MOCK_ROUTINE_FOLDERS = {
    "page": 1,
    "page_count": 1,
    "routine_folders": [
        {
            "id": 1,
            "title": "Treinos de Força",
            "index": 0,
            "created_at": "2026-09-01T00:00:00Z",
            "updated_at": "2026-09-01T00:00:00Z",
        },
        {
            "id": 2,
            "title": "Treinos de Hipertrofia",
            "index": 1,
            "created_at": "2026-09-01T00:00:00Z",
            "updated_at": "2026-09-01T00:00:00Z",
        },
    ]
}

# Exemplo de response de routines
MOCK_ROUTINES = {
    "page": 1,
    "page_count": 1,
    "routines": [
        {
            "id": "routine-001",
            "title": "Rotina A - Peito e Tríceps",
            "folder_id": 1,
            "created_at": "2026-09-01T00:00:00Z",
            "updated_at": "2026-09-01T00:00:00Z",
            "exercises": [
                {
                    "order": 1,
                    "template_id": "template-001",
                    "notes": "Aquecimento",
                    "sets": [
                        {
                            "reps": 8,
                            "weight": 80,
                            "weight_unit": "kg",
                            "rest": 120,
                        }
                    ],
                }
            ],
        }
    ]
}


def get_mock_templates():
    """Retorna mock de templates"""
    return MOCK_EXERCISE_TEMPLATES


def get_mock_folders():
    """Retorna mock de folders"""
    return MOCK_ROUTINE_FOLDERS


def get_mock_routines():
    """Retorna mock de routines"""
    return MOCK_ROUTINES
