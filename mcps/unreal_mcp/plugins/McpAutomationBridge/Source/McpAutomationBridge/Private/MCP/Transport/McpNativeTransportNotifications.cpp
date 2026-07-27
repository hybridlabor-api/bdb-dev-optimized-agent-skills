#include "MCP/Transport/McpNativeTransportPrivate.h"

namespace
{
bool IsLogAutomationEvent(const TSharedPtr<FJsonObject>& Event)
{
	FString EventName;
	return Event.IsValid() &&
		Event->TryGetStringField(TEXT("event"), EventName) &&
		EventName.Equals(TEXT("log"), ESearchCase::CaseSensitive);
}
}

int32 FMcpNativeTransport::BroadcastNotification(
	const FString& Method, const TSharedPtr<FJsonObject>& Params)
{
	if (Method.IsEmpty())
	{
		return 0;
	}

	const FString NotificationJson = FMcpJsonRpc::BuildNotification(Method, Params);
	TArray<TSharedPtr<FNotificationStream>> StreamSnapshot;
	{
		FScopeLock Lock(&NotificationStreamsMutex);
		StreamSnapshot.Reserve(NotificationStreams.Num());
		for (auto& [StreamId, Stream] : NotificationStreams)
		{
			if (Stream.IsValid() && !Stream->bMarkedForRemoval.load())
			{
				StreamSnapshot.Add(Stream);
			}
		}
	}

	return QueueNotificationEventWrites(StreamSnapshot, NotificationJson);
}

bool FMcpNativeTransport::SetLogEventSubscriptionForRequest(
	const FString& RequestId, const bool bSubscribed)
{
	FString SessionId;
	{
		FScopeLock Lock(&SSEConnectionsMutex);
		const TSharedPtr<FSSEConnection>* Connection = SSEConnections.Find(RequestId);
		if (!Connection || !Connection->IsValid())
		{
			return false;
		}
		SessionId = (*Connection)->SessionId;
	}

	FScopeLock Lock(&LogEventSubscriptionsMutex);
	if (bSubscribed)
	{
		LogEventSubscribedSessions.Add(SessionId);
	}
	else
	{
		LogEventSubscribedSessions.Remove(SessionId);
	}
	return true;
}

bool FMcpNativeTransport::HasLogEventSubscribers() const
{
	FScopeLock Lock(&LogEventSubscriptionsMutex);
	return LogEventSubscribedSessions.Num() > 0;
}

int32 FMcpNativeTransport::BroadcastLogEventNotification(
	const TSharedPtr<FJsonObject>& Params)
{
	if (!IsLogAutomationEvent(Params))
	{
		return 0;
	}

	TSet<FString> SubscribedSessions;
	{
		FScopeLock Lock(&LogEventSubscriptionsMutex);
		SubscribedSessions = LogEventSubscribedSessions;
	}
	if (SubscribedSessions.IsEmpty())
	{
		return 0;
	}

	const FString NotificationJson = FMcpJsonRpc::BuildNotification(
		TEXT("notifications/unreal/automation_event"), Params);
	TArray<TSharedPtr<FNotificationStream>> StreamSnapshot;
	{
		FScopeLock Lock(&NotificationStreamsMutex);
		for (auto& [StreamId, Stream] : NotificationStreams)
		{
			if (Stream.IsValid() &&
				!Stream->bMarkedForRemoval.load() &&
				SubscribedSessions.Contains(Stream->SessionId))
			{
				StreamSnapshot.Add(Stream);
			}
		}
	}

	return QueueNotificationEventWrites(StreamSnapshot, NotificationJson);
}

