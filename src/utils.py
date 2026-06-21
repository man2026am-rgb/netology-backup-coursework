"""
Вспомогательные функции для пользовательского интерфейса и логирования.
"""
import os
import sys
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable
from pathlib import Path

from src.config import LOGS_DIR, CACHE_DIR, CACHE_FILE, CACHE_ENABLED, CACHE_TTL


# ============================================================
# НАСТРОЙКА ЛОГГЕРА
# ============================================================

def setup_logger(name: str = "backup", log_dir: Path = LOGS_DIR) -> logging.Logger:
    """
    Настраивает логгер с выводом в файл и консоль.

    Args:
        name: Имя логгера.
        log_dir: Директория для сохранения логов.

    Returns:
        logging.Logger: Настроенный логгер.
    """
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    log_file = log_dir / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


# Создаем логгер
_logger = None


def _get_logger() -> logging.Logger:
    """Возвращает логгер, создавая его при первом вызове."""
    global _logger
    if _logger is None:
        _logger = setup_logger()
    return _logger


# ============================================================
# ФУНКЦИИ ЛОГИРОВАНИЯ
# ============================================================

def log_debug(message: str) -> None:
    """Логирует отладочное сообщение."""
    try:
        _get_logger().debug(message)
    except Exception:
        pass


def log_info(message: str) -> None:
    """Логирует информационное сообщение."""
    try:
        _get_logger().info(message)
    except Exception:
        pass


def log_warning(message: str) -> None:
    """Логирует предупреждение."""
    try:
        _get_logger().warning(message)
    except Exception:
        pass


def log_error(message: str) -> None:
    """Логирует сообщение об ошибке."""
    try:
        _get_logger().error(message)
    except Exception:
        pass


def log_success(message: str) -> None:
    """Логирует сообщение об успешном действии."""
    try:
        _get_logger().info(f"✅ {message}")
    except Exception:
        pass


def log_step(step: str, message: str = "") -> None:
    """Логирует шаг процесса."""
    try:
        _get_logger().info(f"▶️ {step}: {message}" if message else f"▶️ {step}")
    except Exception:
        pass


# ============================================================
# КЭШИРОВАНИЕ API ЗАПРОСОВ
# ============================================================

class APICache:
    """
    Класс для кэширования результатов API запросов.
    """

    def __init__(self, cache_file: Path = CACHE_FILE):
        self.cache_file = cache_file
        self.cache: Dict[str, Any] = {}
        self._load_cache()

    def _load_cache(self) -> None:
        """Загружает кэш из файла."""
        if not CACHE_ENABLED:
            return
        
        if self.cache_file.exists():
            try:
                if self.cache_file.stat().st_size == 0:
                    log_warning("Файл кэша пуст, создаем новый")
                    self.cache = {}
                    return
                    
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
                log_debug(f"Загружен кэш из {self.cache_file}")
            except json.JSONDecodeError as e:
                log_warning(f"Файл кэша поврежден, создаем новый: {e}")
                self.cache = {}
                self._save_cache()
            except Exception as e:
                log_warning(f"Не удалось загрузить кэш: {e}")
                self.cache = {}

    def _save_cache(self) -> None:
        """Сохраняет кэш в файл."""
        if not CACHE_ENABLED:
            return
        
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log_warning(f"Не удалось сохранить кэш: {e}")

    def get(self, key: str) -> Optional[Any]:
        """Получает значение из кэша по ключу."""
        if not CACHE_ENABLED:
            return None

        entry = self.cache.get(key)
        if entry is None:
            return None

        timestamp, data = entry
        if (datetime.now().timestamp() - timestamp) > CACHE_TTL:
            del self.cache[key]
            self._save_cache()
            return None

        log_debug(f"Кэш HIT: {key[:50]}...")
        return data

    def set(self, key: str, value: Any) -> None:
        """Сохраняет значение в кэш."""
        if not CACHE_ENABLED:
            return

        self.cache[key] = (datetime.now().timestamp(), value)
        self._save_cache()
        log_debug(f"Кэш SET: {key[:50]}...")

    def clear(self) -> None:
        """Очищает весь кэш."""
        self.cache = {}
        self._save_cache()
        log_info("Кэш очищен")


api_cache = APICache()


# ============================================================
# ВЫВОД В КОНСОЛЬ
# ============================================================

def clear_screen() -> None:
    """Очищает экран терминала."""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header(text: str, char: str = "=", length: int = 60) -> None:
    """Выводит заголовок."""
    print("\n" + char * length)
    print(f"📸 {text}")
    print(char * length)


