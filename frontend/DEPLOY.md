# Deployment Guide: CivicFix AI

This document provides step-by-step instructions to deploy the CivicFix AI platform. The architecture consists of a React/Vite frontend deployed on **Vercel**, and a FastAPI backend deployed on **Render**.

## 1. Deploying the Frontend (Vercel)

Vercel is ideal for our React Single Page Application (SPA). The project includes a `vercel.json` file to handle SPA routing, preventing 404 errors on page refreshes.

### Steps:
1. Push your repository to GitHub.
2. Log in to [Vercel](https://vercel.com/) and click **Add New Project**.
3. Import your GitHub repository.
4. Vercel will automatically detect the **Vite** framework and configure the build command (`npm run build`) and output directory (`dist`).
5. Expand the **Environment Variables** section and add the following:
   - `VITE_API_BASE_URL`: The URL of your deployed backend (e.g., `https://civicfix-api.onrender.com`).
6. Click **Deploy**.

## 2. Deploying the Backend (Render)

Render is perfect for our FastAPI backend. The project includes a `requirements.txt` and supports a lightweight fallback mode if the free tier runs out of memory for heavy ML models.

### Steps:
1. Log in to [Render](https://render.com/) and click **New +** -> **Web Service**.
2. Connect your GitHub repository.
3. Configure the service:
   - **Name**: `civicfix-api`
   - **Environment**: `Python 3`
   - **Root Directory**: `backend` (if you are deploying from a monorepo, specify `backend` here).
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Expand **Advanced** -> **Environment Variables** and add the following:
   - `ALLOWED_ORIGINS`: `https://your-vercel-app-url.vercel.app` (This secures CORS).
   - `USE_HEAVY_MODELS`: `false` (Recommended on the free tier to prevent memory crashes. Uses LLM fallback instead of local YOLO).
   - `OPENAI_API_KEY`: Your OpenAI key.
   - `GEMINI_API_KEY`: Your Gemini key.
   - `MAPBOX_ACCESS_TOKEN`: Your Mapbox key (if used in backend).
5. Choose the **Free** instance type and click **Create Web Service**.

## 3. Post-Deployment Checklist

- [ ] Update `ALLOWED_ORIGINS` in Render to exactly match your Vercel URL.
- [ ] Update `VITE_API_BASE_URL` in Vercel to exactly match your Render URL.
- [ ] Test the `/report` page on the live frontend to ensure the API call succeeds without CORS errors.
- [ ] Try refreshing the page on `/report` or `/track` to ensure `vercel.json` SPA routing is working.
