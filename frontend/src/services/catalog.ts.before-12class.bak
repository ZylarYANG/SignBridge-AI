export type HandednessPolicy =
  | "dominant_either"
  | "both_hands";


export type DirectionReference =
  | "body_relative"
  | "self_relative"
  | "interlocutor_relative";


export type RequiredPart =
  | "upper_body"
  | "active_hand"
  | "both_hands";


export type CollectionSign = {
  classId: number;

  signId: string;

  label: string;

  handednessPolicy:
    HandednessPolicy;

  requiredParts:
    RequiredPart[];

  directionReference:
    DirectionReference;

  directionSensitive:
    boolean;

  verificationStatus?:
    string;

  researchConfidence?:
    string;
};


export type QualityPolicy = {
  fullCanonicalRequired:
    boolean;

  canonical54DiagnosticOnly:
    boolean;

  minimumRawFrames:
    number;

  minimumShoulderUsableRatio:
    number;

  minimumSingleHandUsableRatio:
    number;

  minimumBothHandsUsableRatio:
    number;

  minimumHandLandmarkRatioPerFrame:
    number;
};


export type CollectionCatalog = {
  schemaVersion: string;

  catalogName: string;

  modelInput: {
    sequenceLength:
      number;

    landmarkCount:
      number;

    coordinateCount:
      number;

    coordinateReference:
      string;

    normalization: {
      origin: string;
      scale: string;
    };
  };

  qualityPolicy:
    QualityPolicy;

  signs:
    CollectionSign[];
};


type RawCatalog = {
  schema_version: string;

  catalog_name: string;

  model_input: {
    sequence_length:
      number;

    landmark_count:
      number;

    coordinate_count:
      number;

    coordinate_reference:
      string;

    normalization: {
      origin: string;
      scale: string;
    };
  };

  quality_policy: {
    full_canonical_required:
      boolean;

    canonical_54_over_54_is_diagnostic_only:
      boolean;

    minimum_raw_frames:
      number;

    minimum_shoulder_usable_ratio:
      number;

    minimum_single_hand_usable_ratio:
      number;

    minimum_both_hands_usable_ratio:
      number;

    minimum_hand_landmark_ratio_per_frame:
      number;
  };

  signs: Array<{
    class_id:
      number;

    sign_id:
      string;

    label:
      string;

    handedness_policy:
      HandednessPolicy;

    required_parts:
      RequiredPart[];

    direction_reference:
      DirectionReference;

    direction_sensitive:
      boolean;

    verification_status?:
      string;

    research_confidence?:
      string;
  }>;
};


const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL
  ??
  "http://127.0.0.1:8000";


export async function fetchSignCatalog(
): Promise<CollectionCatalog> {
  const response =
    await fetch(
      `${API_BASE_URL}/api/dataset/catalog`
    );

  if (!response.ok) {
    const text =
      await response.text();

    throw new Error(
      "Catalog API failed: "
      +
      `${response.status} ${text}`
    );
  }

  const raw = (await response.json()) as RawCatalog;


  const signs =
    raw.signs
      .map(
        (sign) => ({
          classId:
            sign.class_id,

          signId:
            sign.sign_id,

          label:
            sign.label,

          handednessPolicy:
            sign.handedness_policy,

          requiredParts:
            sign.required_parts,

          directionReference:
            sign.direction_reference,

          directionSensitive:
            sign.direction_sensitive,

          verificationStatus:
            sign.verification_status,

          researchConfidence:
            sign.research_confidence,
        })
      )
      .sort(
        (a, b) =>
          a.classId -
          b.classId
      );


  return {
    schemaVersion:
      raw.schema_version,

    catalogName:
      raw.catalog_name,

    modelInput: {
      sequenceLength:
        raw
          .model_input
          .sequence_length,

      landmarkCount:
        raw
          .model_input
          .landmark_count,

      coordinateCount:
        raw
          .model_input
          .coordinate_count,

      coordinateReference:
        raw
          .model_input
          .coordinate_reference,

      normalization: {
        origin:
          raw
            .model_input
            .normalization
            .origin,

        scale:
          raw
            .model_input
            .normalization
            .scale,
      },
    },

    qualityPolicy: {
      fullCanonicalRequired:
        raw
          .quality_policy
          .full_canonical_required,

      canonical54DiagnosticOnly:
        raw
          .quality_policy
          .canonical_54_over_54_is_diagnostic_only,

      minimumRawFrames:
        raw
          .quality_policy
          .minimum_raw_frames,

      minimumShoulderUsableRatio:
        raw
          .quality_policy
          .minimum_shoulder_usable_ratio,

      minimumSingleHandUsableRatio:
        raw
          .quality_policy
          .minimum_single_hand_usable_ratio,

      minimumBothHandsUsableRatio:
        raw
          .quality_policy
          .minimum_both_hands_usable_ratio,

      minimumHandLandmarkRatioPerFrame:
        raw
          .quality_policy
          .minimum_hand_landmark_ratio_per_frame,
    },

    signs,
  };
}
