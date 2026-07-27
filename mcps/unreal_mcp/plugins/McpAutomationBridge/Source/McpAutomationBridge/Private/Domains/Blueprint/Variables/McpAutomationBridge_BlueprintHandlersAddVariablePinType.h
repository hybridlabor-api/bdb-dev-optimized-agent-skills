#pragma once

#include "Domains/Blueprint/McpAutomationBridge_BlueprintActionContext.h"
#include "Domains/BlueprintGraph/McpAutomationBridge_BlueprintGraphCompatibility.h"
#include "Foundation/BridgeHelpers/Reflection/McpAutomationBridgeHelpersClassResolution.h"

namespace McpBlueprintHandlers {
#if WITH_EDITOR
inline bool ResolveAddVariablePinType(const FString &VarType,
                                      FEdGraphPinType &PinType,
                                      FString &OutError) {
  const FString LowerType = VarType.ToLower();
  if (LowerType == TEXT("float")) {
    // UE5: PC_Float is a SUBcategory of PC_Real, not a valid pin category.
    // A bare PC_Float category here makes the variable's Get/Set node pins
    // resolve as int downstream (the compiler then injects Truncate /
    // To Float casts — silent precision loss). Same family as the
    // MakePinType fix for function/event parameters.
    PinType.PinCategory = UEdGraphSchema_K2::PC_Real;
    PinType.PinSubCategory = UEdGraphSchema_K2::PC_Float;
  } else if (LowerType == TEXT("double") || LowerType == TEXT("real")) {
    PinType.PinCategory = UEdGraphSchema_K2::PC_Real;
    PinType.PinSubCategory = UEdGraphSchema_K2::PC_Double;
  } else if (LowerType == TEXT("int") || LowerType == TEXT("integer")) {
    PinType.PinCategory = MCP_PC_Int;
  } else if (LowerType == TEXT("bool") || LowerType == TEXT("boolean")) {
    PinType.PinCategory = MCP_PC_Boolean;
  } else if (LowerType == TEXT("string")) {
    PinType.PinCategory = MCP_PC_String;
  } else if (LowerType == TEXT("name")) {
    PinType.PinCategory = MCP_PC_Name;
  } else if (LowerType == TEXT("text")) {
    PinType.PinCategory = MCP_PC_Text;
  } else if (LowerType == TEXT("vector")) {
    PinType.PinCategory = MCP_PC_Struct;
    PinType.PinSubCategoryObject = TBaseStructure<FVector>::Get();
  } else if (LowerType == TEXT("rotator")) {
    PinType.PinCategory = MCP_PC_Struct;
    PinType.PinSubCategoryObject = TBaseStructure<FRotator>::Get();
  } else if (LowerType == TEXT("transform")) {
    PinType.PinCategory = MCP_PC_Struct;
    PinType.PinSubCategoryObject = TBaseStructure<FTransform>::Get();
  } else if (LowerType == TEXT("object")) {
    PinType.PinCategory = MCP_PC_Object;
    PinType.PinSubCategoryObject = UObject::StaticClass();
  } else if (LowerType == TEXT("class")) {
    PinType.PinCategory = MCP_PC_Class;
    PinType.PinSubCategoryObject = UObject::StaticClass();
  } else if (!VarType.TrimStartAndEnd().IsEmpty()) {
    PinType.PinCategory = MCP_PC_Object;
    UClass *FoundClass = ResolveUClass(VarType);
    if (!FoundClass) {
      OutError = FString::Printf(TEXT("Could not resolve class '%s'"), *VarType);
      return false;
    }
    PinType.PinSubCategoryObject = FoundClass;
  } else {
    PinType.PinCategory = MCP_PC_Wildcard;
  }
  return true;
}
#endif
}
