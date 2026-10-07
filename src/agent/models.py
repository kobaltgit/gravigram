import logging
from typing import List, Dict, Any
from src.database import list_db_models, add_db_model, delete_db_model

logger = logging.getLogger(__name__)

async def get_available_models() -> List[Dict[str, Any]]:
    """Динамически возвращает список моделей из базы данных (с поддержкой добавления новых)."""
    return await list_db_models()

async def register_new_model(model_id: str, name: str, description: str = "") -> Dict[str, Any]:
    """Регистрирует новую модель в системе."""
    return await add_db_model(model_id=model_id, name=name, description=description, is_custom=True)

async def remove_model(model_id: str) -> bool:
    """Удаляет модель из системы."""
    return await delete_db_model(model_id)
