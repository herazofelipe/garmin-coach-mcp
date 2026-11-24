FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --require-hashes -r requirements.txt

# Exercise catalog: generated from Garmin's official package at build time
# (not redistributed in this repo; see build_exercise_catalog.py).
COPY build_exercise_catalog.py requirements-build.txt ./
RUN pip install --no-cache-dir --require-hashes -r requirements-build.txt \
    && python build_exercise_catalog.py \
    && pip uninstall -y garmin-fit-sdk

COPY garmin_mcp_server.py .
# Skills the server publishes over MCP (skills/<name>/SKILL.md).
COPY skills ./skills

# Render injects PORT; the server reads it.
ENV HOST=0.0.0.0
EXPOSE 8000
# Unprivileged user: the server writes nothing to disk.
RUN useradd --system --uid 10001 --no-create-home app
USER app
CMD ["python", "garmin_mcp_server.py"]
