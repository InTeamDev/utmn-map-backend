package floorplan

import (
	"encoding/json"
	"os"
)

// Load reads and decodes the floor plan JSON file
func Load(filePath string) (FloorPlan, error) {
	file, err := os.Open(filePath)
	if err != nil {
		return FloorPlan{}, err
	}
	defer file.Close()

	var plan FloorPlan
	decoder := json.NewDecoder(file)
	err = decoder.Decode(&plan)
	return plan, err
}
