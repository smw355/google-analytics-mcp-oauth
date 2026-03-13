"""OAuth 2.1 authentication layer using FastMCP's RemoteAuthProvider.

Validates incoming Google OAuth access tokens via the tokeninfo endpoint,
then exposes the bearer token for downstream GA API calls.
"""

import httpx
from fastmcp.server.auth import RemoteAuthProvider, TokenVerifier, AccessToken
from pydantic import AnyHttpUrl
from starlette.authentication import AuthenticationError

ANALYTICS_READONLY_SCOPE = "https://www.googleapis.com/auth/analytics.readonly"
_GOOGLE_TOKENINFO_URL = "https://www.googleapis.com/oauth2/v3/tokeninfo"
_GOOGLE_AUTH_SERVER = "https://accounts.google.com"


class GoogleTokenVerifier(TokenVerifier):
    """Validates a Google OAuth access token via the tokeninfo endpoint.

    On success, returns an AccessToken whose .token field is the raw
    bearer token — used by GA API clients downstream.
    """

    async def verify_token(self, token: str) -> AccessToken:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                _GOOGLE_TOKENINFO_URL,
                params={"access_token": token},
            )

        if resp.status_code != 200:
            raise AuthenticationError("Invalid or expired Google access token")

        data = resp.json()

        if "error" in data:
            raise AuthenticationError(f"Token validation failed: {data['error']}")

        scopes = data.get("scope", "").split()
        if ANALYTICS_READONLY_SCOPE not in scopes:
            raise AuthenticationError(
                f"Token is missing required scope: {ANALYTICS_READONLY_SCOPE}. "
                f"Present scopes: {scopes}"
            )

        return AccessToken(
            token=token,
            client_id=data.get("azp") or data.get("aud", ""),
            scopes=scopes,
            subject=data.get("sub"),
        )


def create_auth_provider(base_url: str) -> RemoteAuthProvider:
    """Creates a RemoteAuthProvider that advertises Google as the auth server.

    Obot (or any MCP client) uses the protected resource metadata this
    exposes to discover that tokens must come from accounts.google.com
    with the analytics.readonly scope.
    """
    return RemoteAuthProvider(
        token_verifier=GoogleTokenVerifier(),
        authorization_servers=[AnyHttpUrl(_GOOGLE_AUTH_SERVER)],
        base_url=base_url,
        scopes_supported=[ANALYTICS_READONLY_SCOPE],
        resource_name="Google Analytics MCP Server",
    )
