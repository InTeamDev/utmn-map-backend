package models

type Position struct {
	X, Y float64
}

type Node struct {
	ID       string
	Position Position
}

type Edge struct {
	From, To *Node
	Weight   float64
	LineID   string
}

type AStarNode struct {
	Node   *Node
	Parent *AStarNode
	GScore float64
	FScore float64
}

type FloorPlan struct {
	Objects       map[string]ObjectInfo       `json:"objects"`
	Intersections map[string]IntersectionInfo `json:"intersections"`
	Graph         GraphData                   `json:"graph"`
}

type ObjectInfo struct {
	Position Position `json:"position"`
	Type     string   `json:"type"`
	Text     string   `json:"text"`
}

type IntersectionInfo struct {
	Position Position `json:"position"`
}

type GraphData struct {
	Edges []EdgeData `json:"edges"`
}

type EdgeData struct {
	From   string  `json:"from"`
	To     string  `json:"to"`
	Weight float64 `json:"weight"`
	LineID string  `json:"line_id"`
}
