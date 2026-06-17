import requests
from dotenv import load_dotenv
from tqdm import tqdm
import os

def test_setup():
    # Проверка загрузки переменных окружения
    load_dotenv()
    token = os.getenv('YANDEX_DISK_TOKEN')
    if token:
        print("✅ Переменные окружения загружены")
    else:
        print("❌ Токен не найден в .env файле")
    
    # Проверка установленных библиотек
    print(f"✅ requests версия: {requests.__version__}")
    print(f"✅ tqdm установлен")
    print("✅ Все библиотеки установлены корректно!")

if __name__ == "__main__":
    test_setup()