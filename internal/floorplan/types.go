package floorplan

// Object represents an individual object in the floor plan
type Object struct {
	ID   string `json:"id"`
	Name string `json:"name"`
	X    int    `json:"x"`
	Y    int    `json:"y"`
}

// Intersection represents a connecting point between paths or rooms
type Intersection struct {
	ID string `json:"id"`
	X  int    `json:"x"`
	Y  int    `json:"y"`
}

// Edge represents a path or connection between two points with a weight
type Edge struct {
	From     string  `json:"from"`
	To       string  `json:"to"`
	Distance float64 `json:"distance"` // Distance between From and To
}

// GraphData holds all edges and intersections, structuring the graph
type GraphData struct {
	Edges []Edge                  `json:"edges"`
	Nodes map[string]Intersection `json:"nodes"` // Mapping ID to intersection
}

// FloorPlan represents the entire floor plan with objects and paths
type FloorPlan struct {
	Objects       map[string]Object       `json:"objects"`
	Intersections map[string]Intersection `json:"intersections"`
	Graph         GraphData               `json:"graph"`
}
