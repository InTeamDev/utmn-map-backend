package api

import (
	"encoding/json"
	"net/http"
	"utmn-map-backend/internal/floorplan"
	"utmn-map-backend/internal/graph"
)

// getRouteHandler handles the route-finding endpoint
func getRouteHandler(w http.ResponseWriter, r *http.Request) {
	var data map[string]string
	if err := json.NewDecoder(r.Body).Decode(&data); err != nil {
		http.Error(w, "Invalid request payload", http.StatusBadRequest)
		return
	}
	start, end := data["start"], data["end"]

	G := graph.BuildGraph(floorPlan)
	path, err := graph.FindPath(G, start, end)
	if err != nil || len(path) == 0 {
		http.Error(w, "Path not found", http.StatusNotFound)
		return
	}

	json.NewEncoder(w).Encode(map[string]interface{}{"line_ids": path})
}

// getWeightsHandler returns all edges with weights from the floor plan
func getWeightsHandler(w http.ResponseWriter, r *http.Request) {
	edges := make([]floorplan.Edge, 0)
	for _, edge := range floorPlan.Graph.Edges {
		edges = append(edges, edge)
	}
	json.NewEncoder(w).Encode(map[string]interface{}{"edges": edges})
}
