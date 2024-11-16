package config

import "os"

// Config holds configuration values for the application
type Config struct {
	ServerAddress string
	FloorPlanPath string
}

// Load initializes configuration from environment variables
func Load() Config {
	return Config{
		ServerAddress: getEnv("SERVER_ADDRESS", ":8080"),
		FloorPlanPath: getEnv("FLOOR_PLAN_PATH", "floor_plan.json"),
	}
}

// getEnv retrieves an environment variable or returns a default value
func getEnv(key, defaultValue string) string {
	if value, exists := os.LookupEnv(key); exists {
		return value
	}
	return defaultValue
}
