const SKELETON_TO_MESH_MAP: Record<string, string> = {
  '/Game/Mannequin/Character/Mesh/UE4_Mannequin_Skeleton': '/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple',
  '/Game/Characters/Mannequins/Meshes/SK_Mannequin': '/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple',
  '/Game/Mannequin/Character/Mesh/SK_Mannequin': '/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple',
  '/Game/Characters/Mannequin_UE4/Meshes/UE4_Mannequin_Skeleton': '/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple',
  '/Game/Characters/Mannequins/Skeletons/UE5_Mannequin_Skeleton': '/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple',
  '/Game/Characters/Mannequins/Skeletons/UE5_Female_Mannequin_Skeleton': '/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple',
  '/Game/Characters/Mannequins/Skeletons/UE5_Manny_Skeleton': '/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple',
  '/Game/Characters/Mannequins/Skeletons/UE5_Quinn_Skeleton': '/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple'
};

const SKELETAL_MESH_REPLACEMENTS: Record<string, string> = {
  '/SK_': '/SKM_',
  'UE4_Mannequin': 'SKM_Manny',
  'UE5_Mannequin': 'SKM_Manny',
  'UE5_Manny': 'SKM_Manny',
  'UE5_Quinn': 'SKM_Quinn'
};

const SKELETAL_MESH_REPLACEMENT_PATTERN = /\/SK_|UE4_Mannequin|UE5_Mannequin|UE5_Manny|UE5_Quinn/g;

export function resolveNormalizedSkeletalMeshPath(normalizedInput: string): string {
  const knownMeshPath = SKELETON_TO_MESH_MAP[normalizedInput];
  if (knownMeshPath) {
    return knownMeshPath;
  }

  if (normalizedInput.includes('_Skeleton')) {
    return normalizedInput
      .replace('_Skeleton', '')
      .replace(
        SKELETAL_MESH_REPLACEMENT_PATTERN,
        match => SKELETAL_MESH_REPLACEMENTS[match] ?? match
      );
  }

  if (normalizedInput.includes('/SK_')) {
    return normalizedInput.replace('/SK_', '/SKM_');
  }

  return normalizedInput;
}
