FROM python:3.10.9-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtualenv and "autoactivate it" by enforcing its precedence by adding it to the PATH
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install requirments in virtualenv
RUN pip install --upgrade pip wheel
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt


WORKDIR /app
COPY bot bot

CMD ["python", "-m", "bot"]
