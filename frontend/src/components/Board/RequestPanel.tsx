"use client";
import { taskRequestAPI } from "@/lib/api";

interface TaskRequest {
  id: number;
  task_id: number | null;
  task_title: string | null;
  requester_username: string | null;
  action_type: "create" | "update" | "delete";
  payload: Record<string, any> | null;
}

interface RequestPanelProps {
  projectId: number;
  requests: TaskRequest[];
  onResolved: (requestId: number) => void;
}

export default function RequestPanel({
  projectId,
  requests,
  onResolved,
}: RequestPanelProps) {
  const handleResolve = async (
    requestId: number,
    decision: "approved" | "rejected",
  ) => {
    try {
      await taskRequestAPI.resolve(projectId, requestId, decision);
      onResolved(requestId);
    } catch {
      alert("Cannot handle this request");
    }
  };

  if (requests.length === 0) return null;

  return (
    <div className="bg-white border rounded-lg p-4 mb-4 shadow-sm">
      <h3 className="font-bold text-gray-800">
        📥 Wating for approval ({requests.length})
      </h3>
      <div className="space-y-2">
        {requests.map((r) => (
          <div
            key={r.id}
            className="flex items-center justify-between border rounded p-2 text-sm"
          >
            <span className="text-sm text-gray-500">
              <b>@{r.requester_username}</b> wants <b>{r.action_type}</b> task{" "}
              <b>"{r.task_title ?? `#${r.task_id}`}"</b>
              {r.payload?.title ? ` → title: "${r.payload.title}"` : ""}
              {r.payload?.status ? ` → status: "${r.payload.status}"` : ""}
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => handleResolve(r.id, "approved")}
                className="text-green-600 hover:underline"
              >
                Approve
              </button>
              <button
                onClick={() => handleResolve(r.id, "rejected")}
                className="text-red-600 hover:underline"
              >
                Reject
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
