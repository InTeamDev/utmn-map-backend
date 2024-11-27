package services

import "github.com/InTeamDev/utmn-map-backend/internal/graph/models"

type AStarPriorityQueue []*models.AStarNode

func (pq AStarPriorityQueue) Len() int           { return len(pq) }
func (pq AStarPriorityQueue) Less(i, j int) bool { return pq[i].FScore < pq[j].FScore }
func (pq AStarPriorityQueue) Swap(i, j int)      { pq[i], pq[j] = pq[j], pq[i] }

func (pq *AStarPriorityQueue) Push(x interface{}) {
	*pq = append(*pq, x.(*models.AStarNode))
}

func (pq *AStarPriorityQueue) Pop() interface{} {
	old := *pq
	n := len(old)
	item := old[n-1]
	*pq = old[0 : n-1]
	return item
}
