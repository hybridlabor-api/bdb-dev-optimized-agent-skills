package main

import (
	"fmt"
	"log"

	"github.com/sunqirui1987/ae-mcp/pkg/tools"
)

// BasicProject demonstrates the creation of a simple After Effects project
// with a basic composition
func main() {
	fmt.Println("Starting basic After Effects project demo...")

	// Get project information
	projectInfo, err := tools.GetProjectInfo()
	if err != nil {
		log.Fatalf("Error getting project info: %v", err)
	}
	fmt.Printf("Current project: %s\n", projectInfo["name"])

	// Create a new composition
	compName := "Demo Composition"
	width := 1920
	height := 1080
	duration := 10.0 // 10 seconds
	frameRate := 30.0

	compResult, err := tools.CreateComposition(compName, width, height, duration, frameRate)
	if err != nil {
		log.Fatalf("Error creating composition: %v", err)
	}
	fmt.Printf("Created composition: %s\n", compResult["name"])

	

	fmt.Println("Basic project demo completed successfully!")
} 