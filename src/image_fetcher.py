"""
Модуль для получения изображений из API (cataas.com и dog.ceo)
с поддержкой кэширования.
"""
import requests
import time
from urllib.parse import quote
from typing import Optional, Dict, Any, List, Tuple

from src.config import (
    CAT_API_BASE_URL,
    DOG_API_BASE_URL,
    CAT_API_ENDPOINT,
    CAT_DEFAULT_PARAMS,
    CAT_ALLOWED_COLORS,
    CAT_ALLOWED_FONTS,
    CAT_ALLOWED_FILTERS
)
from src.utils import api_cache, log_debug, log_warning, log_error, log_info


class ImageFetcher:
    """
    Класс для получения изображений из различных источников с кэшированием.
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CatBackup/1.0'
        })
        self.last_error: Optional[str] = None
        self.stats: Dict[str, int] = {
            'total_requests': 0,
            'successful': 0,
            'failed': 0,
            'cache_hits': 0
        }

    # ============================================================
    # МЕТОДЫ ДЛЯ РАБОТЫ С CATAAS.COM (КОШКИ)
    # ============================================================

    def get_cat_image(self, text: str, size: str = '300') -> Optional[bytes]:
        """
        Получает изображение кота с текстом с использованием кэша.

        Args:
            text: Текст для надписи.
            size: Размер изображения.

        Returns:
            Optional[bytes]: Содержимое изображения или None.
        """
        self.stats['total_requests'] += 1

        # Валидация текста
        if not text or len(text.strip()) == 0:
            self.stats['failed'] += 1
            self.last_error = "Текст не может быть пустым"
            return None

        if len(text) > 50:
            self.stats['failed'] += 1
            self.last_error = "Текст слишком длинный (максимум 50 символов)"
            return None

        # Формируем ключ кэша
        cache_key = f"cat_{text}_{size}"
        
        # Проверяем кэш
        cached_data = api_cache.get(cache_key)
        if cached_data is not None:
            self.stats['cache_hits'] += 1
            log_debug(f"Изображение получено из кэша: {cache_key}")
            return cached_data

        try:
            encoded_text = quote(text)
            url = f"{CAT_API_BASE_URL}{CAT_API_ENDPOINT.format(text=encoded_text)}"
            params = {'size': size}

            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                if 'image' in content_type:
                    self.stats['successful'] += 1
                    self.last_error = None
                    # Сохраняем в кэш
                    api_cache.set(cache_key, response.content)
                    return response.content
                else:
                    self.stats['failed'] += 1
                    self.last_error = f"Не изображение: {content_type}"
                    return None
            else:
                self.stats['failed'] += 1
                self.last_error = f"HTTP {response.status_code}"
                return None

        except requests.exceptions.Timeout:
            self.stats['failed'] += 1
            self.last_error = "Таймаут при получении изображения"
            log_error(f"Timeout для {text}")
            return None
        except requests.exceptions.ConnectionError:
            self.stats['failed'] += 1
            self.last_error = "Ошибка соединения с API"
            log_error(f"ConnectionError для {text}")
            return None
        except requests.exceptions.RequestException as e:
            self.stats['failed'] += 1
            self.last_error = str(e)
            log_error(f"RequestException для {text}: {e}")
            return None
        except Exception as e:
            self.stats['failed'] += 1
            self.last_error = str(e)
            log_error(f"Unexpected error для {text}: {e}")
            return None

    def get_cat_image_advanced(self,
                               text: str,
                               size: int = None,
                               color: str = None,
                               font_size: int = None,
                               font: str = None,
                               image_type: str = None,
                               filter_type: str = None,
                               **kwargs) -> Optional[bytes]:
        """
        Расширенная версия получения изображения кота с параметрами и кэшированием.
        """
        self.stats['total_requests'] += 1

        # Валидация
        if not text or len(text.strip()) == 0:
            self.stats['failed'] += 1
            self.last_error = "Текст не может быть пустым"
            return None

        if len(text) > 50:
            self.stats['failed'] += 1
            self.last_error = "Текст не должен превышать 50 символов"
            return None

        # Параметры по умолчанию
        size = size or CAT_DEFAULT_PARAMS.get('size', 300)
        color = color or CAT_DEFAULT_PARAMS.get('color', 'red')
        font_size = font_size or CAT_DEFAULT_PARAMS.get('fontSize', 50)
        font = font or CAT_DEFAULT_PARAMS.get('font', 'Impact')
        image_type = image_type or CAT_DEFAULT_PARAMS.get('type', 'jpg')

        # Валидация параметров
        if color and color not in CAT_ALLOWED_COLORS:
            self.stats['failed'] += 1
            self.last_error = f"Недопустимый цвет: {color}"
            return None

        if font and font not in CAT_ALLOWED_FONTS:
            self.stats['failed'] += 1
            self.last_error = f"Недопустимый шрифт: {font}"
            return None

        if filter_type and filter_type not in CAT_ALLOWED_FILTERS:
            self.stats['failed'] += 1
            self.last_error = f"Недопустимый фильтр: {filter_type}"
            return None

        # Формируем ключ кэша
        cache_key = f"cat_adv_{text}_{size}_{color}_{font_size}_{font}_{image_type}_{filter_type}_{kwargs}"
        
        # Проверяем кэш
        cached_data = api_cache.get(cache_key)
        if cached_data is not None:
            self.stats['cache_hits'] += 1
            log_debug(f"Изображение получено из кэша: {cache_key[:50]}...")
            return cached_data

        try:
            encoded_text = quote(text)
            url = f"{CAT_API_BASE_URL}{CAT_API_ENDPOINT.format(text=encoded_text)}"

            params = {
                'size': max(100, min(size, 800)),
                'color': color.lower(),
                'fontSize': max(10, min(font_size, 100))
            }

            if font:
                params['font'] = font
            if image_type:
                params['type'] = image_type
            if filter_type:
                params['filter'] = filter_type

            for key, value in kwargs.items():
                if key in ['rotate', 'flip', 'flop', 'gravity']:
                    params[key] = value

            response = self.session.get(url, params=params, timeout=30)

            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                if 'image' in content_type:
                    self.stats['successful'] += 1
                    self.last_error = None
                    api_cache.set(cache_key, response.content)
                    return response.content
                else:
                    self.stats['failed'] += 1
                    self.last_error = f"Не изображение: {content_type}"
                    return None
            else:
                self.stats['failed'] += 1
                self.last_error = f"HTTP {response.status_code}"
                return None

        except Exception as e:
            self.stats['failed'] += 1
            self.last_error = str(e)
            log_error(f"Ошибка получения изображения: {e}")
            return None

    def get_multiple_cat_images(self, text: str, count: int = 1) -> List[Tuple[str, bytes]]:
        """
        Получает несколько изображений кошек.
        """
        images = []
        for i in range(1, count + 1):
            image_data = self.get_cat_image(text)
            if image_data:
                safe_text = ''.join(c for c in text if c.isalnum() or c in (' ', '-', '_'))[:20]
                file_name = f"cat_{i}_{safe_text}.jpg"
                images.append((file_name, image_data))
            else:
                log_warning(f"Не удалось получить изображение #{i}")
        return images

    def get_cat_with_preset(self, text: str, preset: str = 'default') -> Optional[bytes]:
        """
        Получает изображение с предустановкой.
        """
        presets = {
            'default': {'size': 300, 'color': 'red', 'font_size': 50},
            'large': {'size': 600, 'color': 'blue', 'font_size': 80, 'filter_type': 'paint'},
            'funny': {'size': 400, 'color': 'yellow', 'font_size': 70, 'font': 'Comic Sans MS', 'filter_type': 'blur'},
            'elegant': {'size': 500, 'color': 'white', 'font_size': 45, 'font': 'Georgia', 'filter_type': 'sepia'},
            'minimal': {'size': 200, 'color': 'black', 'font_size': 30, 'font': 'Arial'}
        }

        preset_params = presets.get(preset, presets['default'])
        return self.get_cat_image_advanced(text, **preset_params)

    def get_cat_with_retry(self, text: str, max_retries: int = 3, **kwargs) -> Optional[bytes]:
        """
        Получает изображение с повторными попытками.
        """
        for attempt in range(1, max_retries + 1):
            log_info(f"Попытка {attempt}/{max_retries}...")

            image_data = self.get_cat_image_advanced(text, **kwargs)

            if image_data:
                log_success(f"Изображение получено на попытке {attempt}")
                return image_data

            if attempt < max_retries:
                wait_time = attempt * 2
                log_info(f"⏳ Ожидание {wait_time} секунд...")
                time.sleep(wait_time)

        self.last_error = f"Не удалось получить изображение после {max_retries} попыток. Последняя ошибка: {self.last_error}"
        log_error(self.last_error)
        return None

    def get_cat_stats(self) -> Dict[str, Any]:
        """
        Возвращает статистику работы с API кошек.
        """
        return {
            **self.stats,
            'success_rate': f"{self.stats['successful'] / max(1, self.stats['total_requests']) * 100:.1f}%",
            'cache_hit_rate': f"{self.stats['cache_hits'] / max(1, self.stats['total_requests']) * 100:.1f}%",
            'last_error': self.last_error
        }

    # ============================================================
    # МЕТОДЫ ДЛЯ РАБОТЫ С DOG.CEO (СОБАКИ)
    # ============================================================

    def get_all_breeds(self) -> Dict[str, List[str]]:
        """
        Получает список всех пород собак и их подпород.
        """
        cache_key = "dog_breeds_all"
        
        # Проверяем кэш
        cached_data = api_cache.get(cache_key)
        if cached_data is not None:
            log_debug("Список пород получен из кэша")
            return cached_data

        url = f"{DOG_API_BASE_URL}/breeds/list/all"

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            data = response.json()
            if data.get('status') == 'success':
                breeds = data.get('message', {})
                api_cache.set(cache_key, breeds)
                return breeds
            else:
                self.last_error = f"API вернул ошибку: {data.get('status')}"
                return {}

        except requests.exceptions.Timeout:
            self.last_error = "Таймаут при получении списка пород"
            log_error(self.last_error)
            return {}
        except requests.exceptions.ConnectionError:
            self.last_error = "Ошибка соединения с Dog.ceo"
            log_error(self.last_error)
            return {}
        except requests.exceptions.RequestException as e:
            self.last_error = f"Ошибка запроса: {str(e)}"
            log_error(self.last_error)
            return {}

    def get_random_dog_image_url(self, breed: str, sub_breed: str = None) -> Optional[str]:
        """
        Получает URL случайного изображения для указанной породы.
        """
        breed_path = f"{breed}/{sub_breed}" if sub_breed else breed
        cache_key = f"dog_url_{breed_path}"
        
        # Проверяем кэш
        cached_data = api_cache.get(cache_key)
        if cached_data is not None:
            log_debug(f"URL для {breed_path} получен из кэша")
            return cached_data

        url = f"{DOG_API_BASE_URL}/breed/{breed_path}/images/random"

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            data = response.json()
            if data.get('status') == 'success':
                image_url = data.get('message')
                api_cache.set(cache_key, image_url)
                return image_url
            else:
                self.last_error = f"API вернул ошибку для {breed_path}: {data.get('status')}"
                return None

        except requests.exceptions.Timeout:
            self.last_error = f"Таймаут при получении изображения для {breed_path}"
            log_error(self.last_error)
            return None
        except requests.exceptions.ConnectionError:
            self.last_error = f"Ошибка соединения при получении {breed_path}"
            log_error(self.last_error)
            return None
        except requests.exceptions.RequestException as e:
            self.last_error = f"Ошибка запроса для {breed_path}: {str(e)}"
            log_error(self.last_error)
            return None

    def get_dog_image_data(self, breed: str, sub_breed: str = None) -> Optional[bytes]:
        """
        Получает бинарные данные изображения собаки.
        """
        breed_path = f"{breed}/{sub_breed}" if sub_breed else breed
        cache_key = f"dog_image_{breed_path}"
        
        # Проверяем кэш
        cached_data = api_cache.get(cache_key)
        if cached_data is not None:
            log_debug(f"Изображение для {breed_path} получено из кэша")
            return cached_data

        image_url = self.get_random_dog_image_url(breed, sub_breed)
        if not image_url:
            return None

        try:
            response = self.session.get(image_url, timeout=30)
            response.raise_for_status()

            content_type = response.headers.get('Content-Type', '')
            if 'image' in content_type:
                image_data = response.content
                api_cache.set(cache_key, image_data)
                return image_data
            else:
                self.last_error = f"Получен не изображение: {content_type}"
                return None

        except requests.exceptions.RequestException as e:
            self.last_error = f"Ошибка скачивания изображения: {str(e)}"
            log_error(self.last_error)
            return None

    def clear_cache(self) -> None:
        """Очищает кэш API запросов."""
        api_cache.clear()
        log_info("Кэш API очищен")