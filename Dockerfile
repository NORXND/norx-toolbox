FROM python:3.14-slim

RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    git \
    ca-certificates \
    build-essential \
    assimp-utils \
    calibre \
    dasel \
    dcraw \
    dvisvgm \
    ffmpeg \
    ghostscript \
    graphicsmagick \
    imagemagick \
    inkscape \
    latexmk \
    libheif-examples \
    libjxl-tools \
    libreoffice \
    libva2 \
    libvips-tools \
    libemail-outlook-message-perl \
    lmodern \
    mupdf-tools \
    pandoc \
    poppler-utils \
    potrace \
    python3-numpy \
    python3-tinycss2 \
    resvg \
    texlive \
    texlive-fonts-recommended \
    texlive-latex-extra \
    texlive-latex-recommended \
    texlive-xetex \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

RUN ARCH=$(uname -m) && \
  if [ "$ARCH" = "aarch64" ]; then \
  VTRACER_ASSET="vtracer-aarch64-unknown-linux-musl.tar.gz"; \
  else \
  VTRACER_ASSET="vtracer-x86_64-unknown-linux-musl.tar.gz"; \
  fi && \
  curl -L -o /tmp/vtracer.tar.gz "https://github.com/visioncortex/vtracer/releases/download/0.6.4/${VTRACER_ASSET}" && \
  tar -xzf /tmp/vtracer.tar.gz -C /tmp/ && \
  mv /tmp/vtracer /usr/local/bin/vtracer && \
  chmod +x /usr/local/bin/vtracer && \
  rm /tmp/vtracer.tar.gz

WORKDIR /app

COPY pyproject.toml poetry.lock* requirements.txt* ./
RUN pip install --no-cache-dir --break-system-packages -e .

COPY . .


RUN useradd --create-home --shell /bin/bash norxtoolbox
RUN mkdir -p /data/norx-toolbox && chown -R norxtoolbox:norxtoolbox /app /data
USER norxtoolbox

EXPOSE 8000

CMD ["python", "-m", "norx_toolbox.main"]