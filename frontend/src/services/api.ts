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
    const responseText =
      await response.text();

    throw new Error(
      `Practice API failed: ` +
      `${response.status} ` +
      responseText
    );
  }

  return response.json();
}
