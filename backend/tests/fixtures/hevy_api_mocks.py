"""
Fixtures para testes da API Hevy
Responses capturadas durante Fase 0 para testes sem chamar API real
"""

# Exemplo de response de exercise_templates
MOCK_EXERCISE_TEMPLATES = {
    "data": [
        {
            "id": "template-001",
            "title": "Supino Reto",
            "category": "strength",
            "muscle_groups": ["chest", "triceps", "shoulders"],
            "equipment": ["barbell", "bench"],
        },
        {
            "id": "template-002",
            "title": "Agachamento",
            "category": "strength",
            "muscle_groups": ["quadriceps", "glutes", "hamstrings"],
            "equipment": ["barbell", "rack"],
        },
        {
            "id": "template-003",
            "title": "Rosca Direta",
            "category": "strength",
            "muscle_groups": ["biceps"],
            "equipment": ["barbell"],
        },
    ]
}

# Exemplo de response de routine_folders
MOCK_ROUTINE_FOLDERS = {
    "data": [
        {
            "id": "folder-001",
            "name": "Treinos de Força",
        },
        {
            "id": "folder-002",
            "name": "Treinos de Hipertrofia",
        },
    ]
}

# Exemplo de response de routines
MOCK_ROUTINES = {
    "data": [
        {
            "id": "routine-001",
            "name": "Rotina A - Peito e Tríceps",
            "folder_id": "folder-001",
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
