#include "Domains/Animation/McpAutomationBridge_AnimationHandlersActionContext.h"

namespace McpAnimationHandlers {
#if WITH_EDITOR
bool HandleAnimationCreateAnimBlueprintAliasAction(FActionContext &Context,
               const TSharedPtr<FJsonObject> &Payload) {
    return Context.InvokePrivateAnimationHandler(
        TEXT("create_animation_blueprint"), Payload);
}
#endif
} // namespace McpAnimationHandlers
