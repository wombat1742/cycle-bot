import aiohttp
import logging
from uuid import uuid4
from datetime import datetime
from typing import List, Optional, Dict, Any
from aiogram.types import User as TgUser
import json
import ssl

logger = logging.getLogger(__name__)

class APITicketService:
    """
    Сервис для работы с тикетами через REST API
    Не использует прямую работу с БД, только HTTP запросы
    """
    
    def __init__(self, api_base_url: str, api_token: str):
        self.api_base_url = api_base_url.rstrip('/')
        self.api_token = api_token
        self.timeout = aiohttp.ClientTimeout(total=30)
        
        logger.info(f"🚀 APITicketService инициализирован")
        logger.info(f"🌐 API Base URL: {self.api_base_url}")
        logger.info(f"🔑 API Token: {self.api_token[:10]}...")
    
    async def _send_api_request(self, method: str, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Универсальный метод для отправки запросов к API
        """
        url = f"{self.api_base_url}/{endpoint.lstrip('/')}"
        
        logger.info(f"📤 Отправка {method} запроса к: {url}")
        
        if data:
            logger.debug(f"📦 Тело запроса: {json.dumps(data, indent=2, ensure_ascii=False)}")
        
        headers = {
            "Authorization": self.api_token,
            "Content-Type": "application/json",
            "User-Agent": "BikeShopBot/1.0"
        }
        
        # SSL контекст для обработки проблем с сертификатами
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        try:
            connector = aiohttp.TCPConnector(ssl=ssl_context)
            
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=self.timeout,
                headers=headers
            ) as session:
                
                request_kwargs = {}
                if data and method.upper() in ['POST', 'PUT', 'PATCH']:
                    request_kwargs['json'] = data
                
                async with session.request(method.upper(), url, **request_kwargs) as response:
                    return await self._process_api_response(response, url)
                    
        except aiohttp.ClientConnectorError as e:
            logger.error(f"❌ Ошибка подключения к {url}: {e}")
            raise ConnectionError(f"Не удалось подключиться к API: {e}")
        except aiohttp.ServerTimeoutError as e:
            logger.error(f"❌ Таймаут при обращении к {url}: {e}")
            raise TimeoutError(f"Превышено время ожидания API: {e}")
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка при запросе к {url}: {e}")
            raise
    
    async def _process_api_response(self, response: aiohttp.ClientResponse, url: str) -> Dict[str, Any]:
        """
        Обработка ответа от API
        """
        logger.info(f"📥 Получен ответ от {url}, статус: {response.status}")
        
        response_text = await response.text()
        
        # Логируем тело ответа для отладки
        if response_text:
            logger.debug(f"📄 Тело ответа: {response_text[:500]}...")
        else:
            logger.debug("📄 Тело ответа: пустое")
        
        # Проверяем статус код
        if response.status >= 400:
            error_msg = f"API вернул ошибку {response.status} для {url}"
            logger.error(f"❌ {error_msg}")
            logger.error(f"   Ответ: {response_text}")
            raise aiohttp.ClientResponseError(
                request_info=response.request_info,
                history=response.history,
                status=response.status,
                message=error_msg,
                headers=response.headers
            )
        
        # Парсим JSON ответ
        if response_text.strip():
            try:
                result = await response.json()
                logger.info(f"✅ Успешный ответ от API")
                return result
            except json.JSONDecodeError as e:
                logger.error(f"❌ Ошибка парсинга JSON от {url}: {e}")
                logger.error(f"   Сырой ответ: {response_text}")
                raise ValueError(f"Невалидный JSON в ответе API: {e}")
        else:
            logger.warning("⚠️ Пустой ответ от API")
            return {}
    
    async def health_check(self) -> bool:
        """
        Проверка доступности API
        """
        logger.info("🏥 Проверка здоровья API...")
        
        try:
            # Пробуем получить несуществующий тикет - если API отвечает, значит работает
            await self._send_api_request("GET", f"ticket/health-check-test-{uuid4()}")
            return True
        except aiohttp.ClientResponseError as e:
            if e.status == 404:
                logger.info("✅ API доступен (получена ожидаемая 404)")
                return True
            else:
                logger.error(f"❌ API недоступен, статус: {e.status}")
                return False
        except Exception as e:
            logger.error(f"❌ API недоступен: {e}")
            return False
    
    async def create_ticket(self, tg_user: TgUser, message_text: str, chat_id: str, msg_id: str) -> Dict[str, Any]:
        """
        Создание нового тикета через API
        """
        logger.info(f"🎫 Создание тикета для пользователя {tg_user.id}")
        
        ticket_id = str(uuid4())
        
        # Подготовка данных для API
        ticket_data = {
            "id": ticket_id,
            "user_id": tg_user.id,
            "status": "open",
            "opened_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        message_data = {
            "id": str(uuid4()),
            "text": message_text,
            "ticket_id": ticket_id,
            "user_id": tg_user.id,
            "is_staff": False,
            "chat_id": chat_id,
            "msg_id": msg_id,
            "created_at": datetime.now().isoformat(),
            "attachments": []
        }
        
        try:
            # Создаем тикет
            logger.info("📝 Создание тикета через API...")
            ticket_result = await self._send_api_request("POST", "ticket/add", ticket_data)
            logger.info(f"✅ Тикет создан: {ticket_id}")
            
            # Добавляем первое сообщение
            logger.info("💬 Добавление начального сообщения...")
            message_result = await self._send_api_request("POST", f"ticket/{ticket_id}/messages/add", message_data)
            logger.info(f"✅ Сообщение добавлено в тикет {ticket_id}")
            
            return {
                "ticket": ticket_result,
                "message": message_result,
                "ticket_id": ticket_id
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка при создании тикета: {e}")
            raise
    
    async def add_message(self, ticket_id: str, tg_user: TgUser, message_text: str, 
                         chat_id: str, msg_id: str, is_staff: bool = False) -> Dict[str, Any]:
        """
        Добавление сообщения в существующий тикет
        """
        logger.info(f"📨 Добавление сообщения в тикет {ticket_id}")
        
        message_data = {
            "id": str(uuid4()),
            "text": message_text,
            "ticket_id": ticket_id,
            "user_id": tg_user.id,
            "is_staff": is_staff,
            "chat_id": chat_id,
            "msg_id": msg_id,
            "created_at": datetime.now().isoformat(),
            "attachments": []
        }
        
        try:
            result = await self._send_api_request("POST", f"ticket/{ticket_id}/messages/add", message_data)
            logger.info(f"✅ Сообщение добавлено в тикет {ticket_id}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка при добавлении сообщения в тикет {ticket_id}: {e}")
            raise
    
    async def add_message_with_attachments(self, ticket_id: str, tg_user: TgUser, 
                                          message_text: str, chat_id: str, msg_id: str,
                                          attachments: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Добавление сообщения с вложениями
        """
        logger.info(f"📎 Добавление сообщения с {len(attachments)} вложениями в тикет {ticket_id}")
        
        message_data = {
            "id": str(uuid4()),
            "text": message_text,
            "ticket_id": ticket_id,
            "user_id": tg_user.id,
            "is_staff": False,
            "chat_id": chat_id,
            "msg_id": msg_id,
            "created_at": datetime.now().isoformat(),
            "attachments": attachments
        }
        
        try:
            result = await self._send_api_request("POST", f"ticket/{ticket_id}/messages/add", message_data)
            logger.info(f"✅ Сообщение с вложениями добавлено в тикет {ticket_id}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка при добавлении сообщения с вложениями: {e}")
            raise
    
    async def get_ticket(self, ticket_id: str) -> Dict[str, Any]:
        """
        Получение информации о тикете
        """
        logger.info(f"📋 Получение тикета {ticket_id}")
        
        try:
            result = await self._send_api_request("GET", f"ticket/{ticket_id}")
            logger.info(f"✅ Тикет {ticket_id} получен")
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка при получении тикета {ticket_id}: {e}")
            raise
    
    async def get_ticket_messages(self, ticket_id: str) -> List[Dict[str, Any]]:
        """
        Получение сообщений тикета
        """
        logger.info(f"💬 Получение сообщений тикета {ticket_id}")
        
        try:
            ticket_data = await self.get_ticket(ticket_id)
            messages = ticket_data.get("messages", [])
            logger.info(f"✅ Получено {len(messages)} сообщений для тикета {ticket_id}")
            return messages
            
        except Exception as e:
            logger.error(f"❌ Ошибка при получении сообщений тикета {ticket_id}: {e}")
            raise
    
    async def get_user_tickets(self, user_id: int, status: str = None) -> List[Dict[str, Any]]:
        """
        Получение тикетов пользователя
        TODO: Нужно добавить соответствующий эндпоинт в API
        """
        logger.info(f"📂 Получение тикетов пользователя {user_id}")
        
        # Временная заглушка - получаем все тикеты и фильтруем локально
        # В будущем нужно добавить эндпоинт /tickets?user_id=123
        logger.warning("⚠️ Эндпоинт для получения тикетов пользователя не реализован")
        return []
    
    async def close_ticket(self, ticket_id: str, closed_by: TgUser) -> Dict[str, Any]:
        """
        Закрытие тикета
        """
        logger.info(f"🔒 Закрытие тикета {ticket_id}")
        
        try:
            # Добавляем системное сообщение о закрытии
            close_message = "Тикет закрыт поддержкой"
            result = await self.add_message(
                ticket_id, closed_by, close_message, "system", str(uuid4()), True
            )
            
            logger.info(f"✅ Тикет {ticket_id} закрыт")
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка при закрытии тикета {ticket_id}: {e}")
            raise