package tools

import (
	"errors"
	"fmt"
)

// Common errors
var (
	ErrInvalidResponse = errors.New("invalid response from After Effects")
	ErrNotFound        = errors.New("item not found in After Effects")
	ErrInvalidParams   = errors.New("invalid parameters for After Effects operation")
)

// ErrAEScriptError represents an error that occurred during execution of After Effects script
func ErrAEScriptError(message string) error {
	return fmt.Errorf("After Effects script error: %s", message)
} 