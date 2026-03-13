# Google Analytics MCP Server with OAuth 2.1

A remote [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server that gives AI agents read access to Google Analytics 4 data. Built with [FastMCP v3.1](https://github.com/jlowin/fastmcp), deployed to Google Cloud Run, and designed to work with [Obot](https://obot.ai) or any MCP client that supports OAuth 2.1 / RFC 9728 protected resource metadata.

Each user authenticates with their own Google account — the server never holds credentials. Tools only surface data the authenticated user can already access in the GA4 interface.

---

## Tools

| Tool | Description |
|------|-------------|
| `ga_get_account_summaries` | List all GA4 accounts and properties accessible to the user |
| `ga_get_property_details` | Get configuration details for a specific GA4 property |
| `ga_list_google_ads_links` | List Google Ads accounts linked to a property |
| `ga_list_property_annotations` | List annotations (notes) added to a property |
| `ga_run_report` | Run a standard GA4 analytics report with custom dimensions, metrics, filters, and date ranges |
| `ga_run_realtime_report` | Run a realtime report showing the last 30 minutes of activity |
| `ga_get_custom_dimensions_and_metrics` | List custom dimensions and metrics defined for a property |

---

## Architecture

```
Obot (or any MCP client)
  │
  │  OAuth 2.1 flow (Google as authorization server)
  ▼
Cloud Run  ── FastMCP / RemoteAuthProvider
  │            └─ RFC 9728 protected resource metadata
  │            └─ GoogleTokenVerifier (tokeninfo endpoint)
  │
  │  Bearer token passed directly to GA REST APIs
  ▼
Google Analytics Admin API  (v1beta / v1alpha)
Google Analytics Data API   (v1beta)
```

The server advertises Google as its authorization server via `/.well-known/oauth-protected-resource/mcp`. Obot discovers this, initiates the OAuth flow with Google on behalf of the user, and forwards the resulting bearer token to the MCP server on each request.

---

## Deploying to Google Cloud Run

### Prerequisites

- [Google Cloud CLI (`gcloud`)](https://cloud.google.com/sdk/docs/install) installed and authenticated
- [Docker](https://docs.docker.com/get-docker/) installed (with BuildKit)
- A Google Cloud project with billing enabled
- Artifact Registry API and Cloud Run API enabled in that project

### 1. Enable required APIs

```bash
gcloud config set project YOUR_PROJECT_ID

gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  --project YOUR_PROJECT_ID
```

### 2. Create an Artifact Registry repository

```bash
gcloud artifacts repositories create cloud-run-images \
  --repository-format=docker \
  --location=us-central1 \
  --project YOUR_PROJECT_ID
```

### 3. Authenticate Docker to Artifact Registry

```bash
gcloud auth configure-docker us-central1-docker.pkg.dev
```

### 4. Build and push the image

> **Apple Silicon (M1/M2/M3):** You must build for `linux/amd64` — Cloud Run does not support ARM images.

```bash
IMAGE="us-central1-docker.pkg.dev/YOUR_PROJECT_ID/cloud-run-images/analytics-mcp-oauth:v1"

docker build --platform linux/amd64 -t analytics-mcp-oauth:v1 .
docker tag analytics-mcp-oauth:v1 "$IMAGE"
docker push "$IMAGE"
```

### 5. Deploy to Cloud Run

On first deploy, use a placeholder base URL — you'll get the real URL after the service is created, then redeploy with it set correctly.

**First deploy** (to get the service URL):
```bash
gcloud run deploy analytics-mcp-oauth \
  --image "$IMAGE" \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars MCP_BASE_URL=placeholder \
  --project YOUR_PROJECT_ID
```

Copy the `Service URL` from the output (e.g. `https://analytics-mcp-oauth-XXXXXXXXXX.us-central1.run.app`).

**Second deploy** with the real base URL:
```bash
SERVICE_URL="https://analytics-mcp-oauth-XXXXXXXXXX.us-central1.run.app"

gcloud run deploy analytics-mcp-oauth \
  --image "$IMAGE" \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars MCP_BASE_URL="$SERVICE_URL" \
  --project YOUR_PROJECT_ID
```

### 6. Verify the deployment

```bash
curl https://YOUR_SERVICE_URL/.well-known/oauth-protected-resource/mcp
```

Expected response:
```json
{
  "resource": "https://YOUR_SERVICE_URL/mcp",
  "authorization_servers": ["https://accounts.google.com/"],
  "scopes_supported": ["https://www.googleapis.com/auth/analytics.readonly"],
  "bearer_methods_supported": ["header"],
  "resource_name": "Google Analytics MCP Server"
}
```

A request to `/mcp` without a token should return `HTTP 401`.

---

## Setting Up the Google OAuth App

The MCP server itself does not handle the OAuth login flow — it only validates tokens. The OAuth flow is delegated to your MCP client (Obot in the example below). You need a Google OAuth 2.0 Web Application client to give Obot the credentials it needs to initiate the flow.

### 1. Create the OAuth client in Google Cloud Console

1. Go to [APIs & Services → Credentials](https://console.cloud.google.com/apis/credentials) in your Google Cloud project
2. Click **Create Credentials → OAuth 2.0 Client ID**
3. Choose **Web application**
4. Set a name (e.g. `Analytics MCP Obot`)
5. Under **Authorized redirect URIs**, add your Obot callback URL:
   ```
   https://YOUR_OBOT_HOST/oauth/mcp/callback
   ```
6. Click **Create** and note the **Client ID** and **Client Secret**

### 2. Enable the Google Analytics APIs

```bash
gcloud services enable \
  analyticsadmin.googleapis.com \
  analyticsdata.googleapis.com \
  --project YOUR_PROJECT_ID
```

> These APIs need to be enabled in the same project used for OAuth. Users must also have access to at least one GA4 property in their Google account.

---

## Connecting to Obot

Obot uses [RFC 9728](https://datatracker.ietf.org/doc/html/rfc9728) protected resource metadata to automatically discover that this server requires Google OAuth. You only need to provide the MCP server URL and the Google OAuth credentials.

### 1. Add the MCP Server in Obot

1. In Obot, go to **MCP Servers** and click **Add**
2. Set the **Connect URL** to:
   ```
   https://YOUR_SERVICE_URL/mcp
   ```
3. Give it a name (e.g. `Google Analytics`)

### 2. Configure Static OAuth credentials

Because Google does not support OAuth dynamic client registration (RFC 7591), you must configure the Google OAuth client credentials manually in Obot.

1. On the MCP Server page, open **Advanced Configuration**
2. Find the **Static OAuth** section
3. Click **Configure Credentials** (or similar) next to the `https://accounts.google.com` authorization server entry
4. Enter:
   - **Client ID**: from the Google Cloud Console OAuth client you created above
   - **Client Secret**: from the Google Cloud Console OAuth client

5. Save

### 3. Authenticate as a user

When an agent using this MCP server is invoked for the first time, Obot will redirect the user through a standard Google OAuth consent screen requesting `analytics.readonly` access. After approval, the server can call GA4 APIs on that user's behalf for the duration of the session.

---

## Local Development

```bash
# Install dependencies
pip install -e .

# Run locally (no OAuth — useful for structural testing only)
MCP_BASE_URL=http://localhost:8080 python -m analytics_mcp_oauth
```

The server starts on port `8080` by default. Override with the `PORT` environment variable.

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `MCP_BASE_URL` | Yes | The public base URL of the deployed service (e.g. `https://YOUR_SERVICE_URL`). Used to construct the protected resource metadata. |
| `PORT` | No | Port to listen on. Defaults to `8080`. |

---

## Security Notes

- **Read-only by design.** All tools use `analytics.readonly` scope. No tool writes, modifies, or deletes any GA data.
- **No credential storage.** The server never stores OAuth tokens. Bearer tokens are validated on each request via Google's tokeninfo endpoint and forwarded directly to the GA REST APIs.
- **Per-user auth.** Each user authenticates independently. One user's token cannot be used by another.
- **Scope enforcement.** `GoogleTokenVerifier` explicitly checks that the `analytics.readonly` scope is present in the token before allowing any tool call. Tokens with missing or incorrect scopes are rejected with a `400` error.
- **No dynamic client registration.** Google does not support RFC 7591. OAuth credentials must be pre-configured as Static OAuth in your MCP client (see Obot setup above).

---

## Project Structure

```
├── Dockerfile
├── pyproject.toml
├── CATALOG.md                          # Obot catalog description
└── src/analytics_mcp_oauth/
    ├── __main__.py                     # Entry point — reads PORT, MCP_BASE_URL, starts server
    ├── server.py                       # FastMCP app + tool registration
    ├── auth.py                         # RemoteAuthProvider + GoogleTokenVerifier
    ├── ga_clients.py                   # API base URLs + auth header helper
    └── tools/
        ├── admin.py                    # Account summaries, property details, ads links, annotations
        ├── reporting.py                # ga_run_report
        ├── realtime.py                 # ga_run_realtime_report
        └── metadata.py                 # Custom dimensions & metrics
```

---

## License

MIT
