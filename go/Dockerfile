FROM golang:1.27 AS builder
WORKDIR /app

COPY go.mod go.sum ./
RUN go mod download

COPY *.go ./
RUN CGO_ENABLED=0 go build -o server .

FROM alpine:latest
WORKDIR /app
COPY --from=builder /app/server .
CMD [ "./server" ]