def print_subheader(text: str, char: str = "-", length: int = 40) -> None:
    """Выводит подзаголовок."""
    print(f"\n{text}")
    print(char * length)


def print_success(text: str) -> None:
    """Выводит сообщение об успехе."""
    print(f"✅ {text}")
    log_success(text)


def print_error(text: str) -> None:
    """Выводит сообщение об ошибке."""
    print(f"❌ {text}")
    log_error(text)


def print_warning(text: str) -> None:
    """Выводит предупреждение."""
    print(f"⚠️ {text}")
    log_warning(text)


def print_info(text: str) -> None:
    """Выводит информационное сообщение."""
    print(f"ℹ️ {text}")
    log_info(text)


def print_separator(char: str = "=", length: int = 50) -> None:
    """Выводит разделительную линию."""
    print(char * length)


# ============================================================
# ВВОД ДАННЫХ
# ============================================================

def get_user_input(
    prompt: str,
    validator: Optional[Callable[[str], bool]] = None,
    error_message: str = "Некорректный ввод",
    default: Optional[str] = None,
    required: bool = True
) -> Optional[str]:
    """Получает ввод от пользователя с валидацией."""
    while True:
        full_prompt = f"{prompt} (Enter для '{default}'): " if default else f"{prompt}: "
        value = input(full_prompt).strip()

        if not value and default:
            value = default

        if not value and required:
            print_error("Это поле обязательно для заполнения")
            continue

        if not value and not required:
            return None

        if validator and not validator(value):
            print_error(error_message)
            continue

        return value


def get_yes_no(prompt: str, default: bool = True) -> bool:
    """Получает ответ Да/Нет от пользователя."""
    yes_options = {'y', 'yes', 'да', 'д', '1'}
    no_options = {'n', 'no', 'нет', 'н', '0'}
    default_text = "Y/n" if default else "y/N"

    while True:
        response = input(f"{prompt} [{default_text}]: ").strip().lower()
        if not response:
            return default
        if response in yes_options:
            return True
        if response in no_options:
            return False
        print_error("Введите 'y' (да) или 'n' (нет)")


def get_number(
    prompt: str,
    min_val: Optional[int] = None,
    max_val: Optional[int] = None,
    default: Optional[int] = None
) -> Optional[int]:
    """Получает число от пользователя."""
    while True:
        default_text = f" (по умолчанию {default})" if default is not None else ""
        value = input(f"{prompt}{default_text}: ").strip()

        if not value and default is not None:
            return default

        if not value:
            print_error("Введите число")
            continue

        try:
            num = int(value)
            if min_val is not None and num < min_val:
                print_error(f"Число должно быть не меньше {min_val}")
                continue
            if max_val is not None and num > max_val:
                print_error(f"Число должно быть не больше {max_val}")
                continue
            return num
        except ValueError:
            print_error("Введите целое число")


def get_choice(
    prompt: str,
    options: List[str],
    default: Optional[str] = None
) -> Optional[str]:
    """Позволяет пользователю выбрать вариант из списка."""
    while True:
        print(f"\n{prompt}")
        for i, option in enumerate(options, 1):
            marker = " (по умолчанию)" if option == default else ""
            print(f"  {i}. {option}{marker}")

        choice = input(f"\nВаш выбор (1-{len(options)}): ").strip()

        if not choice and default:
            return default

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                return options[idx]
            print_error(f"Введите число от 1 до {len(options)}")
        except ValueError:
            for option in options:
                if option.lower().startswith(choice.lower()):
                    return option
            print_error(f"Введите число от 1 до {len(options)} или название варианта")


# ============================================================
# ВАЛИДАТОРЫ
# ============================================================

def validate_text(text: str) -> bool:
    """Проверяет текст для изображений кошек."""
    if not text or len(text.strip()) == 0:
        print_error("Текст не может быть пустым")
        return False

    if len(text) > 50:
        print_error("Текст слишком длинный (максимум 50 символов)")
        return False

    invalid_chars = {'\\', '/', ':', '*', '?', '"', '<', '>', '|'}
    if any(c in text for c in invalid_chars):
        print_error("Текст содержит недопустимые символы")
        return False

    return True


def validate_breed(breed: str, breeds_dict: Dict[str, Any]) -> bool:
    """Проверяет существование породы собаки."""
    if not breed:
        print_error("Название породы не может быть пустым")
        return False

    if breed not in breeds_dict:
        print_error(f"Порода '{breed}' не найдена")
        similar = [b for b in list(breeds_dict.keys())[:10] if breed in b or b in breed]
        if similar:
            print_info(f"Возможно, вы имели в виду: {', '.join(similar[:5])}")
        return False

    return True


