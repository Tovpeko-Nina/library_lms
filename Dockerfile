FROM python:3.12.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install Debian security updates available for the pinned base image, then
# remove package indexes so they do not remain in the runtime image.
# Fixed numeric IDs make file ownership predictable on every host.
RUN apt-get update \
    && apt-get upgrade --yes \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --gid 10001 lms \
    && useradd --uid 10001 --gid lms --no-create-home --shell /usr/sbin/nologin lms

# Dependencies are copied first so this expensive layer is reused when only
# application sources change. All Python versions are pinned in requirements.txt.
COPY requirements.txt ./
RUN python -m pip install --requirement requirements.txt

COPY --chown=10001:10001 . .

EXPOSE 8000
STOPSIGNAL SIGTERM

USER 10001:10001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
