export type CollectionProfileId =
  | "validation"
  | "formal"
  | "extended"
  | "custom";


export type CollectionProfile = {
  id: CollectionProfileId;

  name: string;

  description: string;

  targetTakes: number;
};


export const COLLECTION_PROFILES:
  CollectionProfile[] = [
    {
      id: "validation",

      name: "可行性验证",

      description:
        "用于快速验证动作、质量门控和训练链路。",

      targetTakes: 5,
    },

    {
      id: "formal",

      name: "正式训练",

      description:
        "正式数据集标准，每人每词至少 20 次。",

      targetTakes: 20,
    },

    {
      id: "extended",

      name: "强化采集",

      description:
        "用于重点类别、易混淆类别和比赛强化数据。",

      targetTakes: 50,
    },

    {
      id: "custom",

      name: "自定义",

      description:
        "特殊实验或后续扩展使用。",

      targetTakes: 20,
    },
  ];


export function getCollectionProfile(
  id: CollectionProfileId
): CollectionProfile {
  return (
    COLLECTION_PROFILES.find(
      (profile) =>
        profile.id === id
    )
    ??
    COLLECTION_PROFILES[0]
  );
}