void FMcpNativeTransport::HandleGetMcp(FSocket* ClientSocket, const FString& SessionId,
	const FString& CorsOrigin)
{
	ISocketSubsystem* SocketSub = ISocketSubsystem::Get(PLATFORM_SOCKETSUBSYSTEM);

	// Check per-session stream limit
	{
		FScopeLock Lock(&NotificationStreamsMutex);
		int32 SessionStreamCount = 0;
		int32 ActiveStreamCount = 0;
		for (const auto& [Id, Stream] : NotificationStreams)
		{
			if (!Stream.IsValid() || Stream->bMarkedForRemoval.load())
			{
				continue;
			}
			++ActiveStreamCount;
			if (Stream->SessionId == SessionId)
			{
				++SessionStreamCount;
			}
		}
		if (ActiveStreamCount >= MaxTotalNotificationStreams)
		{
			Lock.Unlock();
			SendHttpResponse(ClientSocket, 429, TEXT("text/plain"),
				FString::Printf(TEXT("Too Many Requests: max %d notification streams"),
					MaxTotalNotificationStreams), {}, CorsOrigin);
			ClientSocket->Close();
			SocketSub->DestroySocket(ClientSocket);
			return;
		}
		if (SessionStreamCount >= MaxNotificationStreamsPerSession)
		{
			Lock.Unlock();
			SendHttpResponse(ClientSocket, 429, TEXT("text/plain"),
				FString::Printf(TEXT("Too Many Requests: max %d notification streams per session"),
					MaxNotificationStreamsPerSession), {}, CorsOrigin);
			ClientSocket->Close();
			SocketSub->DestroySocket(ClientSocket);
			return;
		}
	}

	// Send SSE headers
	if (!SendSSEHeaders(ClientSocket, SessionId, CorsOrigin))
	{
		ClientSocket->Close();
		SocketSub->DestroySocket(ClientSocket);
		return;
	}

	// Park socket as notification stream
	const double Now = FPlatformTime::Seconds();
	TSharedPtr<FNotificationStream> Stream = MakeShared<FNotificationStream>();
	Stream->Socket = ClientSocket;
	Stream->SessionId = SessionId;
	Stream->StreamId = FGuid::NewGuid().ToString();
	Stream->StartTime = Now;
	Stream->LastKeepaliveTime = Now;

	{
		FScopeLock Lock(&NotificationStreamsMutex);
		NotificationStreams.Add(Stream->StreamId, Stream);
	}
	TouchSession(SessionId);

	UE_LOG(LogMcpNativeTransport, Log,
		TEXT("GET /mcp: notification stream %s opened for session %s"),
		*Stream->StreamId, *SessionId);
	// Socket is parked — do NOT close it. Thread pool slot is released.
}

bool FMcpNativeTransport::WriteNotificationEvent(FNotificationStream& Stream, const FString& EventData)
{
	FString Frame = FString::Printf(TEXT("event: message\ndata: %s\n\n"), *EventData);
	FTCHARToUTF8 Utf8(*Frame);

	FScopeLock Lock(&Stream.WriteMutex);
	if (!Stream.Socket)
	{
		return false;
	}
	return SendAllBytes(Stream.Socket, reinterpret_cast<const uint8*>(Utf8.Get()), Utf8.Length());
}

bool FMcpNativeTransport::WriteNotificationKeepalive(FNotificationStream& Stream)
{
	static const char* KeepaliveFrame = ":keepalive\n\n";
	static const int32 KeepaliveLen = FCStringAnsi::Strlen(KeepaliveFrame);

	FScopeLock Lock(&Stream.WriteMutex);
	if (!Stream.Socket)
	{
		return false;
	}
	return SendAllBytes(Stream.Socket, reinterpret_cast<const uint8*>(KeepaliveFrame), KeepaliveLen);
}

void FMcpNativeTransport::CloseNotificationStream(TSharedPtr<FNotificationStream> Stream)
{
	if (!Stream.IsValid())
	{
		return;
	}
	ISocketSubsystem* SocketSub = ISocketSubsystem::Get(PLATFORM_SOCKETSUBSYSTEM);
	FScopeLock Lock(&Stream->WriteMutex);
	if (Stream->Socket)
	{
		Stream->Socket->Close();
		if (SocketSub)
		{
			SocketSub->DestroySocket(Stream->Socket);
		}
		Stream->Socket = nullptr;
	}
}

// ─── Initialize ─────────────────────────────────────────────────────────────
