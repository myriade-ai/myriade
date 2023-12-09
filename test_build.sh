docker-compose down --volumes
docker-compose up -d
sleep 10
curl -f http://localhost:8080/api/databases
