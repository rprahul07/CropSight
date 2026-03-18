# CropSight Backend

This is the FastAPI backend for the CropSight application, providing an AI pipeline to analyze crop health using Deep Learning, NDVI, and Post-Processing techniques.

## Architecture

1. **API Gateway (FastAPI)**: Receives image uploads and routes them through the pipeline.
2. **Preprocessing Service**: Resizes to 1024x1024, normalizes, and extracts channels.
3. **Deep Learning Service**: Uses DeepLabV3 + MobileNetV3 to generate a vegetation mask, filtering non-crop regions.
4. **NDVI Engine**: Extracts vegetation indices (NDVI/ExG).
5. **Fusion Engine**: Combines the DL mask with the NDVI index.
6. **Post-Processing & Clustering**: Uses KMeans to cluster, smooths, and maps severity.
7. **Recommendation System**: Provides actionable zones with severity and recommendations.

## Running the Application

### Locally
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Docker
```bash
docker build -t cropsight-backend .
docker run -p 8000:8000 cropsight-backend
```
