import httpx
from app.config import settings
import asyncio


async def list_models():
    # URL для листинга моделей
    url = f"https://generativelanguage.googleapis.com/v1/models?key={settings.GEMINI_API_KEY}"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                models = resp.json()
                print("Доступные модели:")
                # Выводим названия моделей
                for model in models.get("models", []):
                    print(f"- {model['name']}")
            else:
                print(f"Ошибка {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"Ошибка запроса: {e}")


if __name__ == "__main__":
    asyncio.run(list_models())
