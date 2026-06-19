# FactoryOps dashboard. NEXT_PUBLIC_API_URL is baked at build time (Next inlines
# NEXT_PUBLIC_* vars), so pass it as a build arg from docker-compose.
FROM node:20-alpine AS build
WORKDIR /app
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
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
EXPOSE 3000
CMD ["npm", "run", "start"]
