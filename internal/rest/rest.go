package rest

import (
	"context"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/InTeamDev/utmn-map-backend/config"
	"github.com/InTeamDev/utmn-map-backend/internal/rest/handlers"
)

const (
	shutdownTimeout   = 5 * time.Second
	readHeaderTimeout = 10 * time.Second // Adjust as needed
)

func Init(cfg config.Config) error {
	mux := http.NewServeMux()

	floorPlanHandler := handlers.NewFloorPlanHandler()
	mux.HandleFunc("/floorplan/load", floorPlanHandler.LoadFloorPlan)
	mux.HandleFunc("/floorplan/path", floorPlanHandler.FindPath)

	handlerWithCORS := applyCORS(mux)

	server := &http.Server{
		Addr:              cfg.ServerAddress,
		Handler:           handlerWithCORS,
		ReadHeaderTimeout: readHeaderTimeout,
	}

	stop := make(chan os.Signal, 1)
	signal.Notify(stop, os.Interrupt, syscall.SIGTERM)

	go func() {
		log.Printf("Server is listening on %s", cfg.ServerAddress)
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			// Instead of logging and exiting, you might want to handle this differently
			log.Printf("Could not listen on %s: %v\n", cfg.ServerAddress, err)
			// Optionally, you can send the error to a channel to be handled in the main function
		}
	}()

	<-stop
	log.Println("Shutting down the server...")

	ctx, cancel := context.WithTimeout(context.Background(), shutdownTimeout)
	defer cancel()

	if err := server.Shutdown(ctx); err != nil {
		log.Printf("Server forced to shutdown: %v", err)
		return err // Return the error instead of exiting
	}

	log.Println("Server exiting")
	return nil
}

func applyCORS(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusOK)
			return
		}
		next.ServeHTTP(w, r)
	})
}
