# Cost Control

## 1. Purpose

This project is designed to run within a small GCP trial budget for a recruitment challenge. The deployment keeps the runtime small, avoids always-on infrastructure, and uses only the cloud services needed to expose the Dockerized FastAPI API.

## 2. Default Deployment Cost-Related Choices

- Cloud Run only.
- Minimum instances set to `0`.
- Maximum instances limited to `3`.
- Memory set to `512Mi`.
- CPU set to `1`.
- No GPU.
- No GKE or Kubernetes.
- No always-on VM.
- No BigQuery or Vertex AI calls unless Stage 8 managed retrieval is explicitly enabled.
- Small synthetic catalog packaged in the container.

## 3. Recommended GCP Setup

- Use a dedicated GCP project.
- Set a billing budget.
- Set billing alerts.
- Keep the region consistent across Artifact Registry and Cloud Run.
- Delete the Cloud Run service after review if it is not needed.

## 4. Why Min Instances = 0

`min-instances=0` allows Cloud Run to scale the service to zero when there is no traffic. This avoids idle runtime cost for demo usage. The tradeoff is that the first request after an idle period may experience a cold start.

## 5. What May Increase Cost Later

- Vertex AI inference.
- Embedding generation.
- BigQuery scans.
- BigQuery Vector Search queries.
- BigQuery vector index build and maintenance.
- Load testing.
- Minimum instances greater than `0`.
- High traffic.
- Large Artifact Registry storage.

## 6. Cleanup

Delete the Cloud Run service after the demo if it is not needed:

```bash
gcloud run services delete "${SERVICE_NAME}" \
  --region="${GCP_REGION}" \
  --project="${GCP_PROJECT_ID}"
```

Delete unused container images if needed. Optionally delete the Artifact Registry repository after the challenge:

```bash
gcloud artifacts repositories delete "${ARTIFACT_REPOSITORY}" \
  --location="${GCP_REGION}" \
  --project="${GCP_PROJECT_ID}"
```
