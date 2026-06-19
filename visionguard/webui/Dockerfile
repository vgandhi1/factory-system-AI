# VisionGuard web UI (correction + trends). NEXT_PUBLIC_INFERENCE_URL is the
# browser-reachable inference API address, baked at build time.
FROM node:20-alpine AS build
WORKDIR /app
ARG NEXT_PUBLIC_INFERENCE_URL=http://localhost:8001
ENV NEXT_PUBLIC_INFERENCE_URL=$NEXT_PUBLIC_INFERENCE_URL
COPY package.json ./
RUN npm install
COPY . .
RUN npm run build

FROM node:20-alpine AS run
WORKDIR /app
ENV NODE_ENV=production
COPY --from=build /app/.next ./.next
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/package.json ./package.json
COPY --from=build /app/next.config.js ./next.config.js
COPY --from=build /app/public ./public
EXPOSE 3001
CMD ["npm", "run", "start"]
