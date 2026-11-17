FROM node:22.14.0-alpine AS build
WORKDIR /src
RUN npm install --global pnpm@10.6.2
COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile
COPY frontend/ ./
RUN pnpm build

FROM nginx:1.28.0-alpine
COPY deploy/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /src/dist /usr/share/nginx/html
COPY licenses/frontend-LICENSES.txt /usr/share/nginx/html/third-party-licenses.txt
EXPOSE 8080
