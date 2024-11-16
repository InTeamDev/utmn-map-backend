package config

import "os"

type Config struct {
	ServerAddress string
	FloorPlanPath string
}

func Load() Config {
	return Config{
		ServerAddress: getEnv("SERVER_ADDRESS", ":8080"),
		FloorPlanPath: getEnv("FLOOR_PLAN_PATH", "floor_plan.json"),
	}
}

func getEnv(key, defaultValue string) string {
	if value, exists := os.LookupEnv(key); exists {
		return value
	}
	return defaultValue
}
