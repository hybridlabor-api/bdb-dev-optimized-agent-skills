#include "McpAutomationBridgeSubsystem.h"

#include "Core/Subsystem/McpAutomationBridgeSubsystemCustomHandlerAliases.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "HAL/FileManager.h"
#include "Interfaces/IPluginManager.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"

namespace
{
const TCHAR* HandlerAliasConfigFileName()
{
    return TEXT("handler-aliases.json");
}

constexpr int64 MaxAliasConfigBytes = 64 * 1024;

void AddIfNotEmpty(TArray<FString>& Paths, const FString& Path)
{
    if (!Path.IsEmpty())
    {
        Paths.Add(Path);
    }
}

TArray<FString> GetConfiguredAliasPaths()
{
    TArray<FString> Paths;
    AddIfNotEmpty(
        Paths,
        FPaths::Combine(
            FPaths::ProjectSavedDir(),
            TEXT("Config"),
            TEXT("McpAutomationBridge"),
            HandlerAliasConfigFileName()));
    AddIfNotEmpty(
        Paths,
        FPaths::Combine(
            FPaths::ProjectConfigDir(),
            TEXT("McpAutomationBridge"),
            HandlerAliasConfigFileName()));

    const TSharedPtr<IPlugin> Plugin =
        IPluginManager::Get().FindPlugin(TEXT("McpAutomationBridge"));
    if (Plugin.IsValid())
    {
        AddIfNotEmpty(
            Paths,
            FPaths::Combine(
                Plugin->GetBaseDir(),
                TEXT("Resources"),
                TEXT("MCP"),
                HandlerAliasConfigFileName()));
    }
    return Paths;
}

bool LoadAliasConfigRoot(const FString& ConfigPath, TSharedPtr<FJsonObject>& OutRoot)
{
    const int64 FileSize = IFileManager::Get().FileSize(*ConfigPath);
    if (FileSize < 0 || FileSize > MaxAliasConfigBytes)
    {
        UE_LOG(LogMcpAutomationBridgeSubsystem, Warning,
            TEXT("Skipping MCP handler alias config with unsupported size %lld: %s"),
            FileSize,
            *ConfigPath);
        return false;
    }

    FString RawJson;
    if (!FFileHelper::LoadFileToString(RawJson, *ConfigPath))
    {
        UE_LOG(LogMcpAutomationBridgeSubsystem, Warning,
            TEXT("Could not read MCP handler alias config: %s"), *ConfigPath);
        return false;
    }

    const TSharedRef<TJsonReader<>> Reader =
        TJsonReaderFactory<>::Create(RawJson);
    if (!FJsonSerializer::Deserialize(Reader, OutRoot) || !OutRoot.IsValid())
    {
        UE_LOG(LogMcpAutomationBridgeSubsystem, Warning,
            TEXT("Could not parse MCP handler alias config: %s"), *ConfigPath);
        return false;
    }
    double Version = 0.0;
    if (!OutRoot->TryGetNumberField(TEXT("version"), Version) ||
        !FMath::IsNearlyEqual(Version, 1.0))
    {
        UE_LOG(LogMcpAutomationBridgeSubsystem, Warning,
            TEXT("MCP handler alias config has unsupported or missing version: %s"),
            *ConfigPath);
        return false;
    }
    return true;
}

const TArray<TSharedPtr<FJsonValue>>* ReadAliasArray(
    const TSharedPtr<FJsonObject>& Root,
    const FString& ConfigPath)
{
    const TArray<TSharedPtr<FJsonValue>>* Aliases = nullptr;
    if (Root->TryGetArrayField(TEXT("aliases"), Aliases))
    {
        return Aliases;
    }

    UE_LOG(LogMcpAutomationBridgeSubsystem, Warning,
        TEXT("MCP handler alias config has no aliases array: %s"), *ConfigPath);
    return nullptr;
}

TArray<McpCustomHandlerAliases::FActionAliasEntry> ParseAliasEntries(
    const TArray<TSharedPtr<FJsonValue>>& AliasValues,
    const FString& ConfigPath)
{
    TArray<McpCustomHandlerAliases::FActionAliasEntry> Entries;
    TSet<FString> DeclaredAliases;
    const int32 Limit =
        FMath::Min(AliasValues.Num(), McpCustomHandlerAliases::MaxAliasEntriesPerFile);
    if (AliasValues.Num() > McpCustomHandlerAliases::MaxAliasEntriesPerFile)
    {
        UE_LOG(LogMcpAutomationBridgeSubsystem, Warning,
            TEXT("MCP handler alias config has %d aliases; only the first %d are read: %s"),
            AliasValues.Num(),
            McpCustomHandlerAliases::MaxAliasEntriesPerFile,
            *ConfigPath);
    }

    for (int32 Index = 0; Index < Limit; ++Index)
    {
        McpCustomHandlerAliases::FActionAliasEntry Entry;
        FString Error;
        const TSharedPtr<FJsonValue>& AliasValue = AliasValues[Index];
        const TSharedPtr<FJsonObject> EntryObject =
            AliasValue.IsValid() ? AliasValue->AsObject() : nullptr;
        if (!McpCustomHandlerAliases::ReadAliasEntry(EntryObject, Entry, Error))
        {
            UE_LOG(LogMcpAutomationBridgeSubsystem, Warning,
                TEXT("Skipping MCP handler alias in %s: %s"), *ConfigPath, *Error);
            continue;
        }
        if (DeclaredAliases.Contains(Entry.AliasAction))
        {
            UE_LOG(LogMcpAutomationBridgeSubsystem, Warning,
                TEXT("Skipping duplicate MCP handler alias '%s' in %s"),
                *Entry.AliasAction,
                *ConfigPath);
            continue;
        }

        DeclaredAliases.Add(Entry.AliasAction);
        Entries.Add(MoveTemp(Entry));
    }

    for (int32 Index = Entries.Num() - 1; Index >= 0; --Index)
    {
        if (DeclaredAliases.Contains(Entries[Index].TargetAction))
        {
            UE_LOG(LogMcpAutomationBridgeSubsystem, Warning,
                TEXT("Skipping MCP handler alias '%s' because target '%s' is another alias in %s"),
                *Entries[Index].AliasAction,
                *Entries[Index].TargetAction,
                *ConfigPath);
            Entries.RemoveAt(Index);
        }
    }
    return Entries;
}
}

void UMcpAutomationBridgeSubsystem::LoadConfiguredHandlerAliases()
{
    for (const FString& ConfigPath : GetConfiguredAliasPaths())
    {
        if (!IFileManager::Get().FileExists(*ConfigPath))
        {
            continue;
        }

        TSharedPtr<FJsonObject> Root;
        if (!LoadAliasConfigRoot(ConfigPath, Root))
        {
            continue;
        }

        const TArray<TSharedPtr<FJsonValue>>* AliasValues =
            ReadAliasArray(Root, ConfigPath);
        if (!AliasValues)
        {
            continue;
        }

        int32 RegisteredCount = 0;
        for (const McpCustomHandlerAliases::FActionAliasEntry& Entry :
             ParseAliasEntries(*AliasValues, ConfigPath))
        {
            if (RegisterActionAliasInternal(
                    Entry.AliasAction,
                    Entry.TargetAction,
                    true))
            {
                ++RegisteredCount;
            }
        }

        UE_LOG(LogMcpAutomationBridgeSubsystem, Log,
            TEXT("Loaded %d MCP handler aliases from %s"),
            RegisteredCount,
            *ConfigPath);
    }
}
