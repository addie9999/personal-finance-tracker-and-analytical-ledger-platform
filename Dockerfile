FROM node:22-alpine AS frontend
WORKDIR /ui
COPY frontend/ ./
RUN npm install --no-audit --no-fund && npm run build

FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY ledger.py reports.py seed.py ./
COPY --from=frontend /ui/dist ./frontend/dist
CMD ["uvicorn","ledger:app","--host","0.0.0.0","--port","8000"]
