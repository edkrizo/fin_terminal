import logging
from typing import Dict, Any
from fds.sdk.utils.authentication import ConfidentialClient

logger = logging.getLogger(__name__)

class FactSetAuthProvider:
    def __init__(self):
        """
        Initializes the Auth Provider. 
        Expects the 'FACTSET_CONFIG' environment variable to be set prior to init.
        """
        self._client = None

    @property
    def client(self) -> ConfidentialClient:
        if self._client is None:
            try:
                # When instantiated with no arguments, ConfidentialClient looks for 
                # the FACTSET_CONFIG environment variable containing the JSON string.
                self._client = ConfidentialClient()
            except Exception as e:
                logger.exception("Failed to initialize FactSet ConfidentialClient")
                raise e
        return self._client

    def __call__(self, context: Any = None) -> Dict[str, str]:
        """Returns the auth headers required for FactSet API calls."""
        try:
            token = self.client.get_access_token()
            return {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
        except Exception as e:
            logger.exception("Failed to retrieve FactSet access token")
            return {}

    get_headers = __call__

    def __deepcopy__(self, memo: Dict[int, Any]) -> "FactSetAuthProvider":
        # Drop the active socket for Reasoning Engine serialization
        return FactSetAuthProvider()