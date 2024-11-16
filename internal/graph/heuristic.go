package graph

import (
	"math"
	"utmn-map-backend/internal/floorplan"
)

// HeuristicFunc defines a function type for heuristic calculations
type HeuristicFunc func(node1, node2 floorplan.Intersection) float64

// EuclideanDistance calculates the straight-line distance between two intersections
func EuclideanDistance(node1, node2 floorplan.Intersection) float64 {
	dx := float64(node1.X - node2.X)
	dy := float64(node1.Y - node2.Y)
	return math.Sqrt(dx*dx + dy*dy)
}

// ManhattanDistance calculates the distance in a grid-like path (useful for grids)
func ManhattanDistance(node1, node2 floorplan.Intersection) float64 {
	dx := math.Abs(float64(node1.X - node2.X))
	dy := math.Abs(float64(node1.Y - node2.Y))
	return dx + dy
}
