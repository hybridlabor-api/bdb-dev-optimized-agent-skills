#include "Core/Compatibility/McpVersionCompatibility.h"
#include "MCP/Registry/McpToolDefinition.h"
#include "MCP/Registry/McpToolRegistry.h"
#include "MCP/Registry/McpSchemaBuilder.h"
#include "MCP/Routing/McpConsolidatedActionRouting.h"
#include "MCP/Tools/World/McpBuildEnvironmentSchemaFields.h"

class FMcpTool_BuildEnvironment : public FMcpToolDefinition
{
public:
	FString GetName() const override { return TEXT("build_environment"); }

	FString GetDescription() const override
	{
		return TEXT("Create/sculpt landscapes, paint foliage, and generate procedural "
			"terrain/biomes.");
	}

	FString GetCategory() const override { return TEXT("world"); }

	// Pattern A: default GetDispatchAction() returns GetName()

	TSharedPtr<FJsonObject> BuildInputSchema() const override
	{
		FMcpSchemaBuilder Builder;
		Builder.StringEnum(TEXT("action"), McpConsolidatedActions::BuildEnvironment(),
			TEXT("Action"));
		McpBuildEnvironmentSchema::AddBuildEnvironmentFields(Builder);
		return Builder.Required({TEXT("action")}).Build();
	}
};

MCP_REGISTER_TOOL(FMcpTool_BuildEnvironment);
