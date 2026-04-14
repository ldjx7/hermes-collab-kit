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
        if "access_token" in url and "grant_type=authorization_code" in url:
            return MockResponse(200, {
                "code": 0, "msg": "success",
                "access_token": "mock_user_access_token",
                "refresh_token": "mock_refresh_token",
                "token_type": "Bearer",
                "expire_in": 7200,
                "open_id": "ou_mock_user"
            })
        if "refresh_token" in url:
             return MockResponse(200, {
                "code": 0, "msg": "success",
                "access_token": "new_mock_user_access_token",
                "refresh_token": "new_mock_refresh_token",
                "token_type": "Bearer",
                "expire_in": 7200,
                "open_id": "ou_mock_user"
            })
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


class OAuthManagerError(Exception):
    """Custom exception for OAuth management issues."""
    pass


class OAuthManager:
    """
    Manages the OAuth 2.0 authorization flow for Feishu applications.

    Handles generating authorization URLs, exchanging authorization codes for tokens,
    and refreshing access tokens. It also includes mock methods for token storage.
    """

    def __init__(self, app_id: str, app_secret: str, redirect_uri: str,
                 base_url: str = "https://open.feishu.cn/open-apis"):
        """
        Initializes the OAuthManager.

        Args:
            app_id: The App ID obtained from the Feishu Open Platform.
            app_secret: The App Secret obtained from the Feishu Open Platform.
            redirect_uri: The URL where Feishu redirects after authorization.
            base_url: The base URL for Feishu Open APIs.
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self.redirect_uri = redirect_uri
        self.base_url = base_url
        self._cached_token_data: Optional[Dict[str, Any]] = None
        logger.info(f"OAuthManager initialized for app_id: {app_id}, redirect_uri: {redirect_uri}")

    def get_authorization_url(self, state: str, scope: str = "contact:user.base",
                              response_type: str = "code") -> str:
        """
        Generates the authorization URL to redirect users to Feishu for consent.

        Args:
            state: A unique string to prevent CSRF attacks.
            scope: The requested permissions (e.g., 'contact:user.base', 'im:message').
            response_type: The desired response type (always 'code' for authorization code flow).

        Returns:
            The full authorization URL.
        """
        auth_url = (
            f"{self.base_url}/authen/v1/index?"
            f"app_id={self.app_id}&"
            f"redirect_uri={self.redirect_uri}&"
            f"response_type={response_type}&"
            f"scope={scope}&"
            f"state={state}"
        )
        logger.info(f"Generated authorization URL: {auth_url}")
        return auth_url

    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """
        Exchanges an authorization code for an access token and refresh token.

        Args:
            code: The authorization code received from the Feishu redirect.

        Returns:
            A dictionary containing access_token, refresh_token, expire_in, etc.

        Raises:
            OAuthManagerError: If token exchange fails.
        """
        token_url = f"{self.base_url}/authen/v1/access_token"
        headers = {"Content-Type": "application/json"}
        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret,
            "code": code,
            "grant_type": "authorization_code"
        }
        logger.info(f"Exchanging authorization code for token for app_id: {self.app_id}")

        try:
            response = await httpx.post(token_url, json=payload, headers=headers)
            response.raise_for_status()
            data = await response.json()

            if data.get("code") == 0:
                logger.info("Successfully exchanged code for tokens.")
                await self._store_token(data)
                return data
            else:
                error_msg = data.get("msg", "Unknown error")
                logger.error(f"Failed to exchange code for token: {error_msg} (Code: {data.get('code')})")
                raise OAuthManagerError(f"Failed to exchange code for token: {error_msg}")
        except Exception as e:
            logger.exception(f"Exception during token exchange: {e}")
            raise OAuthManagerError(f"Network or API error during token exchange: {e}")

    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refreshes an expired access token using the refresh token.

        Args:
            refresh_token: The refresh token obtained during the initial authorization.

        Returns:
            A dictionary containing new access_token, refresh_token, expire_in, etc.

        Raises:
            OAuthManagerError: If token refresh fails.
        """
        token_url = f"{self.base_url}/authen/v1/refresh_access_token"
        headers = {"Content-Type": "application/json"}
        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token"
        }
        logger.info(f"Refreshing access token for app_id: {self.app_id}")

        try:
            response = await httpx.post(token_url, json=payload, headers=headers)
            response.raise_for_status()
            data = await response.json()

            if data.get("code") == 0:
                logger.info("Successfully refreshed access token.")
                await self._store_token(data)
                return data
            else:
                error_msg = data.get("msg", "Unknown error")
                logger.error(f"Failed to refresh token: {error_msg} (Code: {data.get('code')})")
                raise OAuthManagerError(f"Failed to refresh token: {error_msg}")
        except Exception as e:
            logger.exception(f"Exception during token refresh: {e}")
            raise OAuthManagerError(f"Network or API error during token refresh: {e}")

    async def _store_token(self, token_data: Dict[str, Any]):
        """
        Mocks storing token data securely.

        In a real application, this would store tokens in a database,
        encrypted file, or secure key store.
        """
        logger.info("Mock storing token data (in-memory cache).")
        self._cached_token_data = token_data
        # In a real app, you might save to:
        # - Database: `db.save_tokens(user_id, token_data)`
        # - Encrypted file: `save_encrypted_json("tokens.json", token_data)`

    async def _retrieve_token(self) -> Optional[Dict[str, Any]]:
        """
        Mocks retrieving token data from storage.

        In a real application, this would retrieve tokens from secure storage.
        """
        logger.info("Mock retrieving token data from in-memory cache.")
        return self._cached_token_data
        # In a real app, you might load from:
        # - Database: `db.load_tokens(user_id)`
        # - Encrypted file: `load_encrypted_json("tokens.json")`

# Example Usage (for testing purposes)
async def main():
    manager = OAuthManager(
        app_id="cli_mock_oauth_app_id",
        app_secret="cli_mock_oauth_app_secret",
        redirect_uri="http://localhost:8000/callback"
    )

    try:
        # 1. Get authorization URL
        state = "random_state_string_123"
        auth_url = manager.get_authorization_url(state)
        print(f"Please open this URL in your browser to authorize: {auth_url}")
        print("After authorization, Feishu will redirect to your redirect_uri with a 'code' and 'state' parameter.")
        print("Simulating authorization code 'mock_auth_code_from_feishu' from redirect.")

        # 2. Simulate exchanging code for token
        mock_auth_code = "mock_auth_code_from_feishu"
        token_data = await manager.exchange_code_for_token(mock_auth_code)
        print("\n--- Initial Token Data ---")
        for key, value in token_data.items():
            print(f"{key}: {value}")
        print("--------------------------")

        # 3. Simulate refreshing token
        if "refresh_token" in token_data:
            print("\nSimulating token refresh...")
            refreshed_token_data = await manager.refresh_token(token_data["refresh_token"])
            print("\n--- Refreshed Token Data ---")
            for key, value in refreshed_token_data.items():
                print(f"{key}: {value}")
            print("----------------------------")
        else:
            print("No refresh token available for simulation.")

    except OAuthManagerError as e:
        logger.error(f"OAuth Manager error in example usage: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred in example usage: {e}")

if __name__ == "__main__":
    asyncio.run(main())