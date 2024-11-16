package graph

import (
	"container/heap"
	"errors"
	"math"
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

// Heuristic calculates the Euclidean distance between two nodes
func Heuristic(node1, node2 floorplan.Intersection) float64 {
	dx := float64(node2.X - node1.X)
	dy := float64(node2.Y - node1.Y)
	return math.Hypot(dx, dy)
}

// FindPath finds the shortest path between two nodes using A*
func FindPath(graph map[string]map[string]floorplan.Edge, nodes map[string]floorplan.Intersection, start, end string) ([]string, error) {
	// Ensure start and end nodes exist
	if _, exists := nodes[start]; !exists {
		return nil, errors.New("start node not found")
	}
	if _, exists := nodes[end]; !exists {
		return nil, errors.New("end node not found")
	}

	// A* algorithm variables
	openSet := &floorplan.PriorityQueue{}
	heap.Init(openSet)
	heap.Push(openSet, &floorplan.PriorityQueueItem{Node: start, Priority: 0})

	cameFrom := make(map[string]string) // Tracks the path
	gScore := make(map[string]float64)  // Cost from start to a node
	for key := range nodes {
		gScore[key] = math.Inf(1)
	}
	gScore[start] = 0

	fScore := make(map[string]float64) // Estimated cost from start to end
	for key := range nodes {
		fScore[key] = math.Inf(1)
	}
	fScore[start] = Heuristic(nodes[start], nodes[end])

	// Main loop
	for openSet.Len() > 0 {
		// Get the node with the lowest fScore
		current := heap.Pop(openSet).(*floorplan.PriorityQueueItem).Node

		// If we reached the goal
		if current == end {
			// Reconstruct the path and extract line IDs
			var path []string
			for current != start {
				prev := cameFrom[current]
				if edge, exists := graph[prev][current]; exists {
					path = append([]string{edge.LineID}, path...)
				}
				current = prev
			}
			return path, nil
		}

		// Process neighbors
		for neighbor, edge := range graph[current] {
			tentativeGScore := gScore[current] + edge.Weight

			if tentativeGScore < gScore[neighbor] {
				// Update path
				cameFrom[neighbor] = current
				gScore[neighbor] = tentativeGScore
				fScore[neighbor] = tentativeGScore + Heuristic(nodes[neighbor], nodes[end])

				// Add neighbor to the open set
				heap.Push(openSet, &floorplan.PriorityQueueItem{Node: neighbor, Priority: fScore[neighbor]})
			}
		}
	}

	// No path found
	return nil, errors.New("no path found")
}
