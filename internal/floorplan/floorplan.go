package floorplan

import (
	"container/heap"
	"encoding/json"
	"errors"
	"math"
	"os"

	"github.com/InTeamDev/utmn-map-backend/internal/graph/models"
	"github.com/InTeamDev/utmn-map-backend/internal/graph/services"
)

type FloorPlan struct{}

func NewFloorPlan() *FloorPlan {
	return &FloorPlan{}
}

func (fp *FloorPlan) LoadFloorPlan(jsonFile string) (models.FloorPlan, error) {
	var floorPlan models.FloorPlan
	data, err := os.ReadFile(jsonFile)
	if err != nil {
		return floorPlan, err
	}
	err = json.Unmarshal(data, &floorPlan)
	return floorPlan, err
}

func (fp *FloorPlan) BuildGraph(floorPlan map[string]interface{}) (*services.Graph, error) {
	g := services.NewGraph()

	objects, objectsOK := floorPlan["objects"].(map[string]interface{})
	if !objectsOK {
		return nil, errors.New("invalid objects data")
	}

	for objID, objInfo := range objects {
		objMap, objMapOK := objInfo.(map[string]interface{})
		if !objMapOK {
			return nil, errors.New("invalid object info")
		}

		position, positionOK := objMap["position"].(map[string]interface{})
		if !positionOK {
			return nil, errors.New("invalid position data")
		}

		x, _ := position["x"].(float64)
		y, _ := position["y"].(float64)

		g.AddNode(objID, models.Position{X: x, Y: y})
	}

	graphData, graphDataOK := floorPlan["graph"].(map[string]interface{})
	if !graphDataOK {
		return nil, errors.New("invalid graph data")
	}

	edges, edgesOK := graphData["edges"].([]interface{})
	if !edgesOK {
		return nil, errors.New("invalid edges data")
	}

	for _, edgeData := range edges {
		edgeMap, edgeMapOK := edgeData.(map[string]interface{})
		if !edgeMapOK {
			return nil, errors.New("invalid edge data")
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
	start, existsStart := g.Nodes[startID]
	end, existsEnd := g.Nodes[endID]

	if !existsStart || !existsEnd {
		return nil, errors.New("start or end node does not exist")
	}

	openSet := &services.AStarPriorityQueue{}
	heap.Push(openSet, &models.AStarNode{
		Node:   start,
		GScore: 0,
		FScore: fp.heuristic(start, end),
		Parent: nil,
	})

	cameFrom := make(map[string]*models.AStarNode)
	gScore := map[string]float64{startID: 0}
	fScore := map[string]float64{startID: fp.heuristic(start, end)}

	for openSet.Len() > 0 {
		current, ok := heap.Pop(openSet).(*models.AStarNode)
		if !ok {
			return nil, errors.New("failed to pop from open set")
		}

		if current.Node.ID == endID {
			return fp.reconstructPath(current, g), nil
		}

		for _, edge := range g.Edges[current.Node.ID] {
			neighbor := edge.To
			tentativeGScore := current.GScore + edge.Weight

			if tentativeGScore < fp.getGScore(gScore, neighbor.ID) {
				cameFrom[neighbor.ID] = current
				gScore[neighbor.ID] = tentativeGScore
				fScore[neighbor.ID] = tentativeGScore + fp.heuristic(neighbor, end)
				heap.Push(openSet, &models.AStarNode{
					Node:   neighbor,
					Parent: current,
					GScore: gScore[neighbor.ID],
					FScore: fScore[neighbor.ID],
				})
			}
		}
	}

	return nil, errors.New("no path found")
}

func (fp *FloorPlan) reconstructPath(current *models.AStarNode, g *services.Graph) []string {
	var path []string
	var lineIDs []string
	for current != nil {
		path = append([]string{current.Node.ID}, path...)
		current = current.Parent
	}

	for i := range path[:len(path)-1] {
		from := path[i]
		to := path[i+1]
		for _, edge := range g.Edges[from] {
			if edge.To.ID == to {
				lineIDs = append(lineIDs, edge.LineID)
				break
			}
		}
	}

	return lineIDs
}

func (fp *FloorPlan) getGScore(gScore map[string]float64, nodeID string) float64 {
	if score, exists := gScore[nodeID]; exists {
		return score
	}
	return math.Inf(1)
}
