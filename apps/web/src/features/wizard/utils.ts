export const CANONICAL_ISLANDS = [
  "Port Blair",
  "Swaraj Dweep (Havelock)",
  "Shaheed Dweep (Neil)",
  "Baratang",
  "Diglipur",
  "Rangat",
  "Mayabunder",
  "Little Andaman",
] as const;

export function resolvePrimaryIsland(
  day?: { primary_island?: any; attractions?: any; ferry?: any },
  dayIdx: number = 0
): string {
  const attractions = Array.isArray(day?.attractions) ? day.attractions : [];
  const attractionsText = attractions.join(" ").toLowerCase();
  const ferryText = typeof day?.ferry === "string" ? day.ferry.toLowerCase() : "";
  const primary = typeof day?.primary_island === "string" ? day.primary_island.trim() : "";

  // 1. Distinct attractions have highest priority because user specifically chose them in Step 2
  if (["havelock", "swaraj", "radhanagar", "elephant beach", "kalapathar", "vijaynagar"].some(k => attractionsText.includes(k))) {
    return "Swaraj Dweep (Havelock)";
  }
  if (["neil", "shaheed", "bharatpur", "laxmanpur", "natural bridge", "sitapur"].some(k => attractionsText.includes(k))) {
    return "Shaheed Dweep (Neil)";
  }
  if (["baratang", "limestone caves", "mud volcano", "parrot island", "nilambur"].some(k => attractionsText.includes(k))) {
    return "Baratang";
  }
  if (["diglipur", "ross and smith", "saddle peak", "ram nagar", "aerial bay"].some(k => attractionsText.includes(k))) {
    return "Diglipur";
  }
  if (["rangat", "dhaninallah", "amkunj", "yerrata"].some(k => attractionsText.includes(k))) {
    return "Rangat";
  }
  if (["mayabunder", "karmatang"].some(k => attractionsText.includes(k))) {
    return "Mayabunder";
  }
  if (["little andaman", "butler bay", "white surf", "hut bay"].some(k => attractionsText.includes(k))) {
    return "Little Andaman";
  }
  if (["cellular", "corbyn", "marina", "flag point", "chidiya", "ross island", "north bay", "jolly buoy", "wandoor", "chatham", "samudrika", "anthropological", "munda pahar", "mount harriet", "mount manipur", "port blair"].some(k => attractionsText.includes(k))) {
    return "Port Blair";
  }

  // 2. Check ferry arrival destination
  if (ferryText && ferryText !== "none") {
    if (ferryText.includes("to swaraj dweep") || ferryText.includes("to havelock")) return "Swaraj Dweep (Havelock)";
    if (ferryText.includes("to shaheed dweep") || ferryText.includes("to neil")) return "Shaheed Dweep (Neil)";
    if (ferryText.includes("to baratang")) return "Baratang";
    if (ferryText.includes("to diglipur")) return "Diglipur";
    if (ferryText.includes("to little andaman")) return "Little Andaman";
    if (ferryText.includes("to rangat")) return "Rangat";
    if (ferryText.includes("to port blair")) return "Port Blair";
  }

  // 3. Check explicit primary_island
  const lowerPrimary = primary.toLowerCase();
  if (lowerPrimary.includes("havelock") || lowerPrimary.includes("swaraj")) return "Swaraj Dweep (Havelock)";
  if (lowerPrimary.includes("neil") || lowerPrimary.includes("shaheed")) return "Shaheed Dweep (Neil)";
  if (lowerPrimary.includes("baratang")) return "Baratang";
  if (lowerPrimary.includes("diglipur")) return "Diglipur";
  if (lowerPrimary.includes("rangat")) return "Rangat";
  if (lowerPrimary.includes("mayabunder")) return "Mayabunder";
  if (lowerPrimary.includes("little andaman")) return "Little Andaman";
  if (lowerPrimary.includes("port blair")) return "Port Blair";

  return primary || (dayIdx === 0 ? "Port Blair" : "Swaraj Dweep (Havelock)");
}
