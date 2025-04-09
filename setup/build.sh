docker-compose build

# Tag the images
docker tag ada_service:latest benderville/ada-service:latest
docker tag ada_view:latest benderville/ada-view:latest

# Push the backend service
docker push benderville/ada-service:latest
docker push benderville/ada-view:latest
