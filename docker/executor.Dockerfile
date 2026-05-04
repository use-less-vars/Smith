FROM python:3.11-slim

RUN useradd -m -u 1000 agent && mkdir /workspace && chown agent:agent /workspace
WORKDIR /workspace
USER agent
CMD ["tail", "-f", "/dev/null"]