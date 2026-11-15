FROM python:3.12-slim
ENV OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
RUN apt-get update && apt-get install -y --no-install-recommends poppler-utils tesseract-ocr curl ca-certificates git nodejs npm && rm -rf /var/lib/apt/lists/*
RUN npm install -g opencode-ai@1.19.5 && opencode --version
RUN pip install --no-cache-dir PyMuPDF==1.26.6 Pillow==12.0.0 numpy==2.2.6 shapely==2.1.2 opencv-python-headless==4.12.0.88
WORKDIR /workspace
COPY drawing.png /workspace/drawing.png
