package floorplan

import (
	"container/heap"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"math"
	"utmn-map-backend/internal/graph/models"
	"utmn-map-backend/internal/graph/services"
)

type FloorPlan struct {
}

func NewFloorPlan() *FloorPlan {
	return &FloorPlan{}
}
func (fp *FloorPlan) LoadFloorPlan(jsonFile string) (models.FloorPlan, error) {
	var floorPlan models.FloorPlan
	data, err := ioutil.ReadFile(jsonFile)
	if err != nil {
		return floorPlan, err
	}
	err = json.Unmarshal(data, &floorPlan)
	return floorPlan, err
}

func (fp *FloorPlan) BuildGraph(floorPlan map[string]interface{}) (*services.Graph, error) {
	g := services.NewGraph()

	// Добавляем узлы (объекты и пересечения)
	objects, ok := floorPlan["objects"].(map[string]interface{})
	if !ok {
		return nil, fmt.Errorf("invalid objects data")
	}

	for objID, objInfo := range objects {
		objMap, ok := objInfo.(map[string]interface{})
		if !ok {
			return nil, fmt.Errorf("invalid object info")
		}

		position, ok := objMap["position"].(map[string]interface{})
		if !ok {
			return nil, fmt.Errorf("invalid position data")
		}

		x, _ := position["x"].(float64)
		y, _ := position["y"].(float64)

		g.AddNode(objID, models.Position{X: x, Y: y})
	}

	// Добавляем рёбра с весами и line_id
	graphData, ok := floorPlan["graph"].(map[string]interface{})
	if !ok {
		return nil, fmt.Errorf("invalid graph data")
	}

	edges, ok := graphData["edges"].([]interface{})
	if !ok {
		return nil, fmt.Errorf("invalid edges data")
	}

	for _, edgeData := range edges {
		edgeMap, ok := edgeData.(map[string]interface{})
		if !ok {
			return nil, fmt.Errorf("invalid edge data")
		}

		fromNodeID, _ := edgeMap["from"].(string)
		toNodeID, _ := edgeMap["to"].(string)
		weight, _ := edgeMap["weight"].(float64)
		lineID, _ := edgeMap["line_id"].(string)

		fromNode, existsFrom := g.Nodes[fromNodeID]
		toNode, existsTo := g.Nodes[toNodeID]

		if !existsFrom || !existsTo {
			continue
		}

		g.AddEdge(fromNode, toNode, weight, lineID)
	}

	return g, nil
}
func (fp *FloorPlan) heuristic(node1, node2 *models.Node) float64 {
	return math.Hypot(node2.Position.X-node1.Position.X, node2.Position.Y-node1.Position.Y)
}
func (fp *FloorPlan) FindPath(g *services.Graph, startID, endID string) ([]string, error) {
	start := g.Nodes[startID]
	end := g.Nodes[endID]

	openSet := &services.AStarPriorityQueue{}
	heap.Push(openSet, &models.AStarNode{Node: start, GScore: 0, FScore: fp.heuristic(start, end)})

	cameFrom := make(map[string]*models.AStarNode)
	gScore := make(map[string]float64)
	fScore := make(map[string]float64)
	gScore[startID] = 0
	fScore[startID] = fp.heuristic(start, end)

	for openSet.Len() > 0 {
		current := heap.Pop(openSet).(*models.AStarNode)

		if current.Node.ID == endID {
			var path []string
			for current != nil {
				path = append([]string{current.Node.ID}, path...)
				current = current.Parent
			}
			var lineIDs []string
			for i := 0; i < len(path)-1; i++ {
				for _, edge := range g.Edges[path[i]] {
					if edge.To.ID == path[i+1] {
						lineIDs = append(lineIDs, edge.LineID)
					}
				}
			}
			return lineIDs, nil
		}

		for _, edge := range g.Edges[current.Node.ID] {
			neighbor := edge.To
			tentativeGScore := current.GScore + edge.Weight
			if _, found := gScore[neighbor.ID]; !found || tentativeGScore < gScore[neighbor.ID] {
				cameFrom[neighbor.ID] = current
				gScore[neighbor.ID] = tentativeGScore
				fScore[neighbor.ID] = gScore[neighbor.ID] + fp.heuristic(neighbor, end)
				heap.Push(openSet, &models.AStarNode{Node: neighbor, Parent: current, GScore: gScore[neighbor.ID], FScore: fScore[neighbor.ID]})
			}
		}
	}

	return nil, fmt.Errorf("no path found")
}
