.PHONY: build test run lint

build:
	go build -o bin/scraper ./cmd/scraper

test:
	go test -v -race -count=1 ./...

run: build
	./bin/scraper

lint:
	gofmt -w .
	go vet ./...

clean:
	rm -rf bin/
