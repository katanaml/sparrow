const SERVER_TZ = Intl.DateTimeFormat().resolvedOptions().timeZone;

export function timestamp(): string {
  return new Date().toLocaleString("en-CA", {
    timeZone: SERVER_TZ,
    year: "numeric", month: "2-digit", day: "2-digit",
    hour: "2-digit", minute: "2-digit", second: "2-digit",
    hour12: false,
  }).replace(",", "");
}