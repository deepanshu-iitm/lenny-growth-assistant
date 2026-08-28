FROM node:20-alpine AS build
WORKDIR /web
COPY package.json ./
COPY index.html tsconfig.json vite.config.ts ./
COPY src ./src
RUN npm install && node ./node_modules/vite/bin/vite.js build

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /web/dist /usr/share/nginx/html
EXPOSE 80
