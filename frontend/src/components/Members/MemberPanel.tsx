"use client";
import { useState, useEffect } from "react";
import { UserPlus, Trash2, Crown, User } from "lucide-react";
import api from "@/lib/api";

interface Member {
  id: number;
  user_id: number;
  role: "owner" | "member";
  user_email: string;
  username: string;
}

interface Props {
  projectId: number;
  currentUserRole: "owner" | "member" | null;
}

export default function MemberPanel({ projectId, currentUserRole }: Props) {
  const [members, setMembers] = useState<Member[]>([]);
  const [inviteUsername, setInviteUsername] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const fetchMembers = async () => {
    try {
      const res = await api.get(`/projects/${projectId}/members`);
      setMembers(res.data);
    } catch {
      console.error("Cannot fetch members");
    }
  };

  useEffect(() => {
    fetchMembers();
  }, [projectId]);

  const handleInvite = async () => {
    if (!inviteUsername.trim()) return;
    setLoading(true);
    setError("");
    setSuccess("");
    try {
      await api.post(`/projects/${projectId}/members`, {
        username: inviteUsername.trim(),
        role: "member",
      });
      setInviteUsername("");
      setSuccess(`Successfully invited "${inviteUsername.trim()}"`);
      setTimeout(() => setSuccess(""), 5000);
      fetchMembers();
    } catch (e: any) {
      setError(
        e.response?.data?.detail || "User not found or already a member",
      );
    } finally {
      setLoading(false);
    }
  };

  const handleRemove = async (userId: number) => {
    try {
      await api.delete(`/projects/${projectId}/members/${userId}`);
      fetchMembers();
    } catch (e: any) {
      setError(e.response?.data?.detail || "Failed to remove member");
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-4 w-72">
      <h3 className="font-semibold text-gray-700 mb-3 flex items-center gap-2">
        <User size={16} /> Members ({members.length})
      </h3>

      {/* Danh sách thành viên */}
      <ul className="space-y-2 mb-4">
        {members.map((m) => (
          <li key={m.id} className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2">
              {m.role === "owner" ? (
                <Crown size={14} className="text-yellow-500" />
              ) : (
                <User size={14} className="text-gray-400" />
              )}
              <span className="text-gray-700 truncate max-w-[140px]">
                {m.username ?? m.user_email}
              </span>
            </div>
            {currentUserRole === "owner" && m.role !== "owner" && (
              <button
                onClick={() => handleRemove(m.user_id)}
                className="text-red-400 hover:text-red-600 transition"
              >
                <Trash2 size={14} />
              </button>
            )}
          </li>
        ))}
      </ul>

      {/* Form mời thành viên — chỉ hiển thị với owner */}
      {currentUserRole === "owner" && (
        <div className="border-t pt-3">
          <p className="text-xs text-gray-500 mb-2 flex items-center gap-1">
            <UserPlus size={12} /> Invite new members
          </p>
          <div className="flex gap-2">
            <input
              type="text"
              value={inviteUsername}
              onChange={(e) => setInviteUsername(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleInvite()}
              placeholder="Enter username..."
              className="flex-1 border-2 border-gray-300 rounded px-2 py-1 text-sm text-gray-900 bg-white placeholder-gray-400 focus:outline-none focus:border-blue-400"
            />
            <button
              onClick={handleInvite}
              disabled={loading}
              className="bg-blue-500 hover:bg-blue-600 text-white text-sm px-3 py-1 rounded disabled:opacity-50 transition"
            >
              Invite
            </button>
          </div>
          {error && <p className="text-red-500 text-xs mt-1">{error}</p>}
          {success && <p className="text-green-500 text-xs mt-1">{success}</p>}
        </div>
      )}
    </div>
  );
}
