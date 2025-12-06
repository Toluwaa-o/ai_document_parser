FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies for Poetry
RUN pip install --no-cache-dir poetry

# Copy only pyproject.toml and poetry.lock first (caching)
COPY pyproject.toml poetry.lock* /app/

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Copy the rest of the application code
COPY . .

# Run the app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
