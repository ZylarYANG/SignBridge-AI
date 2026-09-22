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
  const response =
    await fetch(
      `${API_BASE_URL}/api/practice`,
      {
        method: "POST",

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


export async function saveDatasetSample(
  payload: DatasetSampleRequest
): Promise<DatasetSampleResponse> {
  const response =
    await fetch(
      `${API_BASE_URL}/api/dataset/samples`,
      {
        method: "POST",

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
      `Dataset API failed: ` +
      `${response.status} ${text}`
    );
  }

  return response.json();
}
