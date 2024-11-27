package handlers

import (
	"encoding/json"
	"log"
	"net/http"

	"github.com/InTeamDev/utmn-map-backend/internal/floorplan"
	"github.com/InTeamDev/utmn-map-backend/internal/graph/models"
	"github.com/InTeamDev/utmn-map-backend/internal/graph/services"
)

type FloorPlanHandler struct {
	graph     *services.Graph
	floorPlan *floorplan.FloorPlan
}

func NewFloorPlanHandler() *FloorPlanHandler {
	return &FloorPlanHandler{
		floorPlan: floorplan.NewFloorPlan(),
	}
}

// LoadFloorPlan loads the floor plan from a JSON file.
func (h *FloorPlanHandler) LoadFloorPlan(w http.ResponseWriter, r *http.Request) {
	query := r.URL.Query()
	file := query.Get("file")
	if file == "" {
		http.Error(w, "Missing 'file' query parameter", http.StatusBadRequest)
		return
	}

	floorPlanData, err := h.floorPlan.LoadFloorPlan(file)
	if err != nil {
		http.Error(w, "Failed to load floor plan: "+err.Error(), http.StatusInternalServerError)
		return
	}

	// Convert the loaded floorPlanData to map[string]interface{}
	floorPlanMap, err := convertToMap(floorPlanData)
	if err != nil {
		http.Error(w, "Failed to convert floor plan data: "+err.Error(), http.StatusInternalServerError)
		return
	}

	// Build the graph based on the converted floor plan map
	graph, err := h.floorPlan.BuildGraph(floorPlanMap)
	if err != nil {
		http.Error(w, "Failed to build graph: "+err.Error(), http.StatusInternalServerError)
		return
	}

	h.graph = graph

	w.WriteHeader(http.StatusOK)
	_, err = w.Write([]byte("Floor plan loaded successfully"))
	if err != nil {
		log.Printf("Error writing response: %v", err)
	}
}

// FindPath finds the shortest path between two nodes.
func (h *FloorPlanHandler) FindPath(w http.ResponseWriter, r *http.Request) {
	query := r.URL.Query()
	startIDStr := query.Get("start")
	endIDStr := query.Get("end")

	if startIDStr == "" || endIDStr == "" {
		http.Error(w, "Missing 'start' or 'end' query parameter", http.StatusBadRequest)
		return
	}

	if h.graph == nil {
		http.Error(w, "Graph not initialized", http.StatusInternalServerError)
		return
	}

	// Find the path using the A* algorithm
	lineIDs, err := h.floorPlan.FindPath(h.graph, startIDStr, endIDStr)
	if err != nil {
		http.Error(w, "Failed to find path: "+err.Error(), http.StatusInternalServerError)
		return
	}

	resp := map[string]interface{}{
		"line_ids": lineIDs,
	}
	err = json.NewEncoder(w).Encode(resp)
	if err != nil {
		log.Printf("Error encoding JSON response: %v", err)
		http.Error(w, "Failed to encode response", http.StatusInternalServerError)
		return
	}
}

// TODO (ilya) 26.11.24: Move to utils and add svg parser.
func convertToMap(floorPlan models.FloorPlan) (map[string]interface{}, error) {
	// Marshal the floor plan into JSON bytes
	data, err := json.Marshal(floorPlan)
	if err != nil {
		return nil, err
	}

	// Unmarshal the JSON bytes into a map[string]interface{}
	var result map[string]interface{}
	err = json.Unmarshal(data, &result)
	if err != nil {
		return nil, err
	}

	return result, nil
}
