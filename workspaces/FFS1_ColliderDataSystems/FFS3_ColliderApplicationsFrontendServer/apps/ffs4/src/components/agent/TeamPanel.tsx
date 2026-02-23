/**
 * TeamPanel — Agent team management UI
 *
 * Displays active team members, their status, and the mailbox.
 * Provides controls to create, dissolve, and interact with teams.
 */

import { useState, useEffect } from "react";
import { useSessionStore } from "../../stores/sessionStore";

interface TeamMember {
  sessionId: string;
  nodeId: string;
}

interface TeamStatus {
  teamId: string;
  status: "idle" | "running" | "completed" | "error";
  leader: TeamMember;
  members: TeamMember[];
  mailboxSize: number;
  unreadCount: number;
}

interface TeamPanelProps {
  onCreateTeam?: (nodeIds: string[]) => void;
}

export function TeamPanel({ onCreateTeam }: TeamPanelProps) {
  const [teams, setTeams] = useState<TeamStatus[]>([]);
  const [selectedTeam, setSelectedTeam] = useState<string | null>(null);
  const { sessionId, wsUrl } = useSessionStore();

  // Poll team status
  useEffect(() => {
    if (!wsUrl) return;

    const interval = setInterval(async () => {
      try {
        const resp = await fetch(
          wsUrl.replace("ws://", "http://").replace("wss://", "https://") + "/teams",
        );
        if (resp.ok) {
          setTeams(await resp.json());
        }
      } catch {
        // Silent — teams endpoint may not exist yet
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [wsUrl]);

  const activeTeam = teams.find((t) => t.teamId === selectedTeam);

  if (teams.length === 0) {
    return (
      <div style={{ padding: 12, color: "#6b7280", fontSize: 12, textAlign: "center" }}>
        No active teams. Select multiple nodes in the graph and use "Create Team" to start.
      </div>
    );
  }

  return (
    <div style={{ fontSize: 12, fontFamily: "system-ui, sans-serif" }}>
      {/* Team list */}
      <div style={{ padding: "8px 12px", borderBottom: "1px solid #e5e7eb" }}>
        <div style={{ fontSize: 10, fontWeight: 600, color: "#6b7280", marginBottom: 4 }}>
          TEAMS ({teams.length})
        </div>
        {teams.map((team) => (
          <button
            key={team.teamId}
            onClick={() => setSelectedTeam(team.teamId)}
            style={{
              display: "block",
              width: "100%",
              textAlign: "left",
              padding: "4px 8px",
              marginBottom: 2,
              background: selectedTeam === team.teamId ? "#eff6ff" : "transparent",
              border: selectedTeam === team.teamId ? "1px solid #bfdbfe" : "1px solid transparent",
              borderRadius: 4,
              cursor: "pointer",
              fontSize: 11,
            }}
          >
            <span style={{ fontWeight: 500 }}>{team.teamId}</span>
            <span style={{ marginLeft: 8, color: statusColor(team.status) }}>
              {team.status}
            </span>
            <span style={{ marginLeft: 8, color: "#6b7280" }}>
              {team.members.length} members
            </span>
            {team.unreadCount > 0 && (
              <span
                style={{
                  marginLeft: 8,
                  background: "#ef4444",
                  color: "#fff",
                  borderRadius: 8,
                  padding: "1px 5px",
                  fontSize: 9,
                }}
              >
                {team.unreadCount}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Team detail */}
      {activeTeam && (
        <div style={{ padding: "8px 12px" }}>
          <div style={{ fontSize: 10, fontWeight: 600, color: "#6b7280", marginBottom: 4 }}>
            MEMBERS
          </div>

          {/* Leader */}
          <div
            style={{
              padding: "4px 8px",
              marginBottom: 2,
              background: "#fef3c7",
              borderRadius: 4,
              border: "1px solid #fde68a",
            }}
          >
            <span style={{ fontWeight: 600, color: "#92400e" }}>leader</span>
            <span style={{ marginLeft: 8 }}>{activeTeam.leader.nodeId}</span>
          </div>

          {/* Members */}
          {activeTeam.members.map((member) => (
            <div
              key={member.sessionId}
              style={{
                padding: "4px 8px",
                marginBottom: 2,
                background: "#f9fafb",
                borderRadius: 4,
                border: "1px solid #e5e7eb",
              }}
            >
              <span style={{ color: "#6b7280" }}>member</span>
              <span style={{ marginLeft: 8 }}>{member.nodeId}</span>
            </div>
          ))}

          {/* Stats */}
          <div style={{ marginTop: 8, color: "#6b7280", fontSize: 10 }}>
            Mailbox: {activeTeam.mailboxSize} messages ({activeTeam.unreadCount} unread)
          </div>
        </div>
      )}
    </div>
  );
}

function statusColor(status: string): string {
  switch (status) {
    case "running":
      return "#3b82f6";
    case "completed":
      return "#10b981";
    case "error":
      return "#ef4444";
    default:
      return "#6b7280";
  }
}
