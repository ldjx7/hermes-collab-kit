import asyncio
import logging
from typing import Dict, Any, Optional

# Mock httpx for demonstration purposes. In a real application,
# you would `import httpx` and use it for actual HTTP requests.
class MockAsyncClient:
    """A mock asynchronous HTTP client for httpx."""
    async def post(self, url: str, json: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> Any:
        logging.info(f"MockAsyncClient: POST to {url} with data {json} and headers {headers}")
        await asyncio.sleep(0.1) # Simulate network delay
        if "access_token" in url:
            return MockResponse(200, {"code": 0, "msg": "success", "tenant_access_token": "mock_tenant_access_token", "expire_in": 7200})
        if "message/v4/send" in url:
            return MockResponse(200, {"code": 0, "msg": "success", "data": {"message_id": "mock_msg_id"}})
        return MockResponse(200, {"code": 0, "msg": "success"})

    async def get(self, url: str, headers: Optional[Dict[str, str]] = None) -> Any:
        logging.info(f"MockAsyncClient: GET to {url} with headers {headers}")
        await asyncio.sleep(0.1) # Simulate network delay
        return MockResponse(200, {"code": 0, "msg": "success"})

class MockResponse:
    """A mock HTTP response object."""
    def __init__(self, status_code: int, json_data: Dict[str, Any]):
        self.status_code = status_code
        self._json_data = json_data

    def raise_for_status(self):
        if 200 <= self.status_code < 300:
            return
        raise Exception(f"HTTP Error: {self.status_code}")

    async def json(self) -> Dict[str, Any]:
        return self._json_data

# Use the mock client
httpx = MockAsyncClient()


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class FeishuBotError(Exception):
    """Custom exception for Feishu Bot operations."""
    pass


class FeishuBot:
    """
    Manages interactions with the Feishu Open Platform Bot.

    This class handles bot creation, configuration, sending, and receiving messages.
    It includes mechanisms for token management and API communication.
    """

    def __init__(self, app_id: str, app_secret: str, base_url: str = "https://open.feishu.cn/open-apis"):
        """
        Initializes the FeishuBot with application credentials.

        Args:
            app_id: The App ID obtained from the Feishu Open Platform.
            app_secret: The App Secret obtained from the Feishu Open Platform.
            base_url: The base URL for Feishu Open APIs.
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self.base_url = base_url
        self._tenant_access_token: Optional[str] = None
        self._token_expiry_time: float = 0.0  # Unix timestamp
        logger.info(f"FeishuBot initialized for app_id: {app_id}")

    async def _get_access_token(self, force_refresh: bool = False) -> str:
        """
        Retrieves or refreshes the tenant access token.

        Tokens are cached and refreshed automatically before expiry.

        Args:
            force_refresh: If True, forces a token refresh even if current one is valid.

        Returns:
            The valid tenant access token.

        Raises:
            FeishuBotError: If unable to obtain the access token.
        """
        current_time = asyncio.get_event_loop().time()
        if not force_refresh and self._tenant_access_token and self._token_expiry_time > current_time + 60:
            logger.debug("Using cached tenant access token.")
            return self._tenant_access_token

        logger.info("Refreshing tenant access token...")
        token_url = f"{self.base_url}/auth/v3/tenant_access_token/internal"
        headers = {"Content-Type": "application/json"}
        payload = {"app_id": self.app_id, "app_secret": self.app_secret}

        try:
            response = await httpx.post(token_url, json=payload, headers=headers)
            response.raise_for_status()
            data = await response.json()

            if data.get("code") == 0:
                self._tenant_access_token = data["tenant_access_token"]
                self._token_expiry_time = current_time + data["expire_in"]
                logger.info("Successfully refreshed tenant access token.")
                return self._tenant_access_token
            else:
                error_msg = data.get("msg", "Unknown error")
                logger.error(f"Failed to get tenant access token: {error_msg} (Code: {data.get('code')})")
                raise FeishuBotError(f"Failed to get tenant access token: {error_msg}")
        except Exception as e:
            logger.exception(f"Exception during tenant access token retrieval: {e}")
            raise FeishuBotError(f"Network or API error getting token: {e}")

    async def _api_call(self, method: str, endpoint: str, json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Helper method to make authenticated API calls to Feishu.

        Args:
            method: HTTP method (e.g., 'GET', 'POST').
            endpoint: The API endpoint path (e.g., '/im/v1/messages').
            json_data: JSON payload for POST/PUT requests.

        Returns:
            The JSON response from the Feishu API.

        Raises:
            FeishuBotError: If the API call fails or returns an error.
        """
        token = await self._get_access_token()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
        url = f"{self.base_url}{endpoint}"
        logger.debug(f"Making Feishu API call: {method} {url}")

        try:
            if method.upper() == "POST":
                response = await httpx.post(url, json=json_data, headers=headers)
            elif method.upper() == "GET":
                response = await httpx.get(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            data = await response.json()

            if data.get("code") == 0:
                return data
            else:
                error_msg = data.get("msg", "Unknown API error")
                logger.error(f"Feishu API call failed for {endpoint}: {error_msg} (Code: {data.get('code')})")
                raise FeishuBotError(f"Feishu API error: {error_msg}")
        except Exception as e:
            logger.exception(f"Exception during Feishu API call to {endpoint}: {e}")
            raise FeishuBotError(f"Network or API error: {e}")

    async def send_message(self, receive_id: str, receive_id_type: str, msg_type: str, content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sends a message to a specified user or chat in Feishu.

        Args:
            receive_id: The ID of the recipient (user_id, open_id, chat_id, email, etc.).
            receive_id_type: The type of the receive_id (e.g., 'open_id', 'user_id', 'chat_id').
            msg_type: The type of message (e.g., 'text', 'post', 'interactive').
            content: The message content as a JSON object (e.g., {"text": "Hello world"}).

        Returns:
            The JSON response from the Feishu message sending API.

        Raises:
            FeishuBotError: If message sending fails.
        """
        endpoint = "/im/v1/messages"
        payload = {
            "receive_id": receive_id,
            "receive_id_type": receive_id_type,
            "msg_type": msg_type,
            "content": content
        }
        logger.info(f"Sending {msg_type} message to {receive_id_type}:{receive_id}")
        return await self._api_call("POST", endpoint, json_data=payload)

    async def receive_message(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes an incoming message event from Feishu (e.g., from a webhook).

        This is a placeholder for handling message events. In a real application,
        this would parse the event_data, verify signature, and trigger appropriate
        handlers based on message type and content.

        Args:
            event_data: The raw JSON payload received from Feishu's webhook.

        Returns:
            A dictionary containing processed message information or an acknowledgment.
        """
        logger.info(f"Received Feishu message event. Event type: {event_data.get('header', {}).get('event_type')}")
        # In a real app, you would:
        # 1. Verify webhook signature (security)
        # 2. Parse event_data based on event_type (e.g., 'im.message.receive_v1')
        # 3. Extract sender, message content, etc.
        # 4. Route to specific command/logic handlers.

        # Mock processing
        message_id = event_data.get("event", {}).get("message", {}).get("message_id", "N/A")
        sender_id = event_data.get("event", {}).get("sender", {}).get("sender_id", {}).get("open_id", "N/A")
        text_content = event_data.get("event", {}).get("message", {}).get("content", "{}")
        logger.info(f"Mock processing message {message_id} from {sender_id} with content: {text_content}")

        return {"status": "processed", "message_id": message_id, "sender_id": sender_id}

    async def _configure_bot(self) -> bool:
        """
        Placeholder for configuring the bot (e.g., setting up event subscriptions,
        updating bot profile). This typically involves Feishu Open Platform UI
        or specific management APIs.

        Returns:
            True if configuration is successful, False otherwise.
        """
        logger.info("Mocking bot configuration. This often involves manual setup on Feishu Open Platform.")
        # Actual configuration might involve:
        # - Checking event subscription status
        # - Setting bot avatar/name (if API supported)
        return True

# Example Usage (for testing purposes)
async def main():
    bot = FeishuBot(app_id="cli_mock_app_id", app_secret="cli_mock_app_secret")
    try:
        # Test token retrieval
        token = await bot._get_access_token()
        print(f"Obtained token: {token[:10]}...")

        # Test sending a message (replace with a real user_id/open_id for actual testing)
        mock_user_id = "ou_abcdefg1234567" # This would be a real user's open_id or user_id
        mock_chat_id = "oc_abcdefg1234567" # This would be a real chat ID
        message_content = {"text": "Hello from the Gemini CLI Feishu bot! This is a test message."}
        send_response = await bot.send_message(mock_user_id, "open_id", "text", message_content)
        print(f"Send message response: {send_response}")

        # Test receiving a mock message (simulating a webhook event)
        mock_event = {
            "header": {"event_type": "im.message.receive_v1"},
            "event": {
                "sender": {"sender_id": {"open_id": "ou_sender_mock"}},
                "message": {"message_id": "om_mock_message", "message_type": "text", "content": '{"text":"/help"}'}
            }
        }
        receive_response = await bot.receive_message(mock_event)
        print(f"Receive message processing response: {receive_response}")

    except FeishuBotError as e:
        logger.error(f"Feishu Bot error in example usage: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred in example usage: {e}")

if __name__ == "__main__":
    asyncio.run(main())