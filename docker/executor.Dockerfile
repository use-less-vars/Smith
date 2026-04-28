# Use a slim Python base
FROM python:3.11-slim

# Install system dependencies (LaTeX toolchain)
RUN apt-get update && apt-get install -y --no-install-recommends \
    texlive-latex-base \
    texlive-latex-extra \
    texlive-latex-recommended \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    texlive-publishers \
    texlive-science \
    texlive-pstricks \
    ghostscript \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better layer caching)
COPY docker/requirements-docker.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Create a non-root user (UID 1000, can be changed)
RUN useradd -m -u 1000 agent && \
    mkdir /workspace && chown agent:agent /workspace

# Set working directory
WORKDIR /workspace

# Switch to non-root user
USER agent

# Keep container alive (default command)
CMD ["tail", "-f", "/dev/null"]