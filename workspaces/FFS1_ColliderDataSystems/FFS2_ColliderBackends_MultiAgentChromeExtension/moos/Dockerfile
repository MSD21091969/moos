FROM golang:1.23 AS build
WORKDIR /src

COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -trimpath -ldflags='-s -w' -o /out/kernel ./cmd/kernel

FROM scratch
WORKDIR /app

COPY --from=build /out/kernel /kernel
COPY --from=build /src/migrations /migrations

EXPOSE 8080 18789
ENTRYPOINT ["/kernel"]
