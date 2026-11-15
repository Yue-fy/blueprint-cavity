FROM python:3.12-slim
ENV OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
RUN apt-get update && apt-get install -y --no-install-recommends curl ca-certificates git nodejs npm && rm -rf /var/lib/apt/lists/*
RUN npm install -g opencode-ai@1.19.5 && opencode --version
RUN pip install --no-cache-dir numpy==2.2.6
WORKDIR /workspace
COPY input.json /workspace/input.json
