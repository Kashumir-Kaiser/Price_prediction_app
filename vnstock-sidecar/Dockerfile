# vnstock-sidecar/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install vnstock3 and fastapi for the sidecar API
RUN pip install --no-cache-dir vnstock3==3.2.1 fastapi uvicorn

COPY sidecar.py ./sidecar.py

EXPOSE 9001
CMD ["uvicorn", "sidecar:app", "--host", "0.0.0.0", "--port", "9001"]
