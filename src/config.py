"""
Модуль конфигурации приложения.

Содержит все настройки: переменные окружения, API эндпоинты,
пути к файлам и параметры изображений.
"""
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

from dotenv import load_dotenv


# ============================================================
# БАЗОВЫЕ НАСТРОЙКИ
# ============================================================

BASE_DIR: Path = Path(__file__).resolve().parent.parent
"""Корневая директория проекта."""

load_dotenv(BASE_DIR / '.env')


# ============================================================
# ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ
# ============================================================

YANDEX_DISK_TOKEN: Optional[str] = os.getenv('YANDEX_DISK_TOKEN')
"""OAuth токен для доступа к Яндекс.Диску."""

GROUP_NAME: str = os.getenv('GROUP_NAME', 'default_group')
"""Название группы для создания папок на диске."""

if not YANDEX_DISK_TOKEN:
    raise ValueError(
        "❌ YANDEX_DISK_TOKEN не найден в .env файле!\n"
        "Пожалуйста, создайте файл .env и добавьте:\n"
        "YANDEX_DISK_TOKEN=ваш_токен_с_полигона"
    )


# ============================================================
# API КОНФИГУРАЦИЯ
# ============================================================

CAT_API_BASE_URL: str = 'https://cataas.com'
CAT_API_ENDPOINT: str = '/cat/says/{text}'

DOG_API_BASE_URL: str = 'https://dog.ceo/api'
DOG_API_BREEDS_LIST: str = '/breeds/list/all'
DOG_API_RANDOM_IMAGE: str = '/breed/{breed}/images/random'


# ============================================================
# ЯНДЕКС.ДИСК API
# ============================================================

YANDEX_DISK_BASE_URL: str = 'https://cloud-api.yandex.net/v1/disk'
YANDEX_DISK_RESOURCES: str = '/resources'
YANDEX_DISK_UPLOAD: str = '/resources/upload'


# ============================================================
# ПУТИ И ПАПКИ
# ============================================================

DATA_DIR: Path = BASE_DIR / 'data'
"""Директория для хранения результатов."""

RESULTS_FILE: Path = DATA_DIR / 'backup_results.json'
"""Путь к файлу с результатами бэкапа."""

LOGS_DIR: Path = BASE_DIR / 'logs'
"""Директория для логов."""

CACHE_DIR: Path = BASE_DIR / 'cache'
"""Директория для кэша API запросов."""

CACHE_FILE: Path = CACHE_DIR / 'api_cache.json'
"""Путь к файлу кэша."""

YANDEX_DISK_FOLDERS: Dict[str, str] = {
    'cats': f'/{GROUP_NAME}/Cats',
    'dogs': f'/{GROUP_NAME}/Dogs'
}
"""Имена папок на Яндекс.Диске для разных типов бэкапа."""

MAX_IMAGES_CATS: int = 10
"""Максимальное количество изображений кошек для загрузки."""

MAX_IMAGES_DOGS: int = 5
"""Максимальное количество изображений собак для загрузки."""

# ============================================================
# НАСТРОЙКИ КЭШИРОВАНИЯ
# ============================================================

CACHE_ENABLED: bool = True
"""Включить кэширование API запросов."""

CACHE_TTL: int = 3600
"""Время жизни кэша в секундах (1 час)."""


# ============================================================
# ПАРАМЕТРЫ ИЗОБРАЖЕНИЙ КОШЕК
# ============================================================

CAT_DEFAULT_PARAMS: Dict[str, Any] = {
    'size': 300,
    'color': 'red',
    'fontSize': 50,
    'font': 'Impact',
    'type': 'jpg'
}

CAT_ALLOWED_COLORS: List[str] = ['red', 'green', 'blue', 'yellow', 'white', 'black']
CAT_ALLOWED_FONTS: List[str] = ['Impact', 'Arial', 'Comic Sans MS', 'Georgia', 'Verdana']
CAT_ALLOWED_FILTERS: List[str] = ['blur', 'mono', 'sepia', 'negative', 'edge', 'paint']


# ============================================================
# СОЗДАНИЕ ДИРЕКТОРИЙ
# ============================================================

def _ensure_directories() -> None:
    """Создает необходимые директории, если они не существуют."""
    for directory in [DATA_DIR, LOGS_DIR, CACHE_DIR]:
        if not directory.exists():
            directory.mkdir(parents=True)


_ensure_directories()


# ============================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================

def get_cat_url(text: str) -> str:
    """Формирует URL для получения изображения кота с текстом."""
    from urllib.parse import quote
    encoded_text = quote(text)
    endpoint = CAT_API_ENDPOINT.format(text=encoded_text)
    return f"{CAT_API_BASE_URL}{endpoint}"


def get_dog_url(breed: str) -> str:
    """Формирует URL для получения случайного изображения собаки."""
    endpoint = DOG_API_RANDOM_IMAGE.format(breed=breed)
    return f"{DOG_API_BASE_URL}{endpoint}"


def get_dog_breeds_url() -> str:
    """Формирует URL для получения списка пород собак."""
    return f"{DOG_API_BASE_URL}{DOG_API_BREEDS_LIST}"


def get_yandex_folder_path(backup_type: str) -> str:
    """Возвращает путь к папке на Яндекс.Диске для указанного типа бэкапа."""
    return YANDEX_DISK_FOLDERS.get(backup_type, f'/{GROUP_NAME}/Backup')


def print_config() -> None:
    """Выводит текущую конфигурацию приложения для отладки."""
    print("\n" + "=" * 50)
    print("📋 КОНФИГУРАЦИЯ ПРИЛОЖЕНИЯ")
    print("=" * 50)
    print(f"Группа: {GROUP_NAME}")
    print(f"Токен Яндекс.Диска: {'✅ Установлен' if YANDEX_DISK_TOKEN else '❌ Отсутствует'}")
    print(f"Папка результатов: {RESULTS_FILE}")
    print(f"Папка для кошек: {YANDEX_DISK_FOLDERS['cats']}")
    print(f"Папка для собак: {YANDEX_DISK_FOLDERS['dogs']}")
    print(f"Кэширование: {'✅ Включено' if CACHE_ENABLED else '❌ Отключено'}")
    print(f"Директория логов: {LOGS_DIR}")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    print_config()