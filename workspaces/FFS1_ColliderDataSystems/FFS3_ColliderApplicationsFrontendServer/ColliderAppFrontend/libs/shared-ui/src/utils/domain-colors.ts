export type DomainType =
  | "CLOUD"
  | "FILESYST"
  | "ADMIN"
  | "SIDEPANEL"
  | "AGENT_SEAT";

export const DOMAIN_BADGE_COLORS: Record<DomainType, string> = {
  CLOUD: "border-green-500 text-green-400",
  FILESYST: "border-blue-500 text-blue-400",
  ADMIN: "border-red-500 text-red-400",
  SIDEPANEL: "border-purple-500 text-purple-400",
  AGENT_SEAT: "border-yellow-500 text-yellow-400",
};

export function getDomainColor(domain: string): string {
  return (
    DOMAIN_BADGE_COLORS[domain as DomainType] ?? "border-gray-500 text-gray-400"
  );
}
