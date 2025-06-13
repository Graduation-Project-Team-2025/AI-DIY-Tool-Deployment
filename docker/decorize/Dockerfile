FROM ghcr.io/astral-sh/uv:0.7.13-python3.10-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    libavif-dev pkg-config \
    libjpeg-dev \
    gcc unzip zip \
    python3-dev \
    libxml2-dev \
    libxslt1-dev \
    libffi-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY src/requirements.txt .

ARG HUGGINGFACE_TOKEN

ENV HUGGINGFACE_TOKEN=${HUGGINGFACE_TOKEN}

RUN uv pip install --system --no-cache-dir huggingface_hub transformers

RUN python -c "from huggingface_hub import login; HUGGING_FACE_TOKEN = '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'; login(token=HUGGING_FACE_TOKEN)"
RUN python -c "from huggingface_hub import snapshot_download; snapshot_download(repo_id='openmmlab/upernet-convnext-small', use_auth_token=True, local_dir='./assets/models-weights/upernet-convnext-small')"


RUN uv pip install -r requirements.txt --system

COPY src/ .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
