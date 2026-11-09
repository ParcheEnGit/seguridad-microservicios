FROM node:22-alpine AS development
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

FROM development AS build
# Vite incrusta las variables VITE_* en el código al compilar.
ARG VITE_API_BASE_URL=/api
ARG VITE_GOOGLE_CLIENT_ID=
ARG VITE_KEYCLOAK_ENABLED=false
ARG VITE_SIMULATOR_INTERVAL_SECONDS=15
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL \
    VITE_GOOGLE_CLIENT_ID=$VITE_GOOGLE_CLIENT_ID \
    VITE_KEYCLOAK_ENABLED=$VITE_KEYCLOAK_ENABLED \
    VITE_SIMULATOR_INTERVAL_SECONDS=$VITE_SIMULATOR_INTERVAL_SECONDS
RUN npm run build

FROM nginx:1.29-alpine AS production
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 5173
