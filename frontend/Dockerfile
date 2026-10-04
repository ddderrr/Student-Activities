# ---------- deps ----------
FROM node:22-alpine AS deps

WORKDIR /app

COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci --prefer-offline --fetch-retries=5


# ---------- dev: ใช้กับ compose.override.yml (Vite hot reload) ----------
FROM deps AS dev

COPY . .

EXPOSE 5173

# ถ้า frontend/src ยังไม่ถูก mount (เช่น Docker start container ก่อนที่ drive D: จะพร้อมหลังเปิดเครื่อง)
# ให้ออกไปก่อน แล้ว restart policy จะเริ่มใหม่ ไม่งั้น Vite จะรันต่อโดยไม่มีโค้ดให้เสิร์ฟ
CMD ["sh", "-c", "if [ ! -f src/main.js ]; then echo 'frontend/src is not mounted yet, retrying...'; sleep 3; exit 1; fi; exec node_modules/.bin/vite --host 0.0.0.0 --port 5173 --strictPort"]


# ---------- build ----------
FROM deps AS build

ARG VITE_API_URL=http://127.0.0.1:8000
ENV VITE_API_URL=$VITE_API_URL

COPY . .
RUN npm run build


# ---------- serve (default) ----------
FROM nginx:stable-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
