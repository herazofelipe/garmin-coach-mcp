FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Exercise catalog: generated from Garmin's official package at build time
# (not redistributed in this repo; see build_exercise_catalog.py).
COPY build_exercise_catalog.py .
RUN pip install --no-cache-dir "garmin-fit-sdk>=21,<22" \
    && python build_exercise_catalog.py \
    && pip uninstall -y garmin-fit-sdk

COPY garmin_mcp_server.py .
# Skills the server publishes over MCP (skills/<name>/SKILL.md).
COPY skills ./skills

# Render injects PORT; the server reads it.
ENV HOST=0.0.0.0
EXPOSE 8000
CMD ["python", "garmin_mcp_server.py"]
