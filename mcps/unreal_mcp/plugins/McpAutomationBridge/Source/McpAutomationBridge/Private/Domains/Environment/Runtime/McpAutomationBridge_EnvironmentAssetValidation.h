#pragma once

#include "CoreMinimal.h"

namespace McpEnvironmentHandlers {
#if WITH_EDITOR
bool McpFailEnvironmentAction(FString &OutMessage, FString &OutErrorCode,
                              const FString &Message, const TCHAR *ErrorCode);
bool McpBuildValidatedEnvironmentAssetPath(const FString &RequestedPath, const FString &AssetName,
                                           const TCHAR *AssetLabel, FString &OutPackagePath,
                                           FString &OutMessage, FString &OutErrorCode);
#endif
}
