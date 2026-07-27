package tools

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/sunqirui1987/ae-mcp/pkg/ae"
	"github.com/sunqirui1987/ae-mcp/pkg/manim"
)

// ManimResult represents the result of a Manim operation
type ManimResult struct {
	VideoPath string                 `json:"videoPath"`
	LayerID   string                 `json:"layerId,omitempty"`
	Metadata  map[string]interface{} `json:"metadata,omitempty"`
}

// ManimTool handles Manim-related operations
type ManimTool struct {
	handler *manim.Handler
}

// NewManimTool creates a new Manim tool
func NewManimTool(outputDir string) (*ManimTool, error) {
	handler, err := manim.NewHandler(outputDir)
	if err != nil {
		return nil, fmt.Errorf("failed to create Manim handler: %w", err)
	}

	return &ManimTool{
		handler: handler,
	}, nil
}

// CreateManimLayer creates a new layer from Manim code
func (t *ManimTool) CreateManimLayer(code string, sceneName string) (ManimResult, error) {
	// Generate video from Manim code
	videoPath, err := t.handler.GenerateVideo(code, sceneName)
	if err != nil {
		return ManimResult{}, fmt.Errorf("failed to generate video: %w", err)
	}

	// 确保文件存在
	if _, err := os.Stat(videoPath); os.IsNotExist(err) {
		return ManimResult{}, fmt.Errorf("generated video file does not exist: %s", videoPath)
	}

	// 转换为 After Effects 可用的路径格式
	aeVideoPath := filepath.ToSlash(videoPath)
	if !filepath.IsAbs(aeVideoPath) {
		absPath, err := filepath.Abs(aeVideoPath)
		if err != nil {
			return ManimResult{}, fmt.Errorf("failed to get absolute path: %w", err)
		}
		aeVideoPath = filepath.ToSlash(absPath)
	}

	// Create ExtendScript to import the video and get layer information
	script := fmt.Sprintf(`
		try {
			// 检查是否有活动的合成
			var comp = app.project.activeItem;
			if (!comp || !(comp instanceof CompItem)) {
				// 如果没有活动的合成，创建一个新的
				comp = app.project.items.addComp("%s", 1920, 1080, 1, 10, 30);
				if (!comp) {
					throw new Error("Failed to create composition");
				}
			}

			// 打印当前合成信息
			$.writeln("Current composition: " + comp.name);
			$.writeln("Number of layers: " + comp.layers.length);
			for (var i = 1; i <= comp.layers.length; i++) {
				var layer = comp.layers[i];
				$.writeln("Layer " + i + ": " + layer.name + " (Type: " + layer.matchName + ")");
			}

			// 检查文件是否存在
			var videoFile = new File("%s");
			if (!videoFile.exists) {
				throw new Error("Video file does not exist: " + "%s");
			}

			var importOptions = new ImportOptions(videoFile);
			if (!importOptions.canImportAs(ImportAsType.FOOTAGE)) {
				throw new Error("Cannot import video file: " + "%s");
			}

			// 导入视频文件
			var footageItem = app.project.importFile(importOptions);
			$.writeln("Imported footage: " + footageItem.name);

			// 添加到合成
			var layer = comp.layers.add(footageItem);
			layer.name = "%s";
			$.writeln("Added layer: " + layer.name);

			// Return layer information
			var result = {
				"videoPath": "%s",
				"layerId": layer.id.toString(),
				"metadata": {
					"width": layer.width,
					"height": layer.height,
					"duration": layer.outPoint - layer.inPoint,
					"startTime": layer.startTime
				}
			};
			return returnjson(result);
		} catch (err) {
			$.writeln("Error: " + err.toString());
			throw new Error(err.toString());
		}
	`, sceneName, aeVideoPath, aeVideoPath, aeVideoPath, sceneName, aeVideoPath)

	// Execute the script
	result, err := ae.ExecuteScript(script)
	if err != nil {
		return ManimResult{}, fmt.Errorf("failed to create layer: %w", err)
	}

	// 检查结果是否为空
	if result == nil {
		return ManimResult{}, fmt.Errorf("script execution returned nil result")
	}

	// 尝试将结果转换为字符串
	resultStr, ok := result.(string)
	if !ok {
		return ManimResult{}, fmt.Errorf("script execution returned invalid result type: %T", result)
	}

	// Parse the result
	var manimResult ManimResult
	if err := json.Unmarshal([]byte(resultStr), &manimResult); err != nil {
		return ManimResult{}, fmt.Errorf("failed to parse layer information: %w", err)
	}

	return manimResult, nil
}

