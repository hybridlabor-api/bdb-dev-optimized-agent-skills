package tools

import (
	"encoding/json"
	"fmt"
	"github.com/sunqirui1987/ae-mcp/pkg/ae"
	"strings"
)

// EffectDetails represents details of an After Effects effect
type EffectDetails map[string]interface{}

// EffectParameters represents parameters for an After Effects effect
type EffectParameters map[string]interface{}

// EffectInfo represents information about a known After Effects effect
type EffectInfo struct {
	MatchName   string
	DisplayName string
	Category    string
	BPC         string // Bits per channel
	GPU         string // Version when GPU acceleration was introduced (if applicable)
}

// List of known effects organized by category
var KnownEffects = map[string]EffectInfo{
	// 3D Channel
	"ADBE AUX CHANNEL EXTRACT": {MatchName: "ADBE AUX CHANNEL EXTRACT", DisplayName: "3D Channel Extract", Category: "3D Channel", BPC: "8"},
	"ADBE DEPTH MATTE": {MatchName: "ADBE DEPTH MATTE", DisplayName: "Depth Matte", Category: "3D Channel", BPC: "32"},
	"ADBE DEPTH FIELD": {MatchName: "ADBE DEPTH FIELD", DisplayName: "Depth of Field", Category: "3D Channel", BPC: "32"},
	"EXtractoR": {MatchName: "EXtractoR", DisplayName: "EXtractoR", Category: "3D Channel", BPC: "32"},
	"ADBE FOG_3D": {MatchName: "ADBE FOG_3D", DisplayName: "Fog 3D", Category: "3D Channel", BPC: "32"},
	"ADBE ID MATTE": {MatchName: "ADBE ID MATTE", DisplayName: "ID Matte", Category: "3D Channel", BPC: "32"},
	"IDentifier": {MatchName: "IDentifier", DisplayName: "IDentifier", Category: "3D Channel", BPC: "32"},
	
	// Audio
	"ADBE Aud Reverse": {MatchName: "ADBE Aud Reverse", DisplayName: "Backwards", Category: "Audio"},
	"ADBE Aud BT": {MatchName: "ADBE Aud BT", DisplayName: "Bass & Treble", Category: "Audio"},
	"ADBE Aud Delay": {MatchName: "ADBE Aud Delay", DisplayName: "Delay", Category: "Audio"},
	"ADBE Aud_Flange": {MatchName: "ADBE Aud_Flange", DisplayName: "Flange & Chorus", Category: "Audio"},
	"ADBE Aud HiLo": {MatchName: "ADBE Aud HiLo", DisplayName: "High-Low Pass", Category: "Audio"},
	"ADBE Aud Modulator": {MatchName: "ADBE Aud Modulator", DisplayName: "Modulator", Category: "Audio"},
	"ADBE Param EQ": {MatchName: "ADBE Param EQ", DisplayName: "Parametric EQ", Category: "Audio"},
	"ADBE Aud Reverb": {MatchName: "ADBE Aud Reverb", DisplayName: "Reverb", Category: "Audio"},
	"ADBE Aud Stereo Mixer": {MatchName: "ADBE Aud Stereo Mixer", DisplayName: "Stereo Mixer", Category: "Audio"},
	"ADBE Aud Tone": {MatchName: "ADBE Aud Tone", DisplayName: "Tone", Category: "Audio"},
	
	// Blur & Sharpen
	"ADBE Bilateral": {MatchName: "ADBE Bilateral", DisplayName: "Bilateral Blur", Category: "Blur & Sharpen", BPC: "32"},
	"ADBE Camera Lens Blur": {MatchName: "ADBE Camera Lens Blur", DisplayName: "Camera Lens Blur", Category: "Blur & Sharpen", BPC: "32"},
	"ADBE CameraShakeDeblur": {MatchName: "ADBE CameraShakeDeblur", DisplayName: "Camera-Shake Deblur", Category: "Blur & Sharpen", BPC: "32"},
	"CS CrossBlur": {MatchName: "CS CrossBlur", DisplayName: "CC Cross Blur", Category: "Blur & Sharpen", BPC: "32"},
	"CC Radial Blur": {MatchName: "CC Radial Blur", DisplayName: "CC Radial Blur", Category: "Blur & Sharpen", BPC: "32"},
	"CC Radial Fast Blur": {MatchName: "CC Radial Fast Blur", DisplayName: "CC Radial Fast Blur", Category: "Blur & Sharpen", BPC: "16"},
	"CC Vector Blur": {MatchName: "CC Vector Blur", DisplayName: "CC Vector Blur", Category: "Blur & Sharpen", BPC: "16"},
	"ADBE Channel Blur": {MatchName: "ADBE Channel Blur", DisplayName: "Channel Blur", Category: "Blur & Sharpen", BPC: "32"},
	"ADBE Compound Blur": {MatchName: "ADBE Compound Blur", DisplayName: "Compound Blur", Category: "Blur & Sharpen", BPC: "32"},
	"ADBE Motion Blur": {MatchName: "ADBE Motion Blur", DisplayName: "Directional Blur", Category: "Blur & Sharpen", BPC: "32", GPU: "15.0"},
	"ADBE Box Blur2": {MatchName: "ADBE Box Blur2", DisplayName: "Fast Box Blur", Category: "Blur & Sharpen", BPC: "32", GPU: "14.2"},
	"ADBE Gaussian Blur 2": {MatchName: "ADBE Gaussian Blur 2", DisplayName: "Gaussian Blur", Category: "Blur & Sharpen", BPC: "32", GPU: "13.8"},
	"ADBE Radial Blur": {MatchName: "ADBE Radial Blur", DisplayName: "Radial Blur", Category: "Blur & Sharpen", BPC: "32"},
	"ADBE Sharpen": {MatchName: "ADBE Sharpen", DisplayName: "Sharpen", Category: "Blur & Sharpen", BPC: "32", GPU: "13.8"},
	"ADBE Smart Blur": {MatchName: "ADBE Smart Blur", DisplayName: "Smart Blur", Category: "Blur & Sharpen", BPC: "16"},
	"ADBE Unsharp Mask2": {MatchName: "ADBE Unsharp Mask2", DisplayName: "Unsharp Mask", Category: "Blur & Sharpen", BPC: "32"},
	
	// Channel
	"ADBE Invert": {MatchName: "ADBE Invert", DisplayName: "Invert", Category: "Channel", BPC: "32", GPU: "14.1"},
	"ADBE Arithmetic": {MatchName: "ADBE Arithmetic", DisplayName: "Arithmetic", Category: "Channel", BPC: "8"},
	"ADBE Blend": {MatchName: "ADBE Blend", DisplayName: "Blend", Category: "Channel", BPC: "16"},
	"ADBE Calculations": {MatchName: "ADBE Calculations", DisplayName: "Calculations", Category: "Channel", BPC: "16"},
	"CC Composite": {MatchName: "CC Composite", DisplayName: "CC Composite", Category: "Channel", BPC: "16"},
	"ADBE Channel Combiner": {MatchName: "ADBE Channel Combiner", DisplayName: "Channel Combiner", Category: "Channel", BPC: "8"},
	"ADBE Compound Arithmetic": {MatchName: "ADBE Compound Arithmetic", DisplayName: "Compound Arithmetic", Category: "Channel", BPC: "8"},
	"ADBE Minimax": {MatchName: "ADBE Minimax", DisplayName: "Minimax", Category: "Channel", BPC: "16"},
	"ADBE Remove Color Matting": {MatchName: "ADBE Remove Color Matting", DisplayName: "Remove Color Matting", Category: "Channel", BPC: "32"},
	"ADBE Set Channels": {MatchName: "ADBE Set Channels", DisplayName: "Set Channels", Category: "Channel", BPC: "16"},
	"ADBE Set Matte3": {MatchName: "ADBE Set Matte3", DisplayName: "Set Matte", Category: "Channel", BPC: "32"},
	"ADBE Shift Channels": {MatchName: "ADBE Shift Channels", DisplayName: "Shift Channels", Category: "Channel", BPC: "32"},
	"ADBE Solid Composite": {MatchName: "ADBE Solid Composite", DisplayName: "Solid Composite", Category: "Channel", BPC: "32"},
	
	// CINEMA 4D
	"CINEMA 4D Effect": {MatchName: "CINEMA 4D Effect", DisplayName: "CINEWARE", Category: "CINEMA 4D", BPC: "32"},
	
	// Color Correction
	"ADBE Brightness & Contrast 2": {MatchName: "ADBE Brightness & Contrast 2", DisplayName: "Brightness & Contrast", Category: "Color Correction", BPC: "32", GPU: "14.2"},
	"ADBE ColorBalance": {MatchName: "ADBE ColorBalance", DisplayName: "Color Balance (HLS)", Category: "Color Correction", BPC: "16"},
	"ADBE Lumetri": {MatchName: "ADBE Lumetri", DisplayName: "Lumetri Color", Category: "Color Correction", BPC: "32", GPU: "14.2"},
	"ADBE Curves": {MatchName: "ADBE Curves", DisplayName: "Curves", Category: "Color Correction", BPC: "32", GPU: "14.1"},
	"ADBE HUE SATURATION": {MatchName: "ADBE HUE SATURATION", DisplayName: "Hue/Saturation", Category: "Color Correction", BPC: "32", GPU: "14.1"},
	"ADBE Tint": {MatchName: "ADBE Tint", DisplayName: "Tint", Category: "Color Correction", BPC: "32", GPU: "14.1"},
	
	// Distort
	"ADBE LIQUIFY": {MatchName: "ADBE LIQUIFY", DisplayName: "Liquify", Category: "Distort", BPC: "8"},
	"ADBE Ripple": {MatchName: "ADBE Ripple", DisplayName: "Ripple", Category: "Distort", BPC: "32"},
	"ADBE Spherize": {MatchName: "ADBE Spherize", DisplayName: "Spherize", Category: "Distort", BPC: "8"},
	"ADBE TRANSFORM": {MatchName: "ADBE TRANSFORM", DisplayName: "Transform", Category: "Distort", BPC: "32"},
	"ADBE Warp": {MatchName: "ADBE Warp", DisplayName: "Warp", Category: "Distort", BPC: "8"},
	"ADBE Wave Warp": {MatchName: "ADBE Wave Warp", DisplayName: "Wave Warp", Category: "Distort", BPC: "8"},
	
	// Expression Controls
	"ADBE Angle Control": {MatchName: "ADBE Angle Control", DisplayName: "Angle Control", Category: "Expression Controls", BPC: "32"},
	"ADBE Checkbox Control": {MatchName: "ADBE Checkbox Control", DisplayName: "Checkbox Control", Category: "Expression Controls", BPC: "32"},
	"ADBE Color Control": {MatchName: "ADBE Color Control", DisplayName: "Color Control", Category: "Expression Controls", BPC: "32"},
	"ADBE Layer Control": {MatchName: "ADBE Layer Control", DisplayName: "Layer Control", Category: "Expression Controls", BPC: "32"},
	"ADBE Point Control": {MatchName: "ADBE Point Control", DisplayName: "Point Control", Category: "Expression Controls", BPC: "32"},
	"ADBE Slider Control": {MatchName: "ADBE Slider Control", DisplayName: "Slider Control", Category: "Expression Controls", BPC: "32"},
	"ADBE Point3D Control": {MatchName: "ADBE Point3D Control", DisplayName: "3D Point Control", Category: "Expression Controls", BPC: "32"},
	"ADBE Dropdown Control": {MatchName: "ADBE Dropdown Control", DisplayName: "Dropdown Control", Category: "Expression Controls", BPC: "32"},
	
	// Generate
	"ADBE 4ColorGradient": {MatchName: "ADBE 4ColorGradient", DisplayName: "4-Color Gradient", Category: "Generate", BPC: "16"},
	"ADBE Lightning 2": {MatchName: "ADBE Lightning 2", DisplayName: "Advanced Lightning", Category: "Generate", BPC: "8"},
	"ADBE AudSpect": {MatchName: "ADBE AudSpect", DisplayName: "Audio Spectrum", Category: "Generate", BPC: "32"},
	"ADBE AudWave": {MatchName: "ADBE AudWave", DisplayName: "Audio Waveform", Category: "Generate", BPC: "32"},
	"ADBE Laser": {MatchName: "ADBE Laser", DisplayName: "Beam", Category: "Generate", BPC: "32"},
	"CC Glue Gun": {MatchName: "CC Glue Gun", DisplayName: "CC Glue Gun", Category: "Generate", BPC: "32"},
	"CC Light Burst 2.5": {MatchName: "CC Light Burst 2.5", DisplayName: "CC Light Burst 2.5", Category: "Generate", BPC: "32"},
	"CC Light Rays": {MatchName: "CC Light Rays", DisplayName: "CC Light Rays", Category: "Generate", BPC: "32"},
	"CC Light Sweep": {MatchName: "CC Light Sweep", DisplayName: "CC Light Sweep", Category: "Generate", BPC: "32"},
	"CS Threads": {MatchName: "CS Threads", DisplayName: "CC Threads", Category: "Generate", BPC: "32"},
	"ADBE Cell Pattern": {MatchName: "ADBE Cell Pattern", DisplayName: "Cell Pattern", Category: "Generate", BPC: "8"},
	"ADBE Checkerboard": {MatchName: "ADBE Checkerboard", DisplayName: "Checkerboard", Category: "Generate", BPC: "8"},
	"ADBE Circle": {MatchName: "ADBE Circle", DisplayName: "Circle", Category: "Generate", BPC: "8"},
	"ADBE ELLIPSE": {MatchName: "ADBE ELLIPSE", DisplayName: "Ellipse", Category: "Generate", BPC: "32"},
	"ADBE Eyedropper Fill": {MatchName: "ADBE Eyedropper Fill", DisplayName: "Eyedropper Fill", Category: "Generate", BPC: "8"},
	"ADBE Fill": {MatchName: "ADBE Fill", DisplayName: "Fill", Category: "Generate", BPC: "32"},
	"ADBE Fractal": {MatchName: "ADBE Fractal", DisplayName: "Fractal", Category: "Generate", BPC: "16"},
	"ADBE Ramp": {MatchName: "ADBE Ramp", DisplayName: "Gradient Ramp", Category: "Generate", BPC: "32", GPU: "14.2"},
	"ADBE Grid": {MatchName: "ADBE Grid", DisplayName: "Grid", Category: "Generate", BPC: "8"},
	"ADBE Lens Flare": {MatchName: "ADBE Lens Flare", DisplayName: "Lens Flare", Category: "Generate", BPC: "8"},
	"ADBE Paint Bucket": {MatchName: "ADBE Paint Bucket", DisplayName: "Paint Bucket", Category: "Generate", BPC: "8"},
	"APC Radio Waves": {MatchName: "APC Radio Waves", DisplayName: "Radio Waves", Category: "Generate", BPC: "8"},
	"ADBE Scribble Fill": {MatchName: "ADBE Scribble Fill", DisplayName: "Scribble", Category: "Generate", BPC: "8"},
	"ADBE Stroke": {MatchName: "ADBE Stroke", DisplayName: "Stroke", Category: "Generate", BPC: "8"},
	"APC Vegas": {MatchName: "APC Vegas", DisplayName: "Vegas", Category: "Generate", BPC: "8"},
	"ADBE Write-on": {MatchName: "ADBE Write-on", DisplayName: "Write-on", Category: "Generate", BPC: "8"},
	
	// Noise & Grain
	"VISINF Grain Implant": {MatchName: "VISINF Grain Implant", DisplayName: "Add Grain", Category: "Noise & Grain", BPC: "16"},
	"ADBE Dust & Scratches": {MatchName: "ADBE Dust & Scratches", DisplayName: "Dust & Scratches", Category: "Noise & Grain", BPC: "16"},
	"ADBE Fractal Noise": {MatchName: "ADBE Fractal Noise", DisplayName: "Fractal Noise", Category: "Noise & Grain", BPC: "32", GPU: "14.2"},
	"VISINF Grain Duplication": {MatchName: "VISINF Grain Duplication", DisplayName: "Match Grain", Category: "Noise & Grain", BPC: "16"},
	"ADBE Median": {MatchName: "ADBE Median", DisplayName: "Median", Category: "Noise & Grain", BPC: "16"},
	"ADBE Noise": {MatchName: "ADBE Noise", DisplayName: "Noise", Category: "Noise & Grain", BPC: "32"},
	"ADBE Noise Alpha2": {MatchName: "ADBE Noise Alpha2", DisplayName: "Noise Alpha", Category: "Noise & Grain", BPC: "8"},
	"ADBE Noise HLS2": {MatchName: "ADBE Noise HLS2", DisplayName: "Noise HLS", Category: "Noise & Grain", BPC: "8"},
	"ADBE Noise HLS Auto2": {MatchName: "ADBE Noise HLS Auto2", DisplayName: "Noise HLS Auto", Category: "Noise & Grain", BPC: "8"},
	"VISINF Grain Removal": {MatchName: "VISINF Grain Removal", DisplayName: "Remove Grain", Category: "Noise & Grain", BPC: "16"},
	"ADBE AIF Perlin Noise 3D": {MatchName: "ADBE AIF Perlin Noise 3D", DisplayName: "Turbulent Noise", Category: "Noise & Grain", BPC: "32"},
	
	// Stylize
	"ADBE Glo2": {MatchName: "ADBE Glo2", DisplayName: "Glow", Category: "Stylize", BPC: "32", GPU: "14.1"},
	"ADBE Tile": {MatchName: "ADBE Tile", DisplayName: "Motion Tile", Category: "Stylize", BPC: "8"},
	"ADBE Posterize": {MatchName: "ADBE Posterize", DisplayName: "Posterize", Category: "Stylize", BPC: "32"},
	"ADBE Brush Strokes": {MatchName: "ADBE Brush Strokes", DisplayName: "Brush Strokes", Category: "Stylize", BPC: "8"},
	"ADBE Cartoonify": {MatchName: "ADBE Cartoonify", DisplayName: "Cartoon", Category: "Stylize", BPC: "32"},
	"CS BlockLoad": {MatchName: "CS BlockLoad", DisplayName: "CC Block Load", Category: "Stylize", BPC: "32"},
	"CC Burn Film": {MatchName: "CC Burn Film", DisplayName: "CC Burn Film", Category: "Stylize", BPC: "32"},
	"CC Glass": {MatchName: "CC Glass", DisplayName: "CC Glass", Category: "Stylize", BPC: "16"},
	"CS HexTile": {MatchName: "CS HexTile", DisplayName: "CC HexTile", Category: "Stylize", BPC: "32"},
	"CC Kaleida": {MatchName: "CC Kaleida", DisplayName: "CC Kaleida", Category: "Stylize", BPC: "32"},
	"CC Mr. Smoothie": {MatchName: "CC Mr. Smoothie", DisplayName: "CC Mr. Smoothie", Category: "Stylize", BPC: "16"},
	"CC Plastic": {MatchName: "CC Plastic", DisplayName: "CC Plastic", Category: "Stylize", BPC: "16"},
	"CC RepeTile": {MatchName: "CC RepeTile", DisplayName: "CC RepeTile", Category: "Stylize", BPC: "32"},
	"CC Threshold": {MatchName: "CC Threshold", DisplayName: "CC Threshold", Category: "Stylize", BPC: "32"},
	"CC Threshold RGB": {MatchName: "CC Threshold RGB", DisplayName: "CC Threshold RGB", Category: "Stylize", BPC: "32"},
	"CS Vignette": {MatchName: "CS Vignette", DisplayName: "CC Vignette", Category: "Stylize", BPC: "32"},
	"ADBE Color Emboss": {MatchName: "ADBE Color Emboss", DisplayName: "Color Emboss", Category: "Stylize", BPC: "16"},
	"ADBE Emboss": {MatchName: "ADBE Emboss", DisplayName: "Emboss", Category: "Stylize", BPC: "16"},
	"ADBE Find Edges": {MatchName: "ADBE Find Edges", DisplayName: "Find Edges", Category: "Stylize", BPC: "8", GPU: "14.1"},
	"ADBE Mosaic": {MatchName: "ADBE Mosaic", DisplayName: "Mosaic", Category: "Stylize", BPC: "16"},
	"ADBE Roughen Edges": {MatchName: "ADBE Roughen Edges", DisplayName: "Roughen Edges", Category: "Stylize", BPC: "8"},
	"ADBE Scatter": {MatchName: "ADBE Scatter", DisplayName: "Scatter", Category: "Stylize", BPC: "16"},
	"ADBE Strobe": {MatchName: "ADBE Strobe", DisplayName: "Strobe Light", Category: "Stylize", BPC: "8"},
	"ADBE Texturize": {MatchName: "ADBE Texturize", DisplayName: "Texturize", Category: "Stylize", BPC: "8"},
	"ADBE Threshold2": {MatchName: "ADBE Threshold2", DisplayName: "Threshold", Category: "Stylize", BPC: "32"},
	
	// Synthetic Aperture
	"SYNTHAP CF Color Finesse 2": {MatchName: "SYNTHAP CF Color Finesse 2", DisplayName: "SA Color Finesse 3", Category: "Synthetic Aperture", BPC: "32"},
	
	// Text
	"ADBE Numbers2": {MatchName: "ADBE Numbers2", DisplayName: "Numbers", Category: "Text", BPC: "8"},
	"ADBE Timecode": {MatchName: "ADBE Timecode", DisplayName: "Timecode", Category: "Text", BPC: "8"},
	
	// Time
	"CC Force Motion Blur": {MatchName: "CC Force Motion Blur", DisplayName: "CC Force Motion Blur", Category: "Time", BPC: "32"},
	"CC Wide Time": {MatchName: "CC Wide Time", DisplayName: "CC Wide Time", Category: "Time", BPC: "32"},
	"ADBE Echo": {MatchName: "ADBE Echo", DisplayName: "Echo", Category: "Time", BPC: "32"},
	"ADBE OFMotionBlur": {MatchName: "ADBE OFMotionBlur", DisplayName: "Pixel Motion Blur", Category: "Time", BPC: "32"},
	"ADBE Posterize Time": {MatchName: "ADBE Posterize Time", DisplayName: "Posterize Time", Category: "Time", BPC: "32"},
	"ADBE Difference": {MatchName: "ADBE Difference", DisplayName: "Time Difference", Category: "Time", BPC: "8"},
	"ADBE Time Displacement": {MatchName: "ADBE Time Displacement", DisplayName: "Time Displacement", Category: "Time", BPC: "16"},
	"ADBE Timewarp": {MatchName: "ADBE Timewarp", DisplayName: "Timewarp", Category: "Time", BPC: "32"},
	
	// Transition
	"ADBE Block Dissolve": {MatchName: "ADBE Block Dissolve", DisplayName: "Block Dissolve", Category: "Transition", BPC: "16"},
	"APC CardWipeCam": {MatchName: "APC CardWipeCam", DisplayName: "Card Wipe", Category: "Transition", BPC: "8"},
	"CC Glass Wipe": {MatchName: "CC Glass Wipe", DisplayName: "CC Glass Wipe", Category: "Transition", BPC: "16"},
	"CC Grid Wipe": {MatchName: "CC Grid Wipe", DisplayName: "CC Grid Wipe", Category: "Transition", BPC: "32"},
	"CC Image Wipe": {MatchName: "CC Image Wipe", DisplayName: "CC Image Wipe", Category: "Transition", BPC: "16"},
	"CC Jaws": {MatchName: "CC Jaws", DisplayName: "CC Jaws", Category: "Transition", BPC: "32"},
	"CC Light Wipe": {MatchName: "CC Light Wipe", DisplayName: "CC Light Wipe", Category: "Transition", BPC: "16"},
	"CS LineSweep": {MatchName: "CS LineSweep", DisplayName: "CC Line Sweep", Category: "Transition", BPC: "32"},
	"CC Radial ScaleWipe": {MatchName: "CC Radial ScaleWipe", DisplayName: "CC Radial ScaleWipe", Category: "Transition", BPC: "16"},
	"CC Scale Wipe": {MatchName: "CC Scale Wipe", DisplayName: "CC Scale Wipe", Category: "Transition", BPC: "32"},
	"CC Twister": {MatchName: "CC Twister", DisplayName: "CC Twister", Category: "Transition", BPC: "16"},
	"CC WarpoMatic": {MatchName: "CC WarpoMatic", DisplayName: "CC WarpoMatic", Category: "Transition", BPC: "16"},
	"ADBE Gradient Wipe": {MatchName: "ADBE Gradient Wipe", DisplayName: "Gradient Wipe", Category: "Transition", BPC: "16"},
	"ADBE IRIS_WIPE": {MatchName: "ADBE IRIS_WIPE", DisplayName: "Iris Wipe", Category: "Transition", BPC: "32"},
	"ADBE Linear Wipe": {MatchName: "ADBE Linear Wipe", DisplayName: "Linear Wipe", Category: "Transition", BPC: "32"},
	"ADBE Radial Wipe": {MatchName: "ADBE Radial Wipe", DisplayName: "Radial Wipe", Category: "Transition", BPC: "32"},
	"ADBE Venetian Blinds": {MatchName: "ADBE Venetian Blinds", DisplayName: "Venetian Blinds", Category: "Transition", BPC: "32"},
	
	// Utility
	"ADBE Apply Color LUT2": {MatchName: "ADBE Apply Color LUT2", DisplayName: "Apply Color LUT", Category: "Utility", BPC: "32"},
	"CC Overbrights": {MatchName: "CC Overbrights", DisplayName: "CC Overbrights", Category: "Utility", BPC: "32"},
	"ADBE Cineon Converter2": {MatchName: "ADBE Cineon Converter2", DisplayName: "Cineon Converter", Category: "Utility", BPC: "32"},
	"ADBE ProfileToProfile": {MatchName: "ADBE ProfileToProfile", DisplayName: "Color Profile Converter", Category: "Utility", BPC: "32"},
	"ADBE GROW BOUNDS": {MatchName: "ADBE GROW BOUNDS", DisplayName: "Grow Bounds", Category: "Utility", BPC: "32"},
	"ADBE Compander": {MatchName: "ADBE Compander", DisplayName: "HDR Compander", Category: "Utility", BPC: "32"},
	"ADBE HDR ToneMap": {MatchName: "ADBE HDR ToneMap", DisplayName: "HDR Highlight Compression", Category: "Utility", BPC: "32"},
}

