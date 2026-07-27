#pragma once

#include "CoreMinimal.h"
#include "Templates/SharedPointer.h"

class FJsonObject;
class FMcpBridgeWebSocket;
class UMcpAutomationBridgeSubsystem;

namespace McpInsights
{
enum class ETraceStartMode : uint8
{
    File,
    Network
};

struct FTraceStartRequest
{
    ETraceStartMode Mode = ETraceStartMode::File;
    FString Channels;
    FString OutputPath;
    FString Host = TEXT("localhost");
    int32 Port = 0;
    bool bOverwrite = false;
    bool bExcludeTail = false;
    uint32 MaxTailSize = 0;
};

bool IsInsightsAction(const FString& Action);
FString NormalizeSubAction(
    const FString& Action,
    const TSharedPtr<FJsonObject>& Payload);
TSharedPtr<FJsonObject> CreateInsightsResult(
    const FString& SubAction,
    const FString& TraceAction);
void AddTraceStatus(TSharedPtr<FJsonObject>& Result);
FString StartModeToString(ETraceStartMode Mode);
bool TryBuildStartRequest(
    const TSharedPtr<FJsonObject>& Payload,
    bool bForceFileMode,
    FTraceStartRequest& OutRequest,
    FString& OutError,
    FString& OutErrorCode);
bool TryReadChannels(
    const TSharedPtr<FJsonObject>& Payload,
    FString& OutChannels,
    FString& OutError);
bool TryResolveTracePath(
    const TSharedPtr<FJsonObject>& Payload,
    bool bRequireExistingFile,
    bool bAppendTraceExtension,
    bool bAllowGeneratedDefault,
    FString& OutPath,
    FString& OutError,
    FString& OutErrorCode);
bool TryReadHostAndPort(
    const TSharedPtr<FJsonObject>& Payload,
    bool bRequireHost,
    FString& OutHost,
    int32& OutPort,
    FString& OutError,
    FString& OutErrorCode);
uint32 ReadMaxTailSize(const TSharedPtr<FJsonObject>& Payload);
bool ReadOverwrite(const TSharedPtr<FJsonObject>& Payload);

bool HandleStartSession(
    UMcpAutomationBridgeSubsystem* Bridge,
    const FString& RequestId,
    const FString& Action,
    const TSharedPtr<FJsonObject>& Payload,
    TSharedPtr<FMcpBridgeWebSocket> RequestingSocket);
bool HandleStopSession(
    UMcpAutomationBridgeSubsystem* Bridge,
    const FString& RequestId,
    const TSharedPtr<FJsonObject>& Payload,
    TSharedPtr<FMcpBridgeWebSocket> RequestingSocket);
bool HandlePauseSession(
    UMcpAutomationBridgeSubsystem* Bridge,
    const FString& RequestId,
    const TSharedPtr<FJsonObject>& Payload,
    TSharedPtr<FMcpBridgeWebSocket> RequestingSocket);
bool HandleResumeSession(
    UMcpAutomationBridgeSubsystem* Bridge,
    const FString& RequestId,
    const TSharedPtr<FJsonObject>& Payload,
    TSharedPtr<FMcpBridgeWebSocket> RequestingSocket);
bool HandleGetTraceStatus(
    UMcpAutomationBridgeSubsystem* Bridge,
    const FString& RequestId,
    const TSharedPtr<FJsonObject>& Payload,
    TSharedPtr<FMcpBridgeWebSocket> RequestingSocket);
bool HandleWriteSnapshot(
    UMcpAutomationBridgeSubsystem* Bridge,
    const FString& RequestId,
    const TSharedPtr<FJsonObject>& Payload,
    TSharedPtr<FMcpBridgeWebSocket> RequestingSocket);
bool HandleSendSnapshot(
    UMcpAutomationBridgeSubsystem* Bridge,
    const FString& RequestId,
    const TSharedPtr<FJsonObject>& Payload,
    TSharedPtr<FMcpBridgeWebSocket> RequestingSocket);
bool HandleAnalyzeTrace(
    UMcpAutomationBridgeSubsystem* Bridge,
    const FString& RequestId,
    const TSharedPtr<FJsonObject>& Payload,
    TSharedPtr<FMcpBridgeWebSocket> RequestingSocket);
}
