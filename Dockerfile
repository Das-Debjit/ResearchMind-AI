FROM python:3.11-slim

RUN useradd -m -u 1000 user

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY --chown=user backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir --upgrade -r backend/requirements.txt

COPY --chown=user backend/ backend/

RUN mkdir -p backend/data/uploaded_papers backend/data/faiss_index backend/logs && \
    chown -R user:user backend/data backend/logs

USER user
ENV PATH="/home/user/.local/bin:$PATH"
ENV HOME=/home/user

WORKDIR /app/backend

EXPOSE 7860

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"]