package services

import "github.com/InTeamDev/utmn-map-backend/internal/graph/models"

type Graph struct {
	Nodes map[string]*models.Node
	Edges map[string][]*models.Edge
}

func NewGraph() *Graph {
	return &Graph{
		Nodes: make(map[string]*models.Node),
		Edges: make(map[string][]*models.Edge),
	}
}

func (g *Graph) AddNode(id string, pos models.Position) {
	g.Nodes[id] = &models.Node{ID: id, Position: pos}
}

func (g *Graph) AddEdge(from, to *models.Node, weight float64, lineID string) {
	g.Edges[from.ID] = append(g.Edges[from.ID], &models.Edge{From: from, To: to, Weight: weight, LineID: lineID})
	g.Edges[to.ID] = append(g.Edges[to.ID], &models.Edge{From: to, To: from, Weight: weight, LineID: lineID})
}
