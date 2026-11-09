FROM ghcr.io/home-assistant/base:3.24

# Canary runs only a Python offline shadow evaluator; no host telemetry daemon,
# Supervisor API, hardware devices, mutable HA config or production control loop.
RUN apk add --no-cache python3

COPY canary_runner.py /canary_runner.py
ENTRYPOINT ["python3", "-B", "/canary_runner.py"]
