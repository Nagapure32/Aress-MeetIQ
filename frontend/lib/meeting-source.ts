export function isUploadedMeetingSource(sourceType?: string | null): boolean {
  return sourceType === "upload" || sourceType === "uploaded_recording";
}

export function isManualLiveMeetingSource(sourceType?: string | null): boolean {
  return sourceType === "manual_live";
}

export function getMeetingSourceLabel(sourceType?: string | null): string {
  if (isUploadedMeetingSource(sourceType)) {
    return "Uploaded recording";
  }
  if (isManualLiveMeetingSource(sourceType)) {
    return "Manual meeting";
  }
  return "Calendar meeting";
}
