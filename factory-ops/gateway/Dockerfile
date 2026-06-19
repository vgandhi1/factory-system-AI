# Multi-stage build for the FactoryOps ingestion gateway.
FROM golang:1.25-alpine AS build
WORKDIR /src
COPY go.mod go.sum* ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -o /out/gateway .

FROM gcr.io/distroless/static-debian12
COPY --from=build /out/gateway /gateway
ENTRYPOINT ["/gateway"]
