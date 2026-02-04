# ClusterIQ Setup Guide

This guide will help you set up and run the ClusterIQ application.

## Prerequisites

- Python 3.9 or higher
- Node.js 18 or higher
- npm or yarn
- Databricks workspace access token
- OpenAI API key (or Azure OpenAI credentials)

## Backend Setup

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Create a `.env` file in the backend directory:**
   ```bash
   # Copy the example file
   # On Windows:
   copy .env.example .env
   
   # On macOS/Linux:
   cp .env.example .env
   ```

6. **Edit the `.env` file with your credentials:**
   ```env
   # Databricks Configuration
   DATABRICKS_HOST=https://your-workspace.cloud.databricks.com
   DATABRICKS_TOKEN=your-databricks-token-here

   # OpenAI Configuration
   OPENAI_API_KEY=your-openai-api-key-here
   OPENAI_MODEL=gpt-4-turbo-preview

   # Server Configuration
   BACKEND_PORT=8000
   CORS_ORIGINS=http://localhost:3000,http://localhost:5173
   ```

7. **Run the backend server:**
   ```bash
   python main.py
   ```
   
   Or using uvicorn directly:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

   The API will be available at `http://localhost:8000`

## Frontend Setup

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```
   
   Or using yarn:
   ```bash
   yarn install
   ```

3. **Create a `.env` file (optional, defaults to localhost:8000):**
   ```env
   VITE_API_URL=http://localhost:8000
   ```

4. **Start the development server:**
   ```bash
   npm run dev
   ```
   
   Or using yarn:
   ```bash
   yarn dev
   ```

   The frontend will be available at `http://localhost:3000`

## Getting Databricks Credentials

1. **Generate a Personal Access Token:**
   - Go to your Databricks workspace
   - Navigate to User Settings → Access Tokens
   - Click "Generate New Token"
   - Copy the token (you won't be able to see it again)

2. **Get your workspace URL:**
   - Your workspace URL should look like: `https://your-workspace.cloud.databricks.com`
   - Or for Azure: `https://adb-xxxxx.x.azuredatabricks.net`

## Getting OpenAI Credentials

1. **OpenAI API Key:**
   - Go to https://platform.openai.com/api-keys
   - Create a new API key
   - Copy the key

2. **Alternative: Azure OpenAI:**
   - Get your Azure OpenAI endpoint and API key from Azure Portal
   - Update the `.env` file with Azure credentials

## Running the Application

1. **Start the backend** (in one terminal):
   ```bash
   cd backend
   python main.py
   ```

2. **Start the frontend** (in another terminal):
   ```bash
   cd frontend
   npm run dev
   ```

3. **Open your browser:**
   - Navigate to `http://localhost:3000`
   - You should see the ClusterIQ dashboard

## Usage

1. **Dashboard:**
   - View overall statistics about jobs and clusters
   - Click "Run Analysis" to generate recommendations

2. **Recommendations:**
   - View AI-generated recommendations for cost optimization
   - Enable auto-refresh for real-time updates
   - Filter by severity (high, medium, low)

3. **Jobs:**
   - View all Databricks jobs
   - See job configurations and schedules

4. **Clusters:**
   - View all Databricks clusters
   - Monitor cluster states and configurations

## Troubleshooting

### Backend Issues

- **Import errors:** Make sure all dependencies are installed: `pip install -r requirements.txt`
- **Databricks connection errors:** Verify your token and workspace URL in `.env`
- **OpenAI errors:** Check your API key and ensure you have credits

### Frontend Issues

- **Connection errors:** Ensure the backend is running on port 8000
- **Build errors:** Clear node_modules and reinstall: `rm -rf node_modules && npm install`
- **CORS errors:** Check CORS_ORIGINS in backend `.env` matches your frontend URL

## API Endpoints

- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /api/jobs` - Get all jobs
- `GET /api/jobs/{job_id}/runs` - Get job runs
- `GET /api/clusters` - Get all clusters
- `GET /api/clusters/{cluster_id}/metrics` - Get cluster metrics
- `POST /api/analyze` - Run analysis
- `GET /api/recommendations` - Get cached recommendations
- `GET /api/recommendations/real-time` - Get real-time recommendations
- `GET /api/stats` - Get statistics

## Production Deployment

For production deployment:

1. **Backend:**
   - Use a production ASGI server like Gunicorn with Uvicorn workers
   - Set up proper environment variables
   - Configure HTTPS and security headers

2. **Frontend:**
   - Build the frontend: `npm run build`
   - Serve the `dist` folder with a web server like Nginx
   - Configure API proxy if needed

## Support

For issues or questions, please refer to the main README.md file.

