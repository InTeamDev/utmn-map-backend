package main

import (
	"log"

	"github.com/InTeamDev/utmn-map-backend/config"
	"github.com/InTeamDev/utmn-map-backend/internal/rest"
)

func main() {
	cfg := config.Load()

	if err := rest.Init(cfg); err != nil {
		log.Fatal(err)
	}
}