// lookupEffectMatchName tries to find the match name for an effect given a display name or match name
func lookupEffectMatchName(nameOrMatchName string) string {
	// If it's already a match name, return it
	for _, effect := range KnownEffects {
		if effect.MatchName == nameOrMatchName {
			return nameOrMatchName
		}
	}
	
	// Look up by display name (case-insensitive)
	lowerName := strings.ToLower(nameOrMatchName)
	for _, effect := range KnownEffects {
		if strings.ToLower(effect.DisplayName) == lowerName {
			return effect.MatchName
		}
	}
	
	// If not found in our known effects, return the input as is
	// (it might be a third-party effect or one we don't have listed)
	return nameOrMatchName
}

// ApplyEffect applies an effect to a layer in a composition
func ApplyEffect(compName string, layerName string, effectName string, parameters EffectParameters) (EffectDetails, error) {
	// Convert effect name to match name if possible
	effectMatchName := lookupEffectMatchName(effectName)
	
	// Build the script to apply the effect
	script := `
	try {
		var compName = "` + compName + `";
		var layerName = "` + layerName + `";
		var effectName = "` + effectName + `";
		var effectMatchName = "` + effectMatchName + `";
		
		// Find the composition
		var comp = null;
		for (var i = 1; i <= app.project.numItems; i++) {
			var item = app.project.item(i);
			if (item instanceof CompItem && item.name === compName) {
				comp = item;
				break;
			}
		}
		
		if (!comp) {
			return JSON.stringify({
				error: "Composition not found: " + compName
			});
		}
		
		// Find the layer
		var layer = null;
		for (var i = 1; i <= comp.numLayers; i++) {
			var l = comp.layer(i);
			if (l.name === layerName) {
				layer = l;
				break;
			}
		}
		
		if (!layer) {
			return JSON.stringify({
				error: "Layer not found: " + layerName
			});
		}
		
		// Try to apply the effect using match name first, then display name
		var effect;
		try {
			// Try to apply by match name
			effect = layer.Effects.addProperty(effectMatchName);
		} catch (matchNameErr) {
			try {
				// If match name fails, try with the display name
				effect = layer.Effects.addProperty(effectName);
			} catch (displayNameErr) {
				return JSON.stringify({
					error: "Failed to apply effect: " + effectName + ". Error: " + displayNameErr.toString()
				});
			}
		}
		
		if (!effect) {
			return JSON.stringify({
				error: "Failed to apply effect: " + effectName
			});
		}
	`

	// If parameters were provided, adjust them
	if parameters != nil {
		for key, value := range parameters {
			// Different handling based on parameter type
			switch v := value.(type) {
			case float64:
				script += `
				try {
					if (effect.property("` + key + `")) {
						effect.property("` + key + `").setValue(` + fmt.Sprintf("%f", v) + `);
					}
				} catch (paramErr) {
					// Skip this parameter if it doesn't exist or can't be set
				}
				`
			case bool:
				boolVal := 0
				if v {
					boolVal = 1
				}
				script += `
				try {
					if (effect.property("` + key + `")) {
						effect.property("` + key + `").setValue(` + fmt.Sprintf("%d", boolVal) + `);
					}
				} catch (paramErr) {
					// Skip this parameter if it doesn't exist or can't be set
				}
				`
			case string:
				script += `
				try {
					if (effect.property("` + key + `")) {
						effect.property("` + key + `").setValue("` + escapeJSStringEffect(v) + `");
					}
				} catch (paramErr) {
					// Skip this parameter if it doesn't exist or can't be set
				}
				`
			case []interface{}:
				// Handle arrays (e.g., for color or point values)
				if len(v) > 0 {
					arrayStr := "["
					for i, item := range v {
						if i > 0 {
							arrayStr += ", "
						}
						switch itemVal := item.(type) {
						case float64:
							arrayStr += fmt.Sprintf("%f", itemVal)
						case int:
							arrayStr += fmt.Sprintf("%d", itemVal)
						case string:
							arrayStr += `"` + escapeJSStringEffect(itemVal) + `"`
						default:
							arrayStr += "0"
						}
					}
					arrayStr += "]"
					
					script += `
					try {
						if (effect.property("` + key + `")) {
							effect.property("` + key + `").setValue(` + arrayStr + `);
						}
					} catch (paramErr) {
						// Skip this parameter if it doesn't exist or can't be set
					}
					`
				}
			}
		}
	}

	// Complete the script
	script += `
		// Get information about the applied effect
		var effectInfo = {
			name: effect.name,
			displayName: effect.displayName || effect.name,
			matchName: effect.matchName,
			parameters: []
		};
		
		// Gather parameter information
		for (var i = 1; i <= effect.numProperties; i++) {
			var prop = effect.property(i);
			// Only include properties that we can potentially modify
			if (prop.canSetValue) {
				var paramInfo = {
					name: prop.name,
					matchName: prop.matchName,
					value: prop.value
				};
				effectInfo.parameters.push(paramInfo);
			}
		}
		
		return returnjson(effectInfo);
	} catch (err) {
		return "ERROR: " + err.toString();
	}
	`

	// Execute the script
	result, err := ae.ExecuteScript(script)
	if err != nil {
		return nil, err
	}

	// Extract result
	if resultStr, ok := result.(string); ok {
		// Check if the result indicates an error
		if len(resultStr) > 7 && resultStr[:7] == "ERROR: " {
			return nil, ErrAEScriptError(resultStr[7:])
		}
		
		// Parse the JSON result into a structured object
		var effectDetails EffectDetails
		if err := json.Unmarshal([]byte(resultStr), &effectDetails); err != nil {
			return nil, err
		}
		
		// Check for error in result
		if errMsg, hasErr := effectDetails["error"].(string); hasErr {
			return nil, fmt.Errorf("%s", errMsg)
		}
		
		return effectDetails, nil
	}

	return nil, ErrInvalidResponse
}

