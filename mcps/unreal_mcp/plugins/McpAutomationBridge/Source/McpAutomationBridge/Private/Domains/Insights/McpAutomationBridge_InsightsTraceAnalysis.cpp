#include "Core/Compatibility/McpVersionCompatibility.h"

#include "Domains/Insights/McpAutomationBridge_InsightsRequests.h"

#include "Dom/JsonObject.h"
#include "HAL/FileManager.h"
#include "McpAutomationBridgeSubsystem.h"
#include "Misc/Paths.h"
#include "Serialization/Archive.h"

namespace McpInsights
{
namespace
{
FString ToHex(const TArray<uint8>& Bytes)
{
    FString Hex;
    Hex.Reserve(Bytes.Num() * 2);
    for (uint8 Byte : Bytes)
    {
        Hex += FString::Printf(TEXT("%02X"), Byte);
    }
    return Hex;
}

void AddHeaderProbe(const FString& Path, int64 Size, TSharedPtr<FJsonObject>& Result)
{
    const int64 ReadSize = FMath::Min<int64>(Size, 32);
    TArray<uint8> Header;
    Header.SetNumZeroed(static_cast<int32>(ReadSize));
    TUniquePtr<FArchive> Reader(IFileManager::Get().CreateFileReader(*Path));
    const bool bCanRead = Reader.IsValid() && ReadSize > 0;
    if (bCanRead)
    {
        Reader->Serialize(Header.GetData(), Header.Num());
    }
    Result->SetBoolField(TEXT("headerRead"), bCanRead && !Reader->IsError());
    Result->SetNumberField(TEXT("headerBytesRead"), Header.Num());
    Result->SetStringField(TEXT("headerPreviewHex"), ToHex(Header));
}
}

bool HandleAnalyzeTrace(
    UMcpAutomationBridgeSubsystem* Bridge,
    const FString& RequestId,
    const TSharedPtr<FJsonObject>& Payload,
    TSharedPtr<FMcpBridgeWebSocket> RequestingSocket)
{
    FString Path;
    FString Error;
    FString ErrorCode;
    if (!TryResolveTracePath(Payload, true, false, false, Path, Error, ErrorCode))
    {
        TSharedPtr<FJsonObject> Result =
            CreateInsightsResult(TEXT("analyze_trace"), TEXT("analyze_trace"));
        Result->SetBoolField(TEXT("exists"), false);
        Result->SetStringField(TEXT("path"), Path);
        Result->SetStringField(TEXT("analysisScope"),
            TEXT("local_file_metadata_and_header_probe"));
        Bridge->SendAutomationResponse(RequestingSocket, RequestId, false,
            Error, Result, ErrorCode);
        return true;
    }

    const FFileStatData Stat = IFileManager::Get().GetStatData(*Path);
    TSharedPtr<FJsonObject> Result =
        CreateInsightsResult(TEXT("analyze_trace"), TEXT("analyze_trace"));
    Result->SetStringField(TEXT("status"), TEXT("analyzed"));
    Result->SetStringField(TEXT("analysisScope"),
        TEXT("local_file_metadata_and_header_probe"));
    Result->SetStringField(TEXT("path"), Path);
    Result->SetStringField(TEXT("extension"), FPaths::GetExtension(Path));
    Result->SetBoolField(TEXT("exists"), Stat.bIsValid);
    Result->SetBoolField(TEXT("isDirectory"), Stat.bIsDirectory);
    Result->SetBoolField(TEXT("hasUtraceExtension"),
        FPaths::GetExtension(Path).Equals(TEXT("utrace"), ESearchCase::IgnoreCase));
    Result->SetNumberField(TEXT("sizeBytes"), static_cast<double>(Stat.FileSize));
    Result->SetStringField(TEXT("modifiedUtc"),
        Stat.ModificationTime.ToString(TEXT("%Y-%m-%dT%H:%M:%SZ")));
    AddHeaderProbe(Path, Stat.FileSize, Result);

    Bridge->SendAutomationResponse(RequestingSocket, RequestId, true,
        TEXT("Trace file metadata analyzed."), Result);
    return true;
}
}
