# Backend Connection Fix

## Issue
Frontend cannot connect to backend server.

## Root Cause
The frontend API service was configured to use `http://localhost:8000` directly, but Vite has a proxy configured. This can cause CORS or connection issues.

## Fixes Applied

### 1. Updated `frontend/src/services/api.js`
- ✅ Now uses Vite proxy in development mode (empty baseURL)
- ✅ Falls back to direct URL in production
- ✅ Added request/response interceptors for better error handling
- ✅ Added timeout configuration (30 seconds)
- ✅ Added console logging for debugging

### 2. Updated `frontend/vite.config.js`
- ✅ Enhanced proxy configuration with error handling
- ✅ Added logging for proxy requests
- ✅ Improved proxy rewrite rules

## How It Works Now

**Development Mode:**
- Frontend uses Vite proxy (`/api` → `http://localhost:8000/api`)
- No CORS issues
- Better error handling

**Production Mode:**
- Frontend connects directly to backend URL
- Requires CORS to be configured on backend

## Testing

1. **Restart the frontend server** to apply changes:
   ```bash
   # Stop current frontend (Ctrl+C)
   # Restart:
   cd frontend
   npm run dev
   ```

2. **Check browser console** (F12) for:
   - API request logs
   - Connection errors
   - Response data

3. **Test the connection:**
   - Open browser DevTools (F12)
   - Go to Network tab
   - Try to load the Dashboard
   - Check if API calls are successful

## Troubleshooting

### If still not connecting:

1. **Check backend is running:**
   ```powershell
   Invoke-WebRequest -Uri "http://localhost:8000/health"
   ```

2. **Check frontend proxy:**
   - Open browser console
   - Look for "API Request:" logs
   - Check Network tab for failed requests

3. **Try direct connection:**
   - Create `.env` file in `frontend/` directory:
   ```
   VITE_API_URL=http://localhost:8000
   ```
   - Restart frontend server

4. **Check CORS:**
   - Backend should allow `http://localhost:3000`
   - Check `backend/config.py` CORS_ORIGINS setting

## Expected Behavior

After restarting frontend:
- ✅ API calls should go through Vite proxy
- ✅ Console should show "API Request:" logs
- ✅ Dashboard should load data
- ✅ No CORS errors in console
