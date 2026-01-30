#!/usr/bin/env bash
set -euo pipefail

# Beispiel-Skript: Build, Push und Deploy auf Google Cloud Run
# Benutze Umgebungsvariablen oder setze PROJECT und REGION vor dem Aufruf.

PROJECT=${PROJECT:-your-gcp-project}
REGION=${REGION:-europe-west1}
IMAGE=gcr.io/${PROJECT}/webshoptracker:latest
SERVICE=${SERVICE:-webshop-tracker}

echo "Build image $IMAGE"
docker build -t "$IMAGE" .

echo "Push image"
docker push "$IMAGE"

echo "Deploy to Cloud Run ($REGION)"
# Hinweis: Für Secrets empfiehlt sich Secret Manager + --update-secrets,
# hier ein einfaches Beispiel mit Umgebungsvariablen (CI/Secrets empfohlen).
gcloud run deploy "$SERVICE" \
  --image "$IMAGE" \
  --region "$REGION" \
  --platform managed \
  --memory 512Mi \
  --cpu 1 \
  --allow-unauthenticated \
  --set-env-vars "GMAIL_ADDRESS=${GMAIL_ADDRESS:-}","GMAIL_PASSWORD=${GMAIL_PASSWORD:-}"

echo "Deployed $SERVICE"
