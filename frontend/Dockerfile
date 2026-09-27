# ---------- deps ----------
FROM node:22-alpine AS deps

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci


# ---------- dev: ใช้กับ compose.override.yml (Vite hot reload) ----------
FROM deps AS dev

COPY . .

EXPOSE 5173

CMD ["node_modules/.bin/vite", "--host", "0.0.0.0", "--port", "5173", "--strictPort"]


# ---------- build ----------
FROM deps AS build

COPY . .
RUN npm run build


# ---------- serve (default) ----------
FROM nginx:stable-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
