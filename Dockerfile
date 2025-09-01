# Use an official lightweight Python image.
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Set environment variables for Poetry
ENV POETRY_NO_INTERACTION=1
ENV POETRY_VIRTUALENVS_IN_PROJECT=true

# Install Poetry
RUN pip install poetry

# Copy the dependency files
COPY pyproject.toml poetry.lock ./

# Install project dependencies (production only)
RUN poetry install --no-root --no-dev

# Copy the rest of the application code
COPY . .

# Run our tree-sitter build script
RUN poetry run python build.py

# Expose the port the app runs on
EXPOSE 8000

# Run the web server
CMD ["poetry", "run", "uvicorn", "--host", "0.0.0.0", "--port", "8000", "codecompass_engine.main:app"]