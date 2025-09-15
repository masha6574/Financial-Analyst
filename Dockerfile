# Dockerfile

FROM python:3.11-slim

# Set environment variables, including the correct PATH for the root user's poetry install
ENV PYTHONUNBUFFERED=1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    PATH="/root/.local/bin:$PATH" \
    NLTK_DATA="/app/nltk_data"

# Install system dependencies as root
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    poppler-utils \
    tesseract-ocr \
    libgl1 \
    unzip && \
    rm -rf /var/lib/apt/lists/*

# Install Poetry as root
RUN curl -sSL https://install.python-poetry.org | python3 -

# Set the working directory
WORKDIR /app

# Copy dependency files and install them as root
COPY poetry.lock pyproject.toml ./
RUN poetry install --no-interaction --no-ansi --only main --no-root

# Copy the NLTK downloader script and run it as root
COPY scripts/download_nltk.py /app/scripts/download_nltk.py
RUN poetry run python /app/scripts/download_nltk.py

# Copy the rest of the application code
COPY . .

# --- NEW: Create a non-root user and set permissions at the end ---
RUN useradd -m appuser
# Give ownership of the entire app directory to our new user
RUN chown -R appuser:appuser /app
# Make the startup script executable
RUN chmod +x start.sh

# Switch to the new non-root user for the final command
USER appuser

EXPOSE 7860

# Run the application as the non-root user
CMD ["./start.sh"]