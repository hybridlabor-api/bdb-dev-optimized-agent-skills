#include "McpAutomationBridgeSubsystem.h"

#include "Core/Subsystem/McpAutomationBridgeSubsystemCustomHandlerAliases.h"

#if WITH_EDITOR && WITH_DEV_AUTOMATION_TESTS
#include "Misc/AutomationTest.h"
#include "UObject/Package.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FMcpCustomHandlerAliasValidationTest,
    "McpAutomationBridge.CustomHandlers.AliasValidation",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMcpCustomHandlerAliasValidationTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    using namespace McpCustomHandlerAliases;

    TestTrue(
        TEXT("Lower snake case action identifiers are accepted"),
        IsValidActionIdentifier(TEXT("project_spawn_enemy_2")));
    TestFalse(
        TEXT("Empty identifiers are rejected"),
        IsValidActionIdentifier(TEXT("")));
    TestFalse(
        TEXT("Uppercase identifiers are rejected"),
        IsValidActionIdentifier(TEXT("ProjectSpawnEnemy")));
    TestFalse(
        TEXT("Hyphenated identifiers are rejected"),
        IsValidActionIdentifier(TEXT("project-spawn-enemy")));
    TestFalse(
        TEXT("Path-like identifiers are rejected"),
        IsValidActionIdentifier(TEXT("../spawn_enemy")));

    TSharedPtr<FJsonObject> SelfTargetingEntry = MakeShared<FJsonObject>();
    SelfTargetingEntry->SetStringField(TEXT("alias"), TEXT("same_action"));
    SelfTargetingEntry->SetStringField(TEXT("target"), TEXT("same_action"));
    FActionAliasEntry Entry;
    FString Error;
    TestFalse(
        TEXT("Self-targeting JSON alias entries are rejected"),
        ReadAliasEntry(SelfTargetingEntry, Entry, Error));

    TSharedPtr<FJsonObject> ValidEntry = MakeShared<FJsonObject>();
    ValidEntry->SetStringField(TEXT("alias"), TEXT("project_spawn_enemy"));
    ValidEntry->SetStringField(TEXT("target"), TEXT("target_action"));
    Error.Empty();
    TestTrue(
        TEXT("Canonical JSON alias entries are accepted"),
        ReadAliasEntry(ValidEntry, Entry, Error));
    return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(
    FMcpCustomHandlerAliasDispatchTest,
    "McpAutomationBridge.CustomHandlers.AliasDispatchesToTargetAction",
    EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMcpCustomHandlerAliasDispatchTest::RunTest(const FString& Parameters)
{
    (void)Parameters;
    UMcpAutomationBridgeSubsystem* Bridge =
        NewObject<UMcpAutomationBridgeSubsystem>(GetTransientPackage());
    if (!TestNotNull(TEXT("Bridge subsystem test object exists"), Bridge))
    {
        return false;
    }

    bool bTargetInvoked = false;
    FString SeenAction;
    FString SeenRequestId;
    TSharedPtr<FJsonObject> SeenPayload;
    ERequestOrigin SeenOrigin = ERequestOrigin::WebSocket;
    TestTrue(
        TEXT("Target handler registers"),
        Bridge->RegisterHandler(
            TEXT("target_action"),
            [Bridge, &bTargetInvoked, &SeenAction, &SeenRequestId, &SeenPayload, &SeenOrigin](
                const FString& RequestId,
                const FString& Action,
                const TSharedPtr<FJsonObject>& Payload,
                TSharedPtr<FMcpBridgeWebSocket> RequestingSocket)
            {
                (void)RequestId;
                (void)Payload;
                (void)RequestingSocket;
                bTargetInvoked = true;
                SeenAction = Action;
                SeenRequestId = RequestId;
                SeenPayload = Payload;
                SeenOrigin = Bridge->CurrentRequestOrigin;
                return true;
            }));
    TestTrue(
        TEXT("Alias registers"),
        Bridge->RegisterActionAlias(TEXT("alias_action"), TEXT("target_action")));
    TestFalse(
        TEXT("Duplicate alias is rejected"),
        Bridge->RegisterActionAlias(TEXT("alias_action"), TEXT("target_action")));
    TestFalse(
        TEXT("Alias cannot target another alias"),
        Bridge->RegisterActionAlias(TEXT("second_alias"), TEXT("alias_action")));
    TestTrue(
        TEXT("Protected target handler registers for policy test"),
        Bridge->RegisterHandler(
            TEXT("inspect"),
            [](
                const FString& RequestId,
                const FString& Action,
                const TSharedPtr<FJsonObject>& Payload,
                TSharedPtr<FMcpBridgeWebSocket> RequestingSocket)
            {
                (void)RequestId;
                (void)Action;
                (void)Payload;
                (void)RequestingSocket;
                return true;
            }));
    TestFalse(
        TEXT("Alias cannot target protected inspect action"),
        Bridge->RegisterActionAlias(TEXT("inspect_alias"), TEXT("inspect")));

    const TSharedPtr<FJsonObject> Payload = MakeShared<FJsonObject>();
    Bridge->QueueAutomationRequest(
        TEXT("request-1"),
        TEXT("alias_action"),
        Payload,
        nullptr,
        ERequestOrigin::NativeHTTP);
    Bridge->ProcessPendingAutomationRequests();
    TestTrue(TEXT("Target handler was invoked"), bTargetInvoked);
    TestEqual(
        TEXT("Target handler receives the target action"),
        SeenAction,
        FString(TEXT("target_action")));
    TestEqual(
        TEXT("Request id is preserved through alias dispatch"),
        SeenRequestId,
        FString(TEXT("request-1")));
    TestTrue(
        TEXT("Payload pointer is preserved through alias dispatch"),
        SeenPayload == Payload);
    TestEqual(
        TEXT("Origin is preserved through queued alias dispatch"),
        static_cast<int32>(SeenOrigin),
        static_cast<int32>(ERequestOrigin::NativeHTTP));

    bool bPendingTargetInvoked = false;
    TestTrue(
        TEXT("Config-style alias can wait for a custom target"),
        Bridge->RegisterActionAliasInternal(
            TEXT("late_alias"),
            TEXT("late_target"),
            true));
    TestFalse(
        TEXT("Pending alias is not active before target registration"),
        Bridge->AutomationHandlers.Contains(TEXT("late_alias")));
    TestTrue(
        TEXT("Pending alias is tracked"),
        Bridge->PendingAutomationActionAliases.Contains(TEXT("late_alias")));
    TestTrue(
        TEXT("Late custom target registration activates pending alias"),
        Bridge->RegisterHandler(
            TEXT("late_target"),
            [&bPendingTargetInvoked](
                const FString& RequestId,
                const FString& Action,
                const TSharedPtr<FJsonObject>& Payload,
                TSharedPtr<FMcpBridgeWebSocket> RequestingSocket)
            {
                (void)RequestId;
                (void)Action;
                (void)Payload;
                (void)RequestingSocket;
                bPendingTargetInvoked = true;
                return true;
            }));
    TestTrue(
        TEXT("Late alias becomes active"),
        Bridge->AutomationHandlers.Contains(TEXT("late_alias")));
    Bridge->QueueAutomationRequest(
        TEXT("request-2"),
        TEXT("late_alias"),
        MakeShared<FJsonObject>(),
        nullptr,
        ERequestOrigin::WebSocket);
    Bridge->ProcessPendingAutomationRequests();
    TestTrue(TEXT("Pending alias dispatch invokes late target"), bPendingTargetInvoked);
    return true;
}
#endif
