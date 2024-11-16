package main

import (
	"fmt"
	"github.com/gorilla/mux"
	"net/http"
	"utmn-map-backend/config"
	"utmn-map-backend/internal/api"
	"utmn-map-backend/internal/floorplan"
)

func main() {
	cfg := config.Load()

	floorPlan, err := floorplan.Load(cfg.FloorPlanPath)
	if err != nil {
		fmt.Println("Error loading floor plan:", err)
		return
	}

	router := mux.NewRouter()
	api.SetupRoutes(router, floorPlan)

	fmt.Printf("Server running on %s\n", cfg.ServerAddress)
	http.ListenAndServe(cfg.ServerAddress, router)
}
