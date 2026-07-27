package manim

import (
	"fmt"
	"io"
	"log"
	"os"
	"os/exec"
	"path/filepath"
)

// Handler handles Manim code execution and video generation
type Handler struct {
	OutputDir string
	logger    *log.Logger
}

// NewHandler creates a new Manim handler
func NewHandler(outputDir string) (*Handler, error) {
	// Create logger
	logger := log.New(os.Stdout, "[Manim] ", log.LstdFlags)
	logger.Println("Initializing Manim handler...")

	// 确保输出目录存在
	if err := os.MkdirAll(outputDir, 0755); err != nil {
		return nil, fmt.Errorf("failed to create output directory: %w", err)
	}

	// 检查输出目录是否可写
	testFile := filepath.Join(outputDir, ".test")
	if err := os.WriteFile(testFile, []byte("test"), 0644); err != nil {
		return nil, fmt.Errorf("output directory is not writable: %w", err)
	}
	os.Remove(testFile)

	// Check if Manim is installed
	if err := checkManimInstallation(logger); err != nil {
		return nil, fmt.Errorf("manim not installed: %w", err)
	}
	
	logger.Printf("Manim handler initialized with output directory: %s", outputDir)
	return &Handler{
		OutputDir: outputDir,
		logger:    logger,
	}, nil
}

// checkManimInstallation checks if Manim is installed and installs it if not
func checkManimInstallation(logger *log.Logger) error {
	logger.Println("Checking Manim installation...")

	// Check if manim module exists
	cmd := exec.Command("python", "-m", "manim", "--version")
	if err := cmd.Run(); err == nil {
		logger.Println("Manim is already installed")
		return nil
	}

	// Try to install Manim
	logger.Println("Manim not found. Attempting to install...")
	
	// Check if pip is available
	pipCmd := exec.Command("python", "-m", "pip", "--version")
	if err := pipCmd.Run(); err != nil {
		return fmt.Errorf("pip not found, please install Python and pip first")
	}

	// Install Manim
	logger.Println("Installing Manim...")
	installCmd := exec.Command("python", "-m", "pip", "install", "manim")
	installCmd.Stdout = os.Stdout
	installCmd.Stderr = os.Stderr
	
	if err := installCmd.Run(); err != nil {
		return fmt.Errorf("failed to install Manim: %w", err)
	}

	// Verify installation
	if err := exec.Command("python", "-m", "manim", "--version").Run(); err != nil {
		return fmt.Errorf("Manim installation failed: %w", err)
	}

	logger.Println("Manim installed successfully!")
	return nil
}

// GenerateVideo generates a video from Manim code
func (h *Handler) GenerateVideo(code string, sceneName string) (string, error) {
	h.logger.Printf("Generating video for scene: %s", sceneName)

	// Create temporary directory for Manim files
	tempDir, err := os.MkdirTemp("", "manim-*")
	if err != nil {
		return "", fmt.Errorf("failed to create temp directory: %w", err)
	}
	defer os.RemoveAll(tempDir)
	h.logger.Printf("Created temporary directory: %s", tempDir)

	// Write Manim code to file
	codeFile := filepath.Join(tempDir, "scene.py")
	if err := os.WriteFile(codeFile, []byte(code), 0644); err != nil {
		return "", fmt.Errorf("failed to write Manim code: %w", err)
	}
	h.logger.Printf("Wrote Manim code to: %s", codeFile)

	// Run Manim command using python -m manim
	h.logger.Println("Running Manim command...")
	cmd := exec.Command("python", "-m", "manim", "-qm", "-o", "scene", "--format", "mov", "--transparent", codeFile, sceneName)
	cmd.Dir = h.OutputDir  // 直接在输出目录下运行
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	if err := cmd.Run(); err != nil {
		return "", fmt.Errorf("failed to run Manim: %w", err)
	}
	h.logger.Println("Manim command completed successfully")

	// 视频已经生成在输出目录中，只需要返回路径
	outputPath := filepath.Join(h.OutputDir, "media", "videos", "scene", "720p30", "scene.mov")
	h.logger.Printf("Video generation completed: %s", outputPath)

	// 确保文件存在
	if _, err := os.Stat(outputPath); os.IsNotExist(err) {
		return "", fmt.Errorf("generated video file does not exist: %s", outputPath)
	}

	return outputPath, nil
}

// copyFile copies a file from src to dst
func copyFile(src, dst string) error {
	sourceFile, err := os.Open(src)
	if err != nil {
		return err
	}
	defer sourceFile.Close()

	destFile, err := os.Create(dst)
	if err != nil {
		return err
	}
	defer destFile.Close()

	_, err = io.Copy(destFile, sourceFile)
	if err != nil {
		return err
	}

	return destFile.Sync()
} 