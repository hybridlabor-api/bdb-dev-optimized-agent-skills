#pragma once

#include "EditorBuildUtils.h"
#include "LightingBuildOptions.h" // UE5.8: ELightingBuildQuality no longer pulled transitively via EditorBuildUtils.h

class UWorld;

namespace McpLightingHandlers
{
#if WITH_EDITOR
bool RunLegacyLightingBuild(
    UWorld& World,
    ELightingBuildQuality Quality);
#endif
}
