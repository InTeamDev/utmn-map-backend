package rest

import (
	"log"
	"net/http"
	"utmn-map-backend/config"
	"utmn-map-backend/internal/rest/handlers"
)

func Init(cfg config.Config) {
	mux := http.NewServeMux()

	floorPlanHandler := handlers.NewFloorPlanHandler()
	mux.HandleFunc("/floorplan/load", floorPlanHandler.LoadFloorPlan)
	mux.HandleFunc("/floorplan/path", floorPlanHandler.FindPath)

	cors := func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Access-Control-Allow-Origin", "*")
			w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
			w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
			if r.Method == "OPTIONS" {
				w.WriteHeader(http.StatusOK)
				return
			}
			next.ServeHTTP(w, r)
		})
	}

	handlerWithCORS := cors(mux)

	err := http.ListenAndServe(cfg.ServerAddress, handlerWithCORS)
	if err != nil {
		log.Fatal("[error] failed to start server:", err)
	}
}