// GetManimLayerInfo gets information about a Manim layer
func (t *ManimTool) GetManimLayerInfo(layerID string) (ManimResult, error) {
	script := fmt.Sprintf(`
		try {
			var comp = app.project.activeItem;
			if (!comp || !(comp instanceof CompItem)) {
				throw new Error("No active composition");
			}

			var layer = comp.layer(%s);
			if (!layer) {
				throw new Error("Layer not found");
			}

			var result = {
				"layerId": layer.id.toString(),
				"layerName": layer.name,
				"layerIndex": layer.index,
				"metadata": {
					"width": layer.width,
					"height": layer.height,
					"duration": layer.outPoint - layer.inPoint,
					"startTime": layer.startTime
				}
			};
			return returnjson(result);
		} catch (err) {
			throw new Error(err.toString());
		}
	`, layerID)

	result, err := ae.ExecuteScript(script)
	if err != nil {
		return ManimResult{}, fmt.Errorf("failed to get layer information: %w", err)
	}

	var manimResult ManimResult
	if err := json.Unmarshal([]byte(result.(string)), &manimResult); err != nil {
		return ManimResult{}, fmt.Errorf("failed to parse layer information: %w", err)
	}

	return manimResult, nil
}

// UpdateManimLayer updates a Manim layer with new code
func (t *ManimTool) UpdateManimLayer(layerID string, code string, sceneName string) (ManimResult, error) {
	// Generate new video
	newResult, err := t.CreateManimLayer(code, sceneName)
	if err != nil {
		return ManimResult{}, fmt.Errorf("failed to generate new video: %w", err)
	}

	// Replace the old layer with the new one
	script := fmt.Sprintf(`
		try {
			var comp = app.project.activeItem;
			if (!comp || !(comp instanceof CompItem)) {
				throw new Error("No active composition");
			}

			var oldLayer = comp.layer(%s);
			if (!oldLayer) {
				throw new Error("Old layer not found");
			}

			var newLayer = comp.layer(%s);
			if (!newLayer) {
				throw new Error("New layer not found");
			}

			// Copy properties from old layer to new layer
			newLayer.startTime = oldLayer.startTime;
			newLayer.outPoint = oldLayer.outPoint;
			newLayer.position = oldLayer.position;
			newLayer.scale = oldLayer.scale;
			newLayer.rotation = oldLayer.rotation;
			newLayer.opacity = oldLayer.opacity;

			// Remove old layer
			oldLayer.remove();

			var result = {
				"layerId": newLayer.id.toString(),
				"layerName": newLayer.name,
				"layerIndex": newLayer.index,
				"videoPath": "%s",
				"metadata": {
					"width": newLayer.width,
					"height": newLayer.height,
					"duration": newLayer.outPoint - newLayer.inPoint,
					"startTime": newLayer.startTime
				}
			};
			return returnjson(result);
		} catch (err) {
			throw new Error(err.toString());
		}
	`, layerID, newResult.LayerID, newResult.VideoPath)

	result, err := ae.ExecuteScript(script)
	if err != nil {
		return ManimResult{}, fmt.Errorf("failed to update layer: %w", err)
	}

	var manimResult ManimResult
	if err := json.Unmarshal([]byte(result.(string)), &manimResult); err != nil {
		return ManimResult{}, fmt.Errorf("failed to parse layer information: %w", err)
	}

	return manimResult, nil
}
