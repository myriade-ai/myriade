# Build the dist folder
cd view && yarn build:website

# Copy the dist folder to the remote server using gcloud (server named "website")
gcloud compute ssh website -- "mkdir -p ~/temp_website"
gcloud compute scp --recurse view/dist/* website:~/temp_website/
gcloud compute ssh website -- "sudo cp -r ~/temp_website/* /var/www/myriade.ai/ && sudo chown -R www-data:www-data /var/www/myriade.ai/"
