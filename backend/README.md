# ClusterIQ Backend

Backend service for ClusterIQ that integrates with Databricks APIs and uses AI for cost optimization analysis.

## Features

- **Databricks Integration:** Fetches jobs, clusters, and execution metrics via REST API
- **AI-Powered Analysis:** Uses OpenAI/Azure OpenAI via LangChain for intelligent recommendations (optional)
- **Rule-Based Fallback:** Provides basic analysis even without AI configuration
- **Real-time Updates:** Provides real-time recommendations via API endpoints
- **RESTful API:** Clean REST API for frontend consumption
- **Multiple Server Options:** Simple HTTP server or Flask-based server

## Architecture

```
simple_server.py     # Simple HTTP server (Python built-in, recommended)
main.py              # Flask application and routes (alternative)
databricks_client.py # Databricks REST API client
ai_agent.py          # AI analysis using LangChain OpenAI (optional, modern APIs)
config.py            # Configuration management
```

## Technology Stack

- **Python 3.9+**
- **Flask** (optional, for `main.py`)
- **LangChain OpenAI** - Direct LLM integration (pinned versions: 0.3.7, 0.2.8, 0.3.4)
- **OpenAI SDK** - For Azure OpenAI and standard OpenAI
- **Requests** - HTTP client for Databricks API
- **Python-dotenv** - Environment configuration

## LangChain Status

✅ **Modern Implementation:**
- Uses only `langchain-openai` for direct LLM calls
- No deprecated agent APIs
- Pinned versions for stability
- Optional - system works without LangChain (rule-based analysis)

## API Endpoints

See SETUP.md for complete API documentation.

## Configuration

Create a `.env` file with:
- **Required:** Databricks credentials (host, token)
- **Optional:** OpenAI API key (for AI-powered recommendations)
- **Optional:** Azure OpenAI credentials (endpoint, API key, deployment name)
- Server configuration (port, CORS origins)

**Note:** The system works without AI credentials, but will only provide basic rule-based recommendations.

## Running

### Option 1: Simple HTTP Server (Recommended)
```bash
python simple_server.py
```

### Option 2: Flask Server
```bash
python main.py
```

The server will start on port 8000 by default (configurable via `BACKEND_PORT` in `.env`).

## Dependencies

Install dependencies:
```bash
pip install -r requirements.txt
```

**Key Dependencies:**
- `langchain==0.3.7` - Core LangChain (optional, for AI features)
- `langchain-openai==0.2.8` - OpenAI integration (optional)
- `flask>=3.0.0` - Web framework (for `main.py` only)
- `flask-cors>=4.0.0` - CORS support for Flask
- `requests` - HTTP client
- `python-dotenv` - Environment variables

**Note:** LangChain dependencies are optional. The system will work with rule-based analysis if LangChain is not installed.
