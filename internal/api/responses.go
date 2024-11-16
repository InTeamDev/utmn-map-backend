package api

import (
	"encoding/json"
	"net/http"
)

// JSONResponse sends a JSON response with a custom status code
func JSONResponse(w http.ResponseWriter, status int, data interface{}) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	json.NewEncoder(w).Encode(data)
}

// JSONSuccess sends a 200 OK response with JSON data
func JSONSuccess(w http.ResponseWriter, data interface{}) {
	JSONResponse(w, http.StatusOK, data)
}

// JSONError sends an error message in JSON format with a specified status code
func JSONError(w http.ResponseWriter, status int, message string) {
	JSONResponse(w, status, map[string]string{"error": message})
}
