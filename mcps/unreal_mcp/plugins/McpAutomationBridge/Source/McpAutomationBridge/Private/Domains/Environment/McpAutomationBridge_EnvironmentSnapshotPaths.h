#pragma once

#include "CoreMinimal.h"
#include "Dom/JsonObject.h"

#if WITH_EDITOR
namespace McpEnvironmentHandlers {

bool McpResolveEnvironmentSnapshotPath(
    const TSharedPtr<FJsonObject> &Payload, FString &OutAbsolutePath,
    FString &OutRelativePath, FString &OutError);

}
#endif
