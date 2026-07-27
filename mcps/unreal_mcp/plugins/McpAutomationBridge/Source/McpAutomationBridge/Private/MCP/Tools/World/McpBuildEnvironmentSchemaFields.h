#pragma once

#include "MCP/Registry/McpSchemaBuilder.h"

namespace McpBuildEnvironmentSchema
{
inline void AddVector3(FMcpSchemaBuilder& Builder, const TCHAR* Name, const TCHAR* Description)
{
	Builder.Object(Name, Description, [](FMcpSchemaBuilder& S) { S.Number(TEXT("x")).Number(TEXT("y")).Number(TEXT("z")); });
}

inline void AddRotation(FMcpSchemaBuilder& Builder, const TCHAR* Name, const TCHAR* Description)
{
	Builder.Object(Name, Description, [](FMcpSchemaBuilder& S) { S.Number(TEXT("pitch")).Number(TEXT("yaw")).Number(TEXT("roll")); });
}

inline void AddVector2(FMcpSchemaBuilder& Builder, const TCHAR* Name, const TCHAR* Description)
{
	Builder.Object(Name, Description, [](FMcpSchemaBuilder& S) { S.Number(TEXT("x")).Number(TEXT("y")); });
}

inline void AddBuildEnvironmentFields(FMcpSchemaBuilder& Builder)
{
	Builder
		.String(TEXT("name"), TEXT("Name identifier."))
		.String(TEXT("landscapeName"), TEXT(""))
		.Array(TEXT("heightData"), TEXT(""), TEXT("number"))
		.Number(TEXT("minX"), TEXT("")).Number(TEXT("minY"), TEXT(""))
		.Number(TEXT("maxX"), TEXT("")).Number(TEXT("maxY"), TEXT(""))
		.FreeformObject(TEXT("region"), TEXT("Landscape region bounds."))
		.Bool(TEXT("updateNormals"), TEXT(""))
		.Bool(TEXT("skipFlush"), TEXT("Skip editor flush/update when supported."));
	AddVector3(Builder, TEXT("location"), TEXT("3D location (x, y, z)."));
	AddRotation(Builder, TEXT("rotation"), TEXT("3D rotation (pitch, yaw, roll)."));
	Builder
		.Number(TEXT("sizeX"), TEXT("")).Number(TEXT("sizeY"), TEXT(""))
		.Number(TEXT("sectionSize"), TEXT("")).Number(TEXT("sectionsPerComponent"), TEXT(""));
	AddVector2(Builder, TEXT("componentCount"), TEXT("2D vector."));
	Builder
		.String(TEXT("materialPath"), TEXT("Material asset path."))
		.String(TEXT("tool"), TEXT(""))
		.Number(TEXT("radius"), TEXT("")).Number(TEXT("strength"), TEXT("")).Number(TEXT("falloff"), TEXT(""))
		.String(TEXT("operation"), TEXT("Heightmap or terrain edit operation."))
		.String(TEXT("layerName"), TEXT(""))
		.String(TEXT("actorName"), TEXT("Name of the actor."))
		.String(TEXT("targetActor"), TEXT("Target actor name."))
		.String(TEXT("waterBodyName"), TEXT("Water body actor name."))
		.String(TEXT("foliageType"), TEXT(""))
		.String(TEXT("foliageTypePath"), TEXT("Asset path (e.g., /Game/Path/Asset)."))
		.String(TEXT("meshPath"), TEXT("Mesh asset path."))
		.Number(TEXT("density"), TEXT("")).Number(TEXT("minScale"), TEXT("")).Number(TEXT("maxScale"), TEXT(""))
		.Number(TEXT("cullDistance"), TEXT(""))
		.Bool(TEXT("alignToNormal"), TEXT("")).Bool(TEXT("randomYaw"), TEXT(""))
		.Bool(TEXT("removeAll"), TEXT("Explicitly remove all foliage instances."))
		.ArrayOfObjects(TEXT("locations"), TEXT("")).ArrayOfObjects(TEXT("transforms"), TEXT(""));
	AddVector3(Builder, TEXT("position"), TEXT("3D location (x, y, z)."));
	Builder
		.FreeformObject(TEXT("bounds"), TEXT(""))
		.String(TEXT("volumeName"), TEXT("")).Number(TEXT("seed"), TEXT(""))
		.ArrayOfObjects(TEXT("foliageTypes"), TEXT(""))
		.Number(TEXT("quadsPerSection"), TEXT("")).Number(TEXT("count"), TEXT(""))
		.Array(TEXT("assets"), TEXT(""))
		.Number(TEXT("numLODs"), TEXT("")).Number(TEXT("subdivisions"), TEXT("")).Number(TEXT("tileSize"), TEXT(""))
		.String(TEXT("quality"), TEXT(""))
		.String(TEXT("staticMesh"), TEXT("Mesh asset path."))
		.Number(TEXT("timeoutMs"), TEXT(""))
		.String(TEXT("path"), TEXT("Path to a directory."))
		.String(TEXT("filename"), TEXT(""))
		.String(TEXT("heightmapPath"), TEXT("Filesystem path to a heightmap file."))
		.String(TEXT("outputPath"), TEXT("Filesystem output path."))
		.String(TEXT("landscapePath"), TEXT("Landscape actor/object path."))
		.String(TEXT("landscapeActorPath"), TEXT("Landscape actor object path."))
		.String(TEXT("directionalLightActorPath"), TEXT("Optional directional light actor path for snapshot export."))
		.String(TEXT("skyLightActorPath"), TEXT("Optional skylight actor path for snapshot export."))
		.String(TEXT("layerInfoPath"), TEXT("Landscape layer info asset path."))
		.String(TEXT("physicalMaterialPath"), TEXT("Physical material asset path."))
		.Bool(TEXT("noWeightBlend"), TEXT("Create a non-weight-blended landscape layer info."))
		.Number(TEXT("hardness"), TEXT("Landscape layer hardness."))
		.Array(TEXT("assetPaths"), TEXT("")).Array(TEXT("names"), TEXT(""))
		.Number(TEXT("time"), TEXT("")).Number(TEXT("spacing"), TEXT("")).Number(TEXT("heightScale"), TEXT(""))
		.String(TEXT("material"), TEXT("Material asset path."))
		.String(TEXT("particleSystemPath"), TEXT("Particle system asset path."))
		.String(TEXT("curvePath"), TEXT("Curve asset path or directory."))
		.FreeformObject(TEXT("settings"), TEXT("Properties to apply to created/configured environment objects."))
		.String(TEXT("assetPath"), TEXT("Generic asset path."))
		.String(TEXT("renderTargetPath"), TEXT("Render target asset path."))
		.String(TEXT("lutPath"), TEXT("Color grading LUT asset path."))
		.Number(TEXT("waveHeight"), TEXT("Water wave height."))
		.Number(TEXT("waveLength"), TEXT("Water wave length."))
		.Number(TEXT("amplitude"), TEXT("Wave or effect amplitude."))
		.Number(TEXT("steepness"), TEXT("Water wave steepness, clamped from 0 to 1."))
		.Number(TEXT("speed"), TEXT("Speed value."));
	AddRotation(Builder, TEXT("direction"), TEXT("Direction or rotation value."));
	Builder
		.Number(TEXT("hour"), TEXT("")).Number(TEXT("intensity"), TEXT(""))
		.Number(TEXT("skyLightIntensity"), TEXT("Sky light intensity for time-of-day systems."))
		.Number(TEXT("azimuth"), TEXT("Sun azimuth.")).Number(TEXT("elevation"), TEXT("Sun elevation."))
		.Bool(TEXT("collisionEnabled"), TEXT("Enable collision on configured environment actors."))
		.Number(TEXT("materialIndex"), TEXT("Material slot index."))
		.StringEnum(TEXT("lightType"), {TEXT("Directional"), TEXT("Point"), TEXT("Spot"), TEXT("Rect"), TEXT("DirectionalLight"), TEXT("PointLight"), TEXT("SpotLight"), TEXT("RectLight"), TEXT("directional"), TEXT("point"), TEXT("spot"), TEXT("rect")}, TEXT("Light type."))
		.String(TEXT("lightClass"), TEXT("Unreal light class name."))
		.Array(TEXT("color"), TEXT("RGBA color as an array [r, g, b, a]."), TEXT("number"))
		.Bool(TEXT("castShadows"), TEXT("Whether the light casts shadows."))
		.Bool(TEXT("useAsAtmosphereSunLight"), TEXT("Use a Directional Light as the atmosphere sun light."))
		.Number(TEXT("temperature"), TEXT("Color temperature."))
		.Number(TEXT("falloffExponent"), TEXT("Light falloff exponent."))
		.Number(TEXT("innerCone"), TEXT("Spot light inner cone angle."))
		.Number(TEXT("outerCone"), TEXT("Spot light outer cone angle."))
		.Number(TEXT("width"), TEXT("Width value.")).Number(TEXT("height"), TEXT("Height value."))
		.StringEnum(TEXT("sourceType"), {TEXT("CapturedScene"), TEXT("SpecifiedCubemap")}, TEXT("Sky light source type."))
		.String(TEXT("cubemapPath"), TEXT("Texture asset path."))
		.Bool(TEXT("recapture"), TEXT("Whether to recapture sky lighting."))
		.StringEnum(TEXT("method"), {TEXT("Lightmass"), TEXT("LumenGI"), TEXT("ScreenSpace"), TEXT("None"), TEXT("Filmic"), TEXT("CinematicDOF"), TEXT("Manual")}, TEXT("Lighting, tonemapper, depth-of-field, or exposure method."))
		.Number(TEXT("indirectLightingIntensity"), TEXT("Indirect lighting intensity."))
		.Number(TEXT("bounces"), TEXT("Light bounce count."))
		.String(TEXT("shadowQuality"), TEXT("Shadow quality setting."))
		.Bool(TEXT("cascadedShadows"), TEXT("Whether cascaded shadows are enabled."))
		.Number(TEXT("shadowDistance"), TEXT("Shadow distance."))
		.Bool(TEXT("contactShadows"), TEXT("Whether contact shadows are enabled."))
		.Bool(TEXT("rayTracedShadows"), TEXT("Whether ray-traced shadows are enabled."))
		.Number(TEXT("channel"), TEXT("Light channel index."))
		.Array(TEXT("channels"), TEXT("Light channel indices."), TEXT("number"))
		.Number(TEXT("compensationValue"), TEXT("Exposure compensation value."))
		.Number(TEXT("minBrightness"), TEXT("Minimum brightness."))
		.Number(TEXT("maxBrightness"), TEXT("Maximum brightness."))
		.Bool(TEXT("enabled"), TEXT("Whether the item/feature is enabled."))
		.Number(TEXT("scatteringIntensity"), TEXT("Fog scattering intensity."))
		.Number(TEXT("fogHeight"), TEXT("Fog height."))
		.Bool(TEXT("buildOnlySelected"), TEXT("Build lighting only for selected actors."))
		.Bool(TEXT("buildReflectionCaptures"), TEXT("Build reflection captures."))
		.String(TEXT("levelName"), TEXT("Level name."))
		.Bool(TEXT("copyActors"), TEXT("Copy actors into a created lighting level."))
		.Bool(TEXT("useTemplate"), TEXT("Use a template when creating a level."))
		.String(TEXT("captureSource"), TEXT("Scene capture source."))
		.Number(TEXT("resolution"), TEXT("Capture or reflection resolution."))
		.Number(TEXT("blendWeight"), TEXT("Post-process blend weight."))
		.Bool(TEXT("infiniteUnbound"), TEXT("Whether the post-process volume is unbound."))
		.Number(TEXT("threshold"), TEXT("Post-process threshold value."))
		.Number(TEXT("amount"), TEXT("Post-process amount value."))
		.Number(TEXT("distance"), TEXT("Post-process distance value."))
		.Number(TEXT("aperture"), TEXT("Camera or depth-of-field aperture value."))
		.Number(TEXT("screenPercentage"), TEXT("Screen percentage value."));
	AddVector3(Builder, TEXT("size"), TEXT("3D scale (x, y, z)."));
	Builder
		.String(TEXT("actorPath"), TEXT("Path to actor."))
		.String(TEXT("splineName"), TEXT("Name of spline component."))
		.String(TEXT("componentName"), TEXT("Name of the component."))
		.String(TEXT("blueprintPath"), TEXT("Blueprint asset path."));
	AddVector3(Builder, TEXT("scale"), TEXT("3D scale (x, y, z)."));
	Builder.Number(TEXT("pointIndex"), TEXT("Index of spline point to modify."));
	AddVector3(Builder, TEXT("arriveTangent"), TEXT("Arrive tangent for spline point."));
	AddVector3(Builder, TEXT("leaveTangent"), TEXT("Leave tangent for spline point."));
	AddVector3(Builder, TEXT("tangent"), TEXT("Unified spline tangent."));
	AddRotation(Builder, TEXT("pointRotation"), TEXT("Rotation at spline point."));
	AddVector3(Builder, TEXT("pointScale"), TEXT("Scale at spline point."));
	Builder
		.StringEnum(TEXT("coordinateSpace"), {TEXT("Local"), TEXT("World")}, TEXT("Coordinate space for spline values."))
		.StringEnum(TEXT("splineType"), {TEXT("Linear"), TEXT("Curve"), TEXT("Constant"), TEXT("CurveClamped"), TEXT("CurveCustomTangent")}, TEXT("Type of spline interpolation."))
		.Bool(TEXT("bClosedLoop"), TEXT("Whether spline forms a closed loop."))
		.Bool(TEXT("bUpdateSpline"), TEXT("Update spline after modification."))
		.StringEnum(TEXT("forwardAxis"), {TEXT("X"), TEXT("Y"), TEXT("Z")}, TEXT("Forward axis for spline mesh deformation."));
	AddVector3(Builder, TEXT("startPos"), TEXT("Start position for spline mesh segment."));
	AddVector3(Builder, TEXT("startTangent"), TEXT("Start tangent for spline mesh segment."));
	AddVector3(Builder, TEXT("endPos"), TEXT("End position for spline mesh segment."));
	AddVector3(Builder, TEXT("endTangent"), TEXT("End tangent for spline mesh segment."));
	AddVector2(Builder, TEXT("startScale"), TEXT("X/Y scale at spline mesh start."));
	AddVector2(Builder, TEXT("endScale"), TEXT("X/Y scale at spline mesh end."));
	Builder
		.Number(TEXT("startRoll"), TEXT("Roll angle at spline mesh start."))
		.Number(TEXT("endRoll"), TEXT("Roll angle at spline mesh end."))
		.Bool(TEXT("bSmoothInterpRollScale"), TEXT("Use smooth interpolation for roll/scale."))
		.Number(TEXT("startOffset"), TEXT("Offset from spline start for first mesh."))
		.Number(TEXT("endOffset"), TEXT("Offset from spline end for last mesh."))
		.Bool(TEXT("bAlignToSpline"), TEXT("Align scattered meshes to spline direction."))
		.Bool(TEXT("bRandomizeRotation"), TEXT("Apply random rotation to scattered meshes."));
	AddRotation(Builder, TEXT("rotationRandomRange"), TEXT("Random rotation range (degrees)."));
	AddVector3(Builder, TEXT("captureOffset"), TEXT("Capture offset (x, y, z)."));
	Builder
		.Bool(TEXT("bRandomizeScale"), TEXT("Apply random scale to scattered meshes."))
		.Number(TEXT("scaleMin"), TEXT("Minimum random scale multiplier."))
		.Number(TEXT("scaleMax"), TEXT("Maximum random scale multiplier."))
		.Number(TEXT("randomSeed"), TEXT("Seed for randomization."))
		.StringEnum(TEXT("templateType"), {TEXT("road"), TEXT("river"), TEXT("fence"), TEXT("wall"), TEXT("cable"), TEXT("pipe")}, TEXT("Type of spline template to create."))
		.Number(TEXT("segmentLength"), TEXT("Length of mesh segments for deformation."))
		.Number(TEXT("postSpacing"), TEXT("Spacing between fence posts."))
		.Number(TEXT("railHeight"), TEXT("Height of fence rails."))
		.Number(TEXT("pipeRadius"), TEXT("Radius for pipe template."))
		.Number(TEXT("cableSlack"), TEXT("Slack/sag amount for cable template."))
		.ArrayOfObjects(TEXT("points"), TEXT("Spline points."))
		.String(TEXT("filter"), TEXT("General search filter."))
		.Bool(TEXT("save"), TEXT("Save the asset(s) after the operation."));
}
}
