#pragma once

#include "CoreMinimal.h"
#include "Templates/SharedPointer.h"

class FJsonObject;

namespace McpCustomHandlerAliases
{
struct FActionAliasEntry
{
    FString AliasAction;
    FString TargetAction;
};

constexpr int32 MaxAliasEntriesPerFile = 128;

bool IsValidActionIdentifier(const FString& Action);
bool ReadAliasEntry(
    const TSharedPtr<FJsonObject>& EntryObject,
    FActionAliasEntry& OutEntry,
    FString& OutError);
}
