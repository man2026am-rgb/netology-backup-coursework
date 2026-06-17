"""
Главный модуль программы резервного копирования
"""
import sys
import os
import json
from datetime import datetime

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.backup_manager import BackupManager
from src.image_fetcher import ImageFetcher
from src.config import GROUP_NAME, RESULTS_FILE, YANDEX_DISK_FOLDERS
from src.utils import (
    clear_screen,
    print_header,
    print_subheader,
    print_success,
    print_error,
    print_warning,
    print_info,
    print_separator,
    get_user_input,
    get_yes_no,
    get_number,
    get_choice,
    validate_text,
    validate_breed,
    print_help,
    format_size,
    format_timestamp,
    format_result_preview
)


# ============================================
# ФУНКЦИИ ДЛЯ РАБОТЫ С ПОЛЬЗОВАТЕЛЕМ
# ============================================

def show_main_menu():
    """Показывает главное меню и возвращает выбор пользователя."""
    print_header(f"Программа резервного копирования", "=")
    print(f"👤 Группа: {GROUP_NAME}")
    print(f"📁 Папка для кошек: {YANDEX_DISK_FOLDERS['cats']}")
    print(f"📁 Папка для собак: {YANDEX_DISK_FOLDERS['dogs']}")
    print_separator("-")
    
    options = [
        "🐱 Бэкап кошек (cataas.com)",
        "🐱 Бэкап кошек (расширенный, с пресетами)",
        "🐶 Бэкап собак (все породы)",
        "🐶 Бэкап собаки (конкретная порода)",
        "📊 Показать результаты",
        "❓ Помощь / Справка",
        "🚪 Выход"
    ]
    
    return get_choice("\nВыберите действие:", options)


def get_cat_input():
    """
    Получает от пользователя параметры для бэкапа кошек.
    
    Returns:
        tuple: (text, count) или (None, None) если отмена
    """
    print_subheader("🐱 Бэкап кошек", "-")
    
    # Ввод текста
    text = get_user_input(
        "Введите текст для изображений",
        validator=validate_text,
        error_message="Текст должен быть от 1 до 50 символов"
    )
    if not text:
        return None, None
    
    # Ввод количества
    count = get_number(
        "Сколько изображений загрузить?",
        min_val=1,
        max_val=10,
        default=1
    )
    
    return text, count


def get_cat_preset_input():
    """
    Получает от пользователя параметры для расширенного бэкапа кошек.
    
    Returns:
        tuple: (text, count, preset) или (None, None, None) если отмена
    """
    print_subheader("🐱 Бэкап кошек (расширенный)", "-")
    
    # Ввод текста
    text = get_user_input(
        "Введите текст для изображений",
        validator=validate_text,
        error_message="Текст должен быть от 1 до 50 символов"
    )
    if not text:
        return None, None, None
    
    # Ввод количества
    count = get_number(
        "Сколько изображений загрузить?",
        min_val=1,
        max_val=10,
        default=1
    )
    
    # Выбор пресета
    presets = ['default', 'large', 'funny', 'elegant', 'minimal']
    preset = get_choice(
        "Выберите стиль изображения:",
        presets,
        default='default'
    )
    
    return text, count, preset


def get_dog_breed_input():
    """
    Получает от пользователя породу для бэкапа собак.
    
    Returns:
        str: название породы или None если отмена
    """
    print_subheader("🐶 Бэкап собаки", "-")
    
    # Получаем список пород для подсказки
    fetcher = ImageFetcher()
    breeds = fetcher.get_all_breeds()
    
    if not breeds:
        print_error("Не удалось получить список пород")
        return None
    
    # Показываем доступные породы
    print_info(f"Доступно пород: {len(breeds)}")
    
    # Показываем первые 10 для примера
    breed_list = list(breeds.keys())[:10]
    print("Примеры пород:")
    for i, b in enumerate(breed_list, 1):
        subs = breeds[b]
        subs_str = f" (подпороды: {', '.join(subs)})" if subs else ""
        print(f"  {i}. {b}{subs_str}")
    
    if len(breeds) > 10:
        print(f"  ... и еще {len(breeds) - 10} пород")
    
    # Ввод породы с валидацией
    breed = get_user_input(
        "Введите название породы",
        validator=lambda x: validate_breed(x, breeds),
        error_message="Порода не найдена. Проверьте написание."
    )
    
    return breed


# ============================================
# ФУНКЦИИ ДЛЯ ОТОБРАЖЕНИЯ РЕЗУЛЬТАТОВ
# ============================================

