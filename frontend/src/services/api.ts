export type PracticeRequest = {
  request_id: string;
  target_sign_id: string;
  raw_frame_count: number;
  sequence_length: number;
  landmarks: number[][][];
};


export type PracticeResponse = {
  status: string;
  mode: string;
  request_id: string;
  target_sign_id: string;

  received_shape: [
    number,
    number,
    number
  ];

  message: string;
};


const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ??
  "http://127.0.0.1:8000";


export async function submitPractice(
  payload: PracticeRequest
): Promise<PracticeResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/practice`,
    {
      method: "POST",

      headers: {
        "Content-Type":
          "application/json",
      },

      body:
        JSON.stringify(payload),
    }
  );

  if (!response.ok) {
    const text =
      await response.text();

    throw new Error(
      `Practice API failed: ` +
      `${response.status} ${text}`
    );
  }

  return response.json();
}


export type RawDatasetLandmarkPoint = {
  x: number;
  y: number;
  valid: boolean;
};


export type RawDatasetFrame = {
  timestamp_ms: number;

  landmarks:
    RawDatasetLandmarkPoint[];
};


export type DatasetActiveHand =
  | "left"
  | "right"
  | "both"
  | "none";


export type DatasetSampleRequest = {
  schema_version: "1.0";

  sample_id: string;

  signer_id: string;
  sign_id: string;
  take_id: number;

  label: string;

  collection_profile:
    | "validation"
    | "formal"
    | "extended"
    | "custom";

  collection_session_id:
    string;

  capture: {
    duration_ms: number;
    raw_frame_count: number;
  };

  quality: {
    input_usable: boolean;

    landmark_valid_ratio:
      number;

    shoulder_usable_ratio:
      number;

    left_hand_usable_ratio:
      number;

    right_hand_usable_ratio:
      number;

    both_hands_usable_ratio:
      number;

    active_hand:
      DatasetActiveHand;
  };

  raw_frames:
    RawDatasetFrame[];

  model_input:
    number[][][];
};


export type DatasetSampleResponse = {
  status: string;
  sample_id: string;
  file_path: string;
  manifest_updated: boolean;
};


export type DatasetSampleSummary = {
  schema_version: string;

  sample_id: string;

  signer_id: string;
  sign_id: string;

  take_id: number;
  label: string;

  created_at?: string;

  raw_frame_count: number;
  duration_ms: number;

  input_usable: boolean;

  landmark_valid_ratio:
    number;

  shoulder_usable_ratio:
    number;

  left_hand_usable_ratio:
    number;

  right_hand_usable_ratio:
    number;

  both_hands_usable_ratio:
    number;

  active_hand:
    DatasetActiveHand;

  sample_path: string;
};


export type DatasetSamplesResponse = {
  status: string;
  count: number;

  samples:
    DatasetSampleSummary[];
};


export async function saveDatasetSample(
  payload: DatasetSampleRequest
): Promise<DatasetSampleResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/dataset/samples`,
    {
      method: "POST",

      headers: {
        "Content-Type":
          "application/json",
      },

      body:
        JSON.stringify(payload),
    }
  );

  if (!response.ok) {
    const text =
      await response.text();

    throw new Error(
      `Dataset API failed: ` +
      `${response.status} ${text}`
    );
  }

  return response.json();
}


export async function fetchDatasetSamples(
  signerId: string
): Promise<DatasetSamplesResponse> {
  const normalizedSigner =
    signerId
      .trim()
      .toUpperCase();

  const response = await fetch(
    `${API_BASE_URL}/api/dataset/samples` +
    `?signer_id=${encodeURIComponent(
      normalizedSigner
    )}`
  );

  if (!response.ok) {
    const text =
      await response.text();

    throw new Error(
      `Dataset list API failed: ` +
      `${response.status} ${text}`
    );
  }

  return response.json();
}


export async function deleteDatasetSample(
  sampleId: string
): Promise<void> {
  const response = await fetch(
    `${API_BASE_URL}/api/dataset/samples/` +
    encodeURIComponent(
      sampleId
    ),
    {
      method: "DELETE",
    }
  );

  if (!response.ok) {
    const text =
      await response.text();

    throw new Error(
      `Dataset delete API failed: ` +
      `${response.status} ${text}`
    );
  }
}


export type CollectorSourceType =
  | "team_member"
  | "friend_or_roommate"
  | "volunteer"
  | "other";


export type CollectorAgeGroup =
  | "under_18"
  | "18_25"
  | "26_40"
  | "41_60"
  | "60_plus"
  | "unspecified";


export type CollectorGender =
  | "male"
  | "female"
  | "other"
  | "prefer_not_to_say"
  | "unspecified";


export type CollectorDominantHand =
  | "left"
  | "right"
  | "both"
  | "unspecified";


export type CollectorProfile = {
  signer_id: string;

  source_type:
    CollectorSourceType;

  age_group:
    CollectorAgeGroup;

  gender:
    CollectorGender;

  dominant_hand:
    CollectorDominantHand;

  consent_confirmed:
    boolean;

  note: string;

  created_at:
    string | null;

  updated_at:
    string | null;
};


export type CollectorProfileUpdate = {
  source_type:
    CollectorSourceType;

  age_group:
    CollectorAgeGroup;

  gender:
    CollectorGender;

  dominant_hand:
    CollectorDominantHand;

  consent_confirmed:
    boolean;

  note: string;
};


export async function fetchCollectorProfile(
  signerId: string
): Promise<{
  status: string;
  exists: boolean;
  profile: CollectorProfile;
}> {
  const normalized =
    signerId
      .trim()
      .toUpperCase();

  const response =
    await fetch(
      `${API_BASE_URL}/api/dataset/signers/` +
      encodeURIComponent(
        normalized
      )
    );

  if (!response.ok) {
    const text =
      await response.text();

    throw new Error(
      `Collector profile API failed: ` +
      `${response.status} ${text}`
    );
  }

  return response.json();
}


export async function saveCollectorProfile(
  signerId: string,
  payload: CollectorProfileUpdate
): Promise<{
  status: string;
  profile: CollectorProfile;
}> {
  const normalized =
    signerId
      .trim()
      .toUpperCase();

  const response =
    await fetch(
      `${API_BASE_URL}/api/dataset/signers/` +
      encodeURIComponent(
        normalized
      ),
      {
        method: "PUT",

        headers: {
          "Content-Type":
            "application/json",
        },

        body:
          JSON.stringify(
            payload
          ),
      }
    );

  if (!response.ok) {
    const text =
      await response.text();

    throw new Error(
      `Collector profile save failed: ` +
      `${response.status} ${text}`
    );
  }

  return response.json();
}
