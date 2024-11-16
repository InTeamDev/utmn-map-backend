package graph

import (
	"utmn-map-backend/internal/floorplan"
)

// BuildGraph creates a graph from the floor plan data
func BuildGraph(plan floorplan.FloorPlan) map[string]map[string]floorplan.Edge {
	graph := make(map[string]map[string]floorplan.Edge)
	for _, edge := range plan.Graph.Edges {
		if graph[edge.From] == nil {
			graph[edge.From] = make(map[string]floorplan.Edge)
		}
		graph[edge.From][edge.To] = edge
	}
	return graph
}

func FindPath(graph map[string]map[string]floorplan.Edge, start, end string) ([]string, error) {
	return []string{"line_id_1", "line_id_2"}, nil
}
