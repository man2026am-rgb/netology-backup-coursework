"""
Модуль для работы с Яндекс.Диском с логированием.
"""

import requests
from typing import Optional, Dict, Any, List
from datetime import datetime
from src.config import YANDEX_DISK_TOKEN, YANDEX_DISK_BASE_URL
from src.utils import log_debug, log_info, log_error, log_warning


class YandexDiskClient:
    """Клиент для работы с Яндекс.Диском с логированием."""

    def __init__(self, token: Optional[str] = None):
        self.token = token or YANDEX_DISK_TOKEN
        if not self.token:
            raise ValueError("❌ Токен Яндекс.Диска не указан!")

        log_debug(f"Инициализация клиента, токен: {self.token[:15]}...")

        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"OAuth {self.token}"})

    def _request(self, method: str, url: str, **kwargs) -> dict:
        """Выполняет запрос с логированием."""
        log_debug(f"📡 {method} {url.split('?')[0]}")
        if "params" in kwargs:
            log_debug(f"   Параметры: {kwargs['params']}")

        try:
            response = self.session.request(method, url, timeout=30, **kwargs)
            log_debug(f"   → Статус: {response.status_code}")

            if response.status_code >= 400:
                log_warning(f"   Ошибка: {response.text[:200]}")

            return {
                "status": response.status_code,
                "data": response.json() if response.text else {},
                "text": response.text,
            }
        except Exception as e:
            log_error(f"   Исключение: {e}")
            return {"status": 0, "error": str(e), "data": {}, "text": str(e)}

    def check_connection(self) -> bool:
        """Проверяет подключение к Яндекс.Диску."""
        result = self._request("GET", f"{YANDEX_DISK_BASE_URL}/")
        return result.get("status") == 200

    def get_user_info(self) -> dict:
        """Получает информацию о пользователе."""
        result = self._request("GET", f"{YANDEX_DISK_BASE_URL}/")
        return result.get("data", {}) if result.get("status") == 200 else {}

    def create_folder(self, folder_path: str, silent: bool = False) -> bool:
        """Создает папку на Яндекс.Диске."""
        if not folder_path.startswith("/"):
            folder_path = "/" + folder_path

        if not silent:
            log_info(f"📁 Создание папки: {folder_path}")

        url = f"{YANDEX_DISK_BASE_URL}/resources"
        params = {"path": folder_path}

        result = self._request("PUT", url, params=params)
        status = result.get("status")

        if status == 201:
            if not silent:
                log_info(f"   ✅ Папка создана!")
            return True
        elif status == 409:
            error_text = result.get("text", "")
            if "DiskPathDoesntExistsError" in error_text:
                if not silent:
                    log_warning(f"   ❌ Родительская папка не существует")
                return False
            if not silent:
                log_info(f"   ℹ️ Папка уже существует")
            return True
        else:
            if not silent:
                log_error(f"   ❌ Ошибка: {result.get('text', 'Unknown error')}")
            return False

    def create_path(self, path: str) -> bool:
        """
        Создаёт все папки по указанному пути рекурсивно.

        Args:
            path: полный путь (например, '/netology-backup-coursework/Cats')

        Returns:
            bool: True если все папки созданы
        """
        parts = path.strip("/").split("/")
        current_path = ""

        log_info(f"📁 Создание пути: {path}")

        for part in parts:
            current_path = f"/{part}" if not current_path else f"{current_path}/{part}"
            if not self.create_folder(current_path, silent=True):
                log_error(f"   ❌ Ошибка создания папки: {current_path}")
                return False

        log_info(f"   ✅ Путь создан: {path}")
        return True

    def list_folder(self, folder_path: str) -> List[Dict[str, Any]]:
        """Получает список файлов в папке."""
        if not folder_path.startswith("/"):
            folder_path = "/" + folder_path

        log_debug(f"📂 Проверка папки: {folder_path}")

        url = f"{YANDEX_DISK_BASE_URL}/resources"
        params = {
            "path": folder_path,
            "fields": "_embedded.items.name,_embedded.items.size,_embedded.items.type",
        }

        result = self._request("GET", url, params=params)

        if result.get("status") == 200:
            data = result.get("data", {})
            items = data.get("_embedded", {}).get("items", [])
            log_debug(f"   📄 Найдено элементов: {len(items)}")
            return items
        else:
            log_warning(f"   ❌ Ошибка: {result.get('text', 'Unknown')}")
            return []

    def upload_file(self, file_name: str, file_data: bytes, folder_path: str) -> Dict[str, Any]:
        """Загружает файл на Яндекс.Диск."""
        if not folder_path.startswith("/"):
            folder_path = "/" + folder_path
        if not folder_path.endswith("/"):
            folder_path += "/"
        full_path = f"{folder_path}{file_name}"

        log_info(f"📤 Загрузка файла: {full_path}")
        log_debug(f"   Размер: {len(file_data)} байт")

        # 1. Получаем URL для загрузки
        upload_url = self._get_upload_url(full_path)
        if isinstance(upload_url, dict) and "error" in upload_url:
            log_error(f"   ❌ Ошибка получения URL: {upload_url.get('error')}")
            return {"success": False, "error": upload_url.get("error")}

        if not upload_url:
            log_error(f"   ❌ Не удалось получить URL для загрузки")
            return {"success": False, "error": "Не удалось получить URL для загрузки"}

        # 2. Загружаем файл
        try:
            response = self.session.put(
                upload_url,
                data=file_data,
                headers={"Content-Type": "application/octet-stream"},
                timeout=60,
            )
            log_debug(f"   → Статус загрузки: {response.status_code}")

            if response.status_code == 201:
                log_info(f"   ✅ Файл загружен: {file_name}")
                return {
                    "success": True,
                    "file_name": file_name,
                    "path": full_path,
                    "size": len(file_data),
                }
            else:
                log_error(f"   ❌ Ошибка загрузки: {response.text[:200]}")
                return {"success": False, "error": f"HTTP {response.status_code}"}
        except Exception as e:
            log_error(f"   ❌ Исключение: {e}")
            return {"success": False, "error": str(e)}

    def _get_upload_url(self, file_path: str) -> Optional[str]:
        """
        Получает ссылку для загрузки файла.
        Возвращает URL или None в случае ошибки.
        """
        log_debug(f"📡 Запрос URL для загрузки: {file_path}")

        url = f"{YANDEX_DISK_BASE_URL}/resources/upload"
        params = {"path": file_path, "overwrite": "true"}

        try:
            response = self.session.get(url, params=params, timeout=30)
            log_debug(f"   → Статус: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                href = data.get("href")
                if href:
                    log_debug(f"   ✅ Ссылка получена: {href[:50]}...")
                    return href
                else:
                    log_warning(f"   ❌ В ответе нет href: {data}")
                    return None

            elif response.status_code == 409:
                log_warning(f"   ⚠️ Конфликт: файл уже существует")
                log_info(f"   🔄 Пробуем с уникальным именем...")

                # Генерируем уникальное имя
                import os

                name, ext = os.path.splitext(file_path)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
                new_path = f"{name}_{timestamp}{ext}"
                log_debug(f"   📄 Новое имя: {new_path}")

                # Повторяем запрос с новым именем
                params["path"] = new_path
                response = self.session.get(url, params=params, timeout=30)
                log_debug(f"   → Статус: {response.status_code}")

                if response.status_code == 200:
                    data = response.json()
                    href = data.get("href")
                    if href:
                        log_info(f"   ✅ Ссылка получена для нового имени")
                        return href
                return None

            else:
                log_warning(f"   ❌ Ошибка: {response.status_code} - {response.text[:100]}")
                return None

        except Exception as e:
            log_error(f"   ❌ Исключение: {e}")
            return None
