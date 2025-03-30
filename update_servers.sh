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

# Fetch all instances' names in the specified zone
servers=$(gcloud compute instances list --format="value(name)")

echo "List of servers that will be updated:"
for server in $servers; do
  echo "- $server"
done

for server in $servers; do
  echo "Executing command on instance: $server"
  gcloud compute ssh "$server" --command="$COMMANDS"
done

