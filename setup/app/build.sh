# Remove the dist directory if it exists
rm -rf ./dist

# Build front end
cd ./view && yarn build && cd ..

# Copy .env.osx to .env for OSX app bundle (for PyInstaller)
cp ./service/.env.osx ./setup/app/.env

# Build the app
pyinstaller setup/app/app.spec

# Remove the .env file
rm ./setup/app/.env
