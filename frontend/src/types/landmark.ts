export type LandmarkPoint = {
  x: number;
  y: number;
  valid: boolean;
};

export type LandmarkFrame = {
  timestampMs: number;

  /**
   * Canonical SignBridge order:
   *
   * 0-20   Left hand
   * 21-41  Right hand
   * 42     Nose
   * 43     Mouth left
   * 44     Mouth right
   * 45     Left shoulder
   * 46     Right shoulder
   * 47     Left elbow
   * 48     Right elbow
   * 49     Left wrist
   * 50     Right wrist
   * 51     Left hip
   * 52     Right hip
   * 53     Shoulder center
   */
  landmarks: LandmarkPoint[];
};

export type CaptureSequence = {
  startedAt: number;
  endedAt: number;
  frames: LandmarkFrame[];
};
