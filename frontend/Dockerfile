# frontend/Dockerfile — REPLACE ENTIRELY
# ──────────────────────────────────────────────────────────────────────────────
# Stage 1: deps — install node_modules
# ──────────────────────────────────────────────────────────────────────────────
FROM node:20-alpine AS deps

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --frozen-lockfile

# ──────────────────────────────────────────────────────────────────────────────
# Stage 2: test — run vitest BEFORE building
# ──────────────────────────────────────────────────────────────────────────────
FROM deps AS test
COPY . .
# vitest is already in devDependencies — no extra install needed
ENTRYPOINT ["npx", "vitest"]
CMD ["run", "--reporter=verbose"]

# ──────────────────────────────────────────────────────────────────────────────
# Stage 3: builder — compile production bundle
# ──────────────────────────────────────────────────────────────────────────────
FROM deps AS builder
COPY . .
RUN npm run build

# ──────────────────────────────────────────────────────────────────────────────
# Stage 4: runtime — serve static files with nginx
# ──────────────────────────────────────────────────────────────────────────────
FROM nginx:1.25-alpine AS runtime
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
