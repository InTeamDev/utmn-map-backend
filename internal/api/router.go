package api

import (
	"github.com/gorilla/mux"
	"utmn-map-backend/internal/floorplan"
)

var floorPlan floorplan.FloorPlan

func SetupRoutes(router *mux.Router, plan floorplan.FloorPlan) {
	floorPlan = plan
	router.HandleFunc("/get_route", getRouteHandler).Methods("POST")
	router.HandleFunc("/get_weights", getWeightsHandler).Methods("GET")
}