// GetEffectCategories returns a list of effect categories
func GetEffectCategories() []string {
	categories := make(map[string]bool)
	for _, effect := range KnownEffects {
		categories[effect.Category] = true
	}
	
	result := make([]string, 0, len(categories))
	for category := range categories {
		result = append(result, category)
	}
	return result
}

// GetEffectsByCategory returns effects in a specified category
func GetEffectsByCategory(category string) []EffectInfo {
	var effects []EffectInfo
	for _, effect := range KnownEffects {
		if effect.Category == category {
			effects = append(effects, effect)
		}
	}
	return effects
}

// Helper function to escape special characters in JS strings
func escapeJSStringEffect(s string) string {
	s = strings.ReplaceAll(s, "\\", "\\\\")
	s = strings.ReplaceAll(s, "\"", "\\\"")
	s = strings.ReplaceAll(s, "\n", "\\n")
	s = strings.ReplaceAll(s, "\r", "\\r")
	s = strings.ReplaceAll(s, "\t", "\\t")
	return s
}

// MCP Functions

// MCPApplyEffect applies an effect to a layer via MCP
func MCPApplyEffect(args map[string]interface{}) (interface{}, error) {
	// Validate required parameters
	compName, ok := args["composition_name"].(string)
	if !ok || compName == "" {
		return nil, fmt.Errorf("composition_name is required")
	}
	
	layerName, ok := args["layer_name"].(string)
	if !ok || layerName == "" {
		return nil, fmt.Errorf("layer_name is required")
	}
	
	effectName, ok := args["effect_name"].(string)
	if !ok || effectName == "" {
		return nil, fmt.Errorf("effect_name is required")
	}
	
	// Get optional parameters
	var parameters EffectParameters
	if params, hasParams := args["parameters"].(map[string]interface{}); hasParams {
		parameters = params
	}
	
	// Apply the effect
	return ApplyEffect(compName, layerName, effectName, parameters)
}

// MCPGetEffectCategories returns all effect categories via MCP
func MCPGetEffectCategories(args map[string]interface{}) (interface{}, error) {
	categories := GetEffectCategories()
	return map[string]interface{}{
		"categories": categories,
	}, nil
}

// MCPGetEffectsByCategory returns effects in a category via MCP
func MCPGetEffectsByCategory(args map[string]interface{}) (interface{}, error) {
	category, ok := args["category"].(string)
	if !ok || category == "" {
		return nil, fmt.Errorf("category parameter is required")
	}
	
	effectList := GetEffectsByCategory(category)
	
	// Convert to format suitable for MCP response
	results := make([]map[string]interface{}, len(effectList))
	for i, effect := range effectList {
		results[i] = map[string]interface{}{
			"displayName": effect.DisplayName,
			"matchName":   effect.MatchName,
			"bpc":         effect.BPC,
			"gpu":         effect.GPU,
		}
	}
	
	return map[string]interface{}{
		"category": category,
		"effects":  results,
	}, nil
}
