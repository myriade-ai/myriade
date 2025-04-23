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
  # Nginx
  echo "Copying setup/nginx.conf to instance: $server"
  gcloud compute scp setup/nginx.conf "$server":~/nginx.conf
  echo "Replacing DOMAIN_NAME in nginx.conf with $server.myriade.ai"
  gcloud compute ssh "$server" --command="sed -i 's/\${DOMAIN_NAME}/${server}.myriade.ai/g' nginx.conf"
  echo "Moving nginx.conf to /etc/nginx/sites-available/default and reloading nginx"
  gcloud compute ssh "$server" --command="sudo mv nginx.conf /etc/nginx/sites-available/default && sudo service nginx reload"

  # Restart nginx
  gcloud compute ssh "$server" --command="sudo service nginx restart"
  

  
  # Docker services
  echo "Copying docker-compose.yml to instance: $server"
  gcloud compute scp docker-compose.yml "$server":~/docker-compose.yml

  echo "Copying proxy/nginx.conf to instance: $server"
  gcloud compute scp proxy/nginx.conf "$server":~/proxy_nginx.conf
  echo "Moving proxy_nginx.conf to ~/proxy/nginx.conf"
  gcloud compute ssh "$server" --command="sudo mv proxy_nginx.conf ~/proxy/nginx.conf"

  echo "Executing command on instance: $server"
  gcloud compute ssh "$server" --command="$COMMANDS"
done

