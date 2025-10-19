import aiohttp
import logging
from typing import Dict, Any, Optional
from uuid import uuid4
from datetime import datetime

logger = logging.getLogger(__name__)

class APIClient:
    def __init__(self, base_url: str, token: str, timeout: int = 30):
        self.base_url = base_url
        self.token = token
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=self.timeout,
            headers={"Authorization": self.token}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Базовый метод для HTTP запросов"""
        # Полный URL с портом
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        logger.info(f"🔄 Отправка запроса к: {url}")
        
        # Добавляем заголовок авторизации
        if 'headers' not in kwargs:
            kwargs['headers'] = {}
        kwargs['headers']['Authorization'] = self.token
        kwargs['headers']['Content-Type'] = 'application/json'
        
        try:
            async with self.session.request(method, url, **kwargs) as response:
                logger.info(f"📡 Статус ответа: {response.status}")
                
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"❌ API error {response.status}: {error_text}")
                    response.raise_for_status()
                
                result = await response.json()
                logger.info(f"✅ Успешный ответ от API: {result}")
                return result
                
        except aiohttp.ClientError as e:
            logger.error(f"❌ Ошибка подключения к API: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка: {e}")
            raise
    
    async def create_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создать новый тикет"""
        return await self._request('POST', 'ticket/add', json=ticket_data)
    
    async def add_message_to_ticket(self, ticket_id: str, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Добавить сообщение в тикет"""
        return await self._request('POST', f'ticket/{ticket_id}/messages/add', json=message_data)
    
    async def get_ticket(self, ticket_id: str) -> Dict[str, Any]:
        """Получить тикет по ID"""
        return await self._request('GET', f'ticket/{ticket_id}')