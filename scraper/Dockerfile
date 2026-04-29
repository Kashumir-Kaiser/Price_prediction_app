# Stage 1: build
FROM golang:1.26.2-alpine AS builder
RUN apk add --no-cache git ca-certificates
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o /scraper ./cmd/scraper

# Stage 2: test
FROM golang:1.26.2-alpine AS test
RUN apk add --no-cache git ca-certificates
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
# Default command – will run tests; compose can override if needed
CMD ["go", "test", "-v", "./..."]

# Stage 2: run
FROM scratch
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=builder /scraper /scraper
ENTRYPOINT ["/scraper"]