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
	// Load configuration
	cfg := config.Load()

	// Load the floor plan data
	floorPlan, err := floorplan.Load(cfg.FloorPlanPath)
	if err != nil {
		fmt.Println("Error loading floor plan:", err)
		return
	}

	// Set up the router with API routes
	router := mux.NewRouter()
	api.SetupRoutes(router, floorPlan)

	// Start the server
	fmt.Printf("Server running on %s\n", cfg.ServerAddress)
	http.ListenAndServe(cfg.ServerAddress, router)
}
