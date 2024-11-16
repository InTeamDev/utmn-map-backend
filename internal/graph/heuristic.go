package graph

import (
	"math"
	"utmn-map-backend/internal/floorplan"
)

type HeuristicFunc func(node1, node2 floorplan.Intersection) float64

func EuclideanDistance(node1, node2 floorplan.Intersection) float64 {
	dx := float64(node1.X - node2.X)
	dy := float64(node1.Y - node2.Y)
	return math.Sqrt(dx*dx + dy*dy)
}

func ManhattanDistance(node1, node2 floorplan.Intersection) float64 {
	dx := math.Abs(float64(node1.X - node2.X))
	dy := math.Abs(float64(node1.Y - node2.Y))
	return dx + dy
}
