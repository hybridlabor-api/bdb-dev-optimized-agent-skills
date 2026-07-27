/**
 * Blueprint handler argument types.
 */
import type { HandlerArgs } from './handler-common-types.js';

// ============================================================================
// Blueprint Types
// ============================================================================

export interface BlueprintArgs extends HandlerArgs {
    blueprintPath?: string;
    name?: string;
    savePath?: string;
    blueprintType?: string;
    componentType?: string;
    componentName?: string;
    attachTo?: string;
    variableName?: string;
    eventType?: string;
    customEventName?: string;
    nodeType?: string;
    graphName?: string;
    x?: number;
    y?: number;
    memberName?: string;
    nodeId?: string;
    pinName?: string;
    linkedTo?: string;
    fromNodeId?: string;
    fromPin?: string;
    fromPinName?: string;
    toNodeId?: string;
    toPin?: string;
    toPinName?: string;
    propertyName?: string;
    value?: unknown;
    properties?: Record<string, unknown>;
    compile?: boolean;
    save?: boolean;
    metadata?: Record<string, unknown>;
    // Variable configuration (C++ TryGetStringField/BoolField)
    variableType?: string;
    defaultValue?: unknown;
    category?: string;
    isReplicated?: boolean;
    isPublic?: boolean;
    variablePinType?: Record<string, unknown>;
    // Function configuration
    functionName?: string;
    inputs?: Array<{ name: string; type: string }>;
    outputs?: Array<{ name: string; type: string }>;
    parameters?: Array<{ name: string; type: string }>;
    // Rename operations
    oldName?: string;
    newName?: string;
    // Node positioning
    posX?: number;
    posY?: number;
    // Event configuration
    eventName?: string;
    // Component/SCS configuration
    componentClass?: string;
    parentComponent?: string;
    meshPath?: string;
    materialPath?: string;
    transform?: Record<string, unknown>;
    applyAndSave?: boolean;
    // Script configuration
    scriptName?: string;
    // Graph operations
    memberClass?: string;
    targetClass?: string;
    inputAxisName?: string;
    inputPin?: string;
    outputPin?: string;
    // Compilation options
    saveAfterCompile?: boolean;
    // Timing/async options
    timeoutMs?: number;
    waitForCompletion?: boolean;
    waitForCompletionTimeoutMs?: number;
    shouldExist?: boolean;
    // Parent class for blueprint creation
    parentClass?: string;
    // SCS operations array
    operations?: Array<Record<string, unknown>>;
}
