package main

import (
	"utmn-map-backend/config"
	"utmn-map-backend/internal/rest"
)

func main() {
	cfg := config.Load()

	rest.Init(cfg)
}
