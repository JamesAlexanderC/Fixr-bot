FROM python:3.12-slim

WORKDIR /usr/local/app

ENV PYTHONUNBUFFERED=1

# xvfb: camoufox launches a real (non-headless) Firefox by default, so a
# virtual display is required inside the container.
# tini: reaps zombie browser subprocesses spawned by camoufox and handles
# signals correctly since it (not our script) is what runs as PID 1.
RUN apt-get update && apt-get install -y --no-install-recommends xvfb tini \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# System libraries the camoufox/playwright Firefox build needs at runtime.
RUN playwright install-deps firefox

COPY . .
RUN chmod +x entrypoint.sh

RUN useradd -m app && chown -R app:app /usr/local/app
USER app

# Downloads the browser binary into the app user's cache dir, must run as
# the same user that will launch the browser at runtime.
RUN camoufox fetch

EXPOSE 8000

ENTRYPOINT ["/usr/bin/tini", "--", "./entrypoint.sh"]
CMD ["python", "main.py"]
