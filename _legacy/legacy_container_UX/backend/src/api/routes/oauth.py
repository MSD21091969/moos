"""OAuth authentication routes for external API integrations."""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse

from src.api.dependencies import get_app_container, get_user_context
from src.core.container import AppContainer
from src.core.oauth_manager import GoogleOAuthFlow, OAuthManager
from src.models.context import UserContext

router = APIRouter(prefix="/oauth", tags=["OAuth"])


@router.get("/google/authorize")
async def google_authorize(
    scopes: str = Query("sheets", description="Comma-separated scopes: sheets, drive"),
    user_ctx: UserContext = Depends(get_user_context),
):
    """
    Initiate Google OAuth flow.

    **Scopes**:
    - `sheets`: Google Sheets read/write
    - `drive`: Google Drive read-only
    - `sheets,drive`: Both

    Redirects user to Google consent screen.
    """
    # Determine scopes
    scope_map = {
        "sheets": GoogleOAuthFlow.SHEETS_SCOPES,
        "drive": GoogleOAuthFlow.DRIVE_SCOPES,
    }

    requested_scopes = []
    for scope in scopes.split(","):
        scope = scope.strip()
        if scope in scope_map:
            requested_scopes.extend(scope_map[scope])

    if not requested_scopes:
        requested_scopes = GoogleOAuthFlow.SHEETS_SCOPES  # Default

    # Remove duplicates
    requested_scopes = list(set(requested_scopes))

    # Create OAuth flow
    from src.core.config import settings

    flow = GoogleOAuthFlow.create_flow(
        scopes=requested_scopes,
        redirect_uri=settings.google_oauth_redirect_uri,
    )

    # Get authorization URL
    auth_url = GoogleOAuthFlow.get_authorization_url(flow)

    # Store state in session (for CSRF protection)
    # TODO: Store flow state in Redis with TTL

    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def oauth_callback(
    code: str = Query(..., description="Authorization code from OAuth provider"),
    state: str = Query(None, description="CSRF state token"),
    error: str = Query(None, description="Error from OAuth provider"),
    user_ctx: UserContext = Depends(get_user_context),
    container: AppContainer = Depends(get_app_container),
):
    """
    OAuth callback handler.

    Exchanges authorization code for access token and stores in Firestore.

    **Not meant to be called directly** - Google redirects here after user consent.
    """
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")

    # TODO: Validate state token (CSRF protection)

    # Create flow (must match authorize flow)
    from src.core.config import settings

    flow = GoogleOAuthFlow.create_flow(
        scopes=GoogleOAuthFlow.SHEETS_SCOPES,  # TODO: Retrieve original scopes from state
        redirect_uri=settings.google_oauth_redirect_uri,
    )

    # Exchange code for credentials
    try:
        credentials = GoogleOAuthFlow.exchange_code(flow, code)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to exchange code: {str(e)}")

    # Store credentials
    oauth_manager = OAuthManager(container.firestore_client)
    await oauth_manager.store_token(
        user_id=user_ctx.user_id,
        provider="google",
        credentials=credentials,
    )

    # Redirect to success page
    return {
        "message": "Google account connected successfully",
        "user_id": user_ctx.user_id,
        "scopes": credentials.scopes,
    }


@router.get("/google/status")
async def google_status(
    user_ctx: UserContext = Depends(get_user_context),
    container: AppContainer = Depends(get_app_container),
):
    """
    Check Google OAuth status for current user.

    Returns whether user has valid Google token.
    """
    oauth_manager = OAuthManager(container.firestore_client)
    has_token = await oauth_manager.has_valid_token(
        user_id=user_ctx.user_id,
        provider="google",
    )

    return {
        "connected": has_token,
        "provider": "google",
        "user_id": user_ctx.user_id,
    }


@router.delete("/google/revoke")
async def google_revoke(
    user_ctx: UserContext = Depends(get_user_context),
    container: AppContainer = Depends(get_app_container),
):
    """
    Revoke Google OAuth token for current user.

    Removes stored credentials from Firestore.
    """
    oauth_manager = OAuthManager(container.firestore_client)
    await oauth_manager.revoke_token(
        user_id=user_ctx.user_id,
        provider="google",
    )

    return {
        "message": "Google account disconnected",
        "user_id": user_ctx.user_id,
    }