def show_results():
    """Показывает результаты предыдущих бэкапов."""
    clear_screen()
    print_header("📊 РЕЗУЛЬТАТЫ БЭКАПА", "=")
    
    if not RESULTS_FILE.exists():
        print_warning("Файл с результатами не найден")
        print_info("Сначала выполните бэкап изображений")
        input("\nНажмите Enter для возврата...")
        return
    
    try:
        with open(RESULTS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Общая информация
        print_info(f"Группа: {data.get('group_name', 'Unknown')}")
        print_info(f"Дата: {format_timestamp(data.get('timestamp', ''))}")
        print_separator("-")
        
        # Статистика
        stats = data.get('stats', {})
        print("\n📊 СТАТИСТИКА")
        print_separator("-")
        print(f"   ✅ Успешно: {stats.get('successful', 0)}")
        print(f"   ❌ Ошибок: {stats.get('failed', 0)}")
        print(f"   📦 Всего: {stats.get('processed', 0)}")
        print(f"   💾 Размер: {format_size(stats.get('total_size', 0))}")
        
        # Список файлов
        files = data.get('files', [])
        if files:
            print(f"\n📋 ЗАГРУЖЕННЫЕ ФАЙЛЫ ({len(files)})")
            print_separator("-")
            
            # Показываем последние 10 файлов
            for i, file_info in enumerate(files[-10:], 1):
                status = "✅" if file_info.get('success') else "❌"
                name = file_info.get('file_name', 'unknown')
                size = file_info.get('size', 0)
                source = file_info.get('source', 'unknown')
                print(f"   {i}. {status} {name} ({format_size(size)})")
                print(f"      Источник: {source}")
            
            if len(files) > 10:
                print(f"\n   ... и еще {len(files) - 10} файлов")
        else:
            print("\n📭 Нет загруженных файлов")
        
        # Путь к файлу
        print_separator("-")
        print_info(f"Файл результатов: {RESULTS_FILE}")
        
    except json.JSONDecodeError:
        print_error("Ошибка чтения JSON файла")
    except Exception as e:
        print_error(f"Ошибка: {e}")
    
    input("\nНажмите Enter для возврата в меню...")


# ============================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================

def main():
    """Основная функция программы."""
    clear_screen()
    
    while True:
        choice = show_main_menu()
        
        # ============================================
        # 1. БЭКАП КОШЕК (ОБЫЧНЫЙ)
        # ============================================
        if choice == "🐱 Бэкап кошек (cataas.com)":
            clear_screen()
            text, count = get_cat_input()
            
            if text and count:
                try:
                    manager = BackupManager()
                    results = manager.backup_cats(text, count)
                    
                    # Показываем результаты
                    successful = sum(1 for r in results if r.get('success'))
                    print_separator("-")
                    print_success(f"Загружено: {successful}/{count} изображений")
                    manager.print_summary()
                except Exception as e:
                    print_error(f"Ошибка: {e}")
            
            input("\nНажмите Enter для продолжения...")
        
        # ============================================
        # 2. БЭКАП КОШЕК (РАСШИРЕННЫЙ)
        # ============================================
        elif choice == "🐱 Бэкап кошек (расширенный, с пресетами)":
            clear_screen()
            text, count, preset = get_cat_preset_input()
            
            if text and count:
                try:
                    manager = BackupManager()
                    results = manager.backup_cats_advanced(text, count, preset=preset)
                    
                    successful = sum(1 for r in results if r.get('success'))
                    print_separator("-")
                    print_success(f"Загружено: {successful}/{count} изображений")
                    manager.print_summary()
                except Exception as e:
                    print_error(f"Ошибка: {e}")
            
            input("\nНажмите Enter для продолжения...")
        
        # ============================================
        # 3. БЭКАП СОБАК (ВСЕ ПОРОДЫ)
        # ============================================
        elif choice == "🐶 Бэкап собак (все породы)":
            clear_screen()
            print_subheader("🐶 Бэкап всех пород собак", "-")
            print_warning("Это может занять много времени!")
            
            if get_yes_no("Продолжить?", default=False):
                try:
                    manager = BackupManager()
                    results = manager.backup_dogs()
                    
                    successful = sum(1 for r in results if r.get('success'))
                    print_separator("-")
                    print_success(f"Загружено: {successful} изображений")
                    manager.print_summary()
                except Exception as e:
                    print_error(f"Ошибка: {e}")
            else:
                print_info("Отменено")
            
            input("\nНажмите Enter для продолжения...")
        
        # ============================================
        # 4. БЭКАП СОБАКИ (КОНКРЕТНАЯ ПОРОДА)
        # ============================================
        elif choice == "🐶 Бэкап собаки (конкретная порода)":
            clear_screen()
            breed = get_dog_breed_input()
            
            if breed:
                try:
                    manager = BackupManager()
                    results = manager.backup_dogs(breed)
                    
                    successful = sum(1 for r in results if r.get('success'))
                    print_separator("-")
                    print_success(f"Загружено: {successful} изображений")
                    manager.print_summary()
                except Exception as e:
                    print_error(f"Ошибка: {e}")
            
            input("\nНажмите Enter для продолжения...")
        
        # ============================================
        # 5. ПОКАЗАТЬ РЕЗУЛЬТАТЫ
        # ============================================
        elif choice == "📊 Показать результаты":
            show_results()
        
        # ============================================
        # 6. ПОМОЩЬ / СПРАВКА
        # ============================================
        elif choice == "❓ Помощь / Справка":
            print_help()
        
        # ============================================
        # 7. ВЫХОД
        # ============================================
        elif choice == "🚪 Выход":
            print_success("До свидания! 👋")
            break
        
        else:
            print_error("Неизвестный выбор")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Программа прервана пользователем")
        sys.exit(0)
    except Exception as e:
        print_error(f"Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)