import type { ComponentInfo, Vector3 } from '../../../types/handlers/handler-types.js';
import { normalizeArgs, extractString } from '../foundation/arguments/argument-helper.js';
import { ActorActionHandler, ComponentsResult, executeActorRequest } from './actor-handler-utils.js';

export const handleApplyForce: ActorActionHandler = async (args, tools) => {
    const params = normalizeArgs(args, [
        { key: 'actorName', aliases: ['name'], required: true }
    ]);
    const actorName = extractString(params, 'actorName');
    const force = args.force as Vector3;

    const tryApplyForce = async (): Promise<Record<string, unknown>> => {
        return await executeActorRequest(tools, {
            action: 'apply_force',
            actorName,
            force
        });
    };

    try {
        return await tryApplyForce();
    } catch (error: unknown) {
        const errorMsg = error instanceof Error ? error.message : String(error);

        if (errorMsg.toUpperCase().includes('PHYSICS')) {
            try {
                const compsResult = await executeActorRequest(tools, {
                    action: 'get_components',
                    actorName
                }) as ComponentsResult;
                if (compsResult && compsResult.success && Array.isArray(compsResult.components)) {
                    const meshComp = compsResult.components.find((component: ComponentInfo) => {
                        const name = component.name || '';
                        return typeof name === 'string' && (
                            name.toLowerCase().includes('staticmesh') ||
                            name.toLowerCase().includes('mesh') ||
                            name.toLowerCase().includes('primitive')
                        );
                    });

                    if (meshComp) {
                        await executeActorRequest(tools, {
                            action: 'set_component_properties',
                            actorName,
                            componentName: meshComp.name,
                            properties: { SimulatePhysics: true, bSimulatePhysics: true, Mobility: 2 }
                        });
                        return await tryApplyForce();
                    }
                }
            } catch (retryError: unknown) {
                const retryMsg = retryError instanceof Error ? retryError.message : String(retryError);
                throw new Error(`${errorMsg} (Auto-enable physics failed: ${retryMsg})`);
            }
        }

        throw error;
    }
};
