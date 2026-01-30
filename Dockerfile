FROM mcr.microsoft.com/playwright/python:latest

WORKDIR /app

# Kopiere Abhängigkeiten zuerst (Layer-Caching)
COPY requirements.txt /app/
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Kopiere Projektdateien
COPY . /app

# Standardkommando
CMD ["python", "bot.py"]
