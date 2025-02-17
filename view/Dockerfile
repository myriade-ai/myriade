# Stage 1: Build the Vue.js application
FROM node:lts-alpine AS build-stage
WORKDIR /app
COPY package.json yarn.lock ./

RUN yarn install
COPY . .
RUN yarn build-only

# Stage 2: Serve the app with Nginx
FROM nginx:stable-alpine as production-stage
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Proxy api requests to the Flask app
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
