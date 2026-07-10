export function getMessageText(content: unknown): string {
  if (typeof content === "string") return content;
  if (Array.isArray(content)) {
    return content
      .map((block) => {
        if (typeof block === "string") return block;
        if (block && typeof block === "object" && "text" in block) {
          return String((block as { text?: unknown }).text ?? "");
        }
        return "";
      })
      .join("");
  }
  return "";
}

export function toolLabel(name?: string): string {
  switch (name) {
    case "retrieve_information":
      return "Care guidelines";
    case "tavily_search":
    case "tavily_search_results_json":
      return "Web search";
    case "get_baby_profile":
      return "Baby profile";
    case "save_baby_fact":
      return "Remembering";
    default:
      return name ?? "tool";
  }
}
