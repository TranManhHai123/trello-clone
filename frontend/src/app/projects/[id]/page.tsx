"use client";
import { useEffect, useState, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { taskAPI, projectAPI, memberAPI, Member } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";
import { useTaskStore, Task } from "@/store/taskStore";
import Navbar from "@/components/Layout/Navbar";
import KanbanBoard from "@/components/Board/KanbanBoard";
import MemberPanel from "@/components/Members/MemberPanel";
import { ArrowLeft, Crown, Users } from "lucide-react";

interface Project {
  id: number;
  name: string;
  description: string | null;
  owner_id: number;
  owner_username: string | null;
}

type UserRole = "owner" | "member" | null;

export default function ProjectPage() {
  const { id } = useParams();
  const projectId = parseInt(id as string);
  const router = useRouter();
  const { user, token } = useAuthStore();
  const { setTasks, addTask, updateTask, removeTask } = useTaskStore();

  const [project, setProject] = useState<Project | null>(null);
  const [members, setMembers] = useState<Member[]>([]);
  const [currentUserRole, setCurrentUserRole] = useState<UserRole>(null);
  const [showMembers, setShowMembers] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // ── useEffect 1: Load dữ liệu ban đầu (giữ nguyên) ──────────────────────
  useEffect(() => {
    if (!token) {
      router.push("/");
      return;
    }

    Promise.all([
      projectAPI.getAll(),
      taskAPI.getByProject(projectId),
      memberAPI.getByProject(projectId),
    ])
      .then(([projectsRes, tasksRes, membersRes]) => {
        const found = projectsRes.data.find((p: Project) => p.id === projectId);
        setProject(found ?? null);
        setTasks(tasksRes.data);
        setMembers(membersRes.data);

        if (user) {
          const me = membersRes.data.find((m: Member) => m.user_id === user.id);
          setCurrentUserRole(me?.role ?? null);
        }
      })
      .catch((e) => {
        if (e.response?.status === 403) {
          setError("You don't have permission to view this project.");
        } else {
          setError("Failed to load project data.");
        }
      })
      .finally(() => setLoading(false));
  }, [token, projectId, router, setTasks, user]);

  // ── useEffect 2: WebSocket real-time ─────────────────────────────────────
  useEffect(() => {
    if (!token) return;

    const API_BASE = "http://192.168.1.238:8000";
    const wsBase = API_BASE.replace(/^http/, "ws");
    const wsUrl = `${wsBase}/ws/projects/${projectId}`;

    let ws: WebSocket | null = null;
    let isClosed = false; // flag để tránh tạo lại sau khi đã cleanup

    // Delay nhỏ để tránh Strict Mode double-invoke race condition
    const timer = setTimeout(() => {
      if (isClosed) return; // useEffect đã cleanup trước khi timer chạy

      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log(`[WS] Connected to project ${projectId}`);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "TASK_CREATED") {
            addTask(data.task as Task);
          } else if (data.type === "TASK_UPDATED") {
            updateTask(data.task.id, data.task as Partial<Task>);
          } else if (data.type === "TASK_DELETED") {
            removeTask(data.task_id as number);
          }
        } catch (err) {
          console.error("[WS] Failed to parse message:", err);
        }
      };

      ws.onerror = () => {
        console.error("[WS] Connection error — check backend is running");
      };

      ws.onclose = () => {
        console.log(`[WS] Disconnected from project ${projectId}`);
      };
    }, 100); // 100ms đủ để Strict Mode unmount giả hoàn thành

    return () => {
      isClosed = true;
      clearTimeout(timer);
      if (ws) {
        ws.close();
        ws = null;
      }
    };
  }, [projectId, token, addTask, updateTask, removeTask]);

  // ── Render ───────────────────────────────────────────────────────────────
  if (loading)
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <p className="text-center text-gray-500 py-20">Loading board...</p>
      </div>
    );

  if (!project)
    return (
      <div className="min-h-screen bg-gray-50">
        <Navbar />
        <p className="text-center text-red-500 py-20">
          Cannot find project with ID {projectId}.
        </p>
      </div>
    );

  return (
    <div className="min-h-screen bg-gray-100">
      <Navbar />

      <div className="px-6 py-4 bg-white border-b flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.push("/dashboard")}
            className="text-gray-500 hover:text-gray-800"
          >
            <ArrowLeft size={20} />
          </button>
          <div>
            <h2 className="font-bold text-gray-800">{project.name}</h2>
            <div className="flex items-center gap-3 mt-0.5">
              {project.description && (
                <p className="text-sm text-gray-500">{project.description}</p>
              )}
              {project.owner_username && (
                <p className="text-xs text-amber-600 flex items-center gap-1">
                  <Crown size={11} /> {project.owner_username}
                </p>
              )}
            </div>
          </div>
        </div>

        <button
          onClick={() => setShowMembers(!showMembers)}
          className={`flex items-center gap-2 px-3 py-1.5 rounded text-sm font-medium transition
            ${showMembers ? "bg-blue-100 text-blue-700" : "bg-gray-200 hover:bg-gray-300 text-gray-700"}`}
        >
          <Users size={16} /> Members
        </button>
      </div>

      {showMembers && (
        <div className="px-6 pb-3 pt-3">
          <MemberPanel
            projectId={projectId}
            currentUserRole={currentUserRole}
          />
        </div>
      )}

      <KanbanBoard
        projectId={projectId}
        members={members}
        currentUserRole={currentUserRole}
      />
    </div>
  );
}