# ============================================================
# ФОРМАТИРОВАНИЕ
# ============================================================

def format_size(size_bytes: int) -> str:
    """Форматирует размер в байтах в читаемый вид."""
    units = ['Б', 'КБ', 'МБ', 'ГБ', 'ТБ']
    size = float(size_bytes)

    for unit in units:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0

    return f"{size:.1f} ТБ"


def format_timestamp(timestamp: str) -> str:
    """Форматирует временную метку в читаемый вид."""
    try:
        dt = datetime.fromisoformat(timestamp)
        return dt.strftime('%d.%m.%Y %H:%M:%S')
    except (ValueError, TypeError):
        return timestamp


def get_timestamp() -> str:
    """Возвращает текущую временную метку в ISO формате."""
    return datetime.now().isoformat()


def safe_filename(text: str, max_length: int = 30) -> str:
    """Преобразует текст в безопасное имя файла."""
    safe = ''.join(c for c in text if c.isalnum() or c in (' ', '-', '_'))
    safe = safe.replace(' ', '_')
    if len(safe) > max_length:
        safe = safe[:max_length]
    return safe


# ============================================================
# ФОРМАТИРОВАНИЕ РЕЗУЛЬТАТА (ДОБАВЛЕНА НОВАЯ ФУНКЦИЯ)
# ============================================================

def format_result_preview(result: Dict[str, Any]) -> str:
    """
    Форматирует результат для отображения в консоли.

    Args:
        result: Словарь с результатом загрузки.

    Returns:
        str: Отформатированная строка для вывода.
    """
    if result.get('success'):
        name = result.get('file_name', 'unknown')
        size = result.get('size', 0)
        return f"✅ {name} ({format_size(size)})"
    else:
        error = result.get('error', 'Неизвестная ошибка')
        return f"❌ {error[:50]}"


# ============================================================
# СПРАВКА
# ============================================================

def print_help() -> None:
    """Выводит справку по использованию программы."""
    clear_screen()
    print_header("СПРАВКА ПО ПРОГРАММЕ")

    print("\n📖 ОБЩЕЕ ОПИСАНИЕ")
    print_separator("-")
    print("Программа для резервного копирования изображений")
    print("из API (cataas.com и dog.ceo) в облачное хранилище Яндекс.Диск.")

    print("\n📋 ДОСТУПНЫЕ ФУНКЦИИ")
    print_separator("-")
    print("1. Бэкап кошек (cataas.com)")
    print("   - Загружает изображения кошек с настраиваемым текстом")
    print("   - Можно выбрать количество изображений (1-10)")
    print("   - Доступны предустановки: default, large, funny, elegant, minimal")
    print("   - Поддерживается кэширование API запросов")
    print("\n2. Бэкап собак (dog.ceo)")
    print("   - Загружает изображения всех пород или конкретной")
    print("   - Автоматически обрабатывает подпороды")
    print("\n3. Просмотр результатов")
    print("   - Показывает статистику и список загруженных файлов")
    print("   - JSON файл сохраняется в data/backup_results.json")

    print("\n📁 СТРУКТУРА ПАПОК НА ЯНДЕКС.ДИСКЕ")
    print_separator("-")
    group = os.getenv('GROUP_NAME', 'ваша_группа')
    print(f"  /{group}/")
    print("    ├── Cats/        # Изображения кошек")
    print("    └── Dogs/        # Изображения собак")
    print("        ├── breed1/  # Папка для каждой породы")
    print("        └── breed2/")

    print("\n📄 ФОРМАТ РЕЗУЛЬТАТОВ (JSON)")
    print_separator("-")
    print("""  {
    'timestamp': '2024-01-01T12:00:00',
    'group_name': 'ваша_группа',
    'stats': {'successful': 5, 'failed': 0, ...},
    'files': [...]
  }""")

    print("\n⚙️ ТРЕБОВАНИЯ")
    print_separator("-")
    print("  - Файл .env с токеном Яндекс.Диска")
    print("  - Переменная GROUP_NAME в .env")
    print("  - Интернет-соединение")

    print("\n📝 ЛОГИРОВАНИЕ")
    print_separator("-")
    print("  - Логи сохраняются в папку logs/")
    print("  - Формат: backup_YYYYMMDD.log")
    print("  - Содержит все этапы работы программы")
    print("  - Поддерживается кэширование API запросов")

    print("\n" + "=" * 60)
    input("Нажмите Enter для возврата в меню...")