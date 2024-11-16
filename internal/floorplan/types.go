package floorplan

type Object struct {
	ID   string `json:"id"`
	Name string `json:"name"`
	X    int    `json:"x"`
	Y    int    `json:"y"`
}

type Intersection struct {
	ID string `json:"id"`
	X  int    `json:"x"`
	Y  int    `json:"y"`
}

type Edge struct {
	From   string  `json:"from"`
	To     string  `json:"to"`
	Weight float64 `json:"weight"`
	LineID string  `json:"line_id"`
}

type GraphData struct {
	Edges []Edge                  `json:"edges"`
	Nodes map[string]Intersection `json:"nodes"`
}

type FloorPlan struct {
	Objects       map[string]Object       `json:"objects"`
	Intersections map[string]Intersection `json:"intersections"`
	Graph         GraphData               `json:"graph"`
}
