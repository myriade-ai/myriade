#!/bin/bash

# Commands you want to execute remotely
COMMANDS=$(cat <<'EOF'
    echo "Running on $(hostname)"
    sudo docker compose pull
    sudo docker compose up -d
    sudo docker system prune --all --force
    sudo docker ps
EOF
)

# Check if a server list is provided as an argument
if [ -n "$1" ]; then
  # Use the provided list, splitting by comma
  IFS=',' read -r -a servers <<< "$1"
else
  # Fetch all instances' names in the specified zone if no argument is provided
  servers=$(gcloud compute instances list --format="value(name)")
fi

echo "List of servers that will be updated:"
for server in "${servers[@]}"; do
  echo "- $server"
done

for server in "${servers[@]}"; do
  echo "Copying docker-compose.yml to instance: $server"
  gcloud compute scp ada/docker-compose.yml "$server":~/docker-compose.yml
  echo "Executing command on instance: $server"
  gcloud compute ssh "$server" --command="$COMMANDS"
done

