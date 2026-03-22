FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml README.md /app/
COPY src /app/src
COPY docs_site /app/docs_site

RUN pip install --upgrade pip && pip install .

ENV PYTHONPATH=/app/src

EXPOSE 8000

CMD ["uvicorn", "foundry.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
