# syntax=docker/dockerfile:1
# Complaint-router image: API + CLI, with trained models baked in at build time.
# Builds with Docker Desktop, Podman Desktop (podman build) and Rancher Desktop.
# Runs as non-root and is compatible with OpenShift's arbitrary UIDs (group 0).
#
#   docker build -t fde-01-foundations:local .                              # Banking77 models
#   docker build --build-arg TRAIN_DATASET=fixture -t fde-01-foundations:local .   # offline
#   docker build --build-arg TRAIN_TRANSFORMER=true ...                    # + DistilBERT (slow)

FROM python:3.12-slim AS build
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /build
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip wheel --no-deps --wheel-dir /wheels .

FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 PORT=8000 MODEL_DIR=/app/models \
    LLM_PROVIDERS_FILE=/app/config/providers.yaml OMP_NUM_THREADS=1
WORKDIR /app
RUN useradd --uid 10001 --gid 0 --no-create-home --shell /usr/sbin/nologin app
# CPU-only PyTorch: about 10x smaller than the default CUDA build.
RUN pip install --index-url https://download.pytorch.org/whl/cpu "torch>=2.4"
# The PyTorch index ships an old setuptools with known CVEs; take the patched one from PyPI.
RUN pip install --upgrade "setuptools>=83"
COPY --from=build /wheels /wheels
RUN pip install /wheels/*.whl && rm -rf /wheels
COPY app ./app
COPY config ./config

FROM runtime AS train
ARG TRAIN_DATASET=banking77
ARG TRAIN_TRANSFORMER=false
# `.starter` exists only in learner starter repos: there, training may fail until the
# exercises are done, and the image is still built (it serves 503 until a model exists).
COPY pyproject.toml .starte[r] ./
RUN set -e; mkdir -p /app/models; \
    train() { complaint-router --data-dir /tmp/data train --dataset "$TRAIN_DATASET" \
              --model-dir /app/models "$@"; }; \
    if [ -f .starter ]; then \
      (train --model baseline && train --model mlp) || echo "starter: models not trained yet"; \
    else \
      train --model baseline && train --model mlp; \
      if [ "$TRAIN_TRANSFORMER" = "true" ]; then \
        pip install "transformers>=4.45" "tokenizers>=0.20" && train --model transformer; \
      fi; \
    fi; \
    rm -rf /tmp/data

FROM runtime AS final
ARG TRAIN_TRANSFORMER=false
RUN if [ "$TRAIN_TRANSFORMER" = "true" ]; then \
      pip install "transformers>=4.45" "tokenizers>=0.20"; fi
COPY --from=train /app/models /app/models
RUN chgrp -R 0 /app && chmod -R g=u /app
USER 10001
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD python -c "import urllib.request,os;urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\",\"8000\")}/health/live')"
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
