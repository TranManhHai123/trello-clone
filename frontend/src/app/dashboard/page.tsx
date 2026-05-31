"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { projectAPI } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";
import Navbar from "@/components/Layout/Navbar";
import { Plus, Trash2, FolderOpen, Crown } from "lucide-react";

interface Project {
  id: number;
  name: string;
  description: string | null;
  owner_id: number;
  owner_username: string | null;
}

export default function DashboardPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [creating, setCreating] = useState(false);
  const [showForm, setShowForm] = useState(false);

  const { token } = useAuthStore();
  const router = useRouter();

  // Chưa đăng nhập → về trang login
  useEffect(() => {
    if (!token) {
      router.push("/");
      return;
    }
    projectAPI
      .getAll()
      .then((res) => setProjects(res.data))
      .finally(() => setLoading(false));
  }, [token, router]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    setCreating(true);
    try {
      const res = await projectAPI.create({
        name: name.trim(),
        description: description.trim() || undefined,
      });
      setProjects((prev) => [...prev, res.data]);
      setName("");
      setDescription("");
      setShowForm(false);
    } catch {
      alert("Failed to create project");
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: number, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("Delete this project? All tasks within will also be deleted."))
      return;
    try {
      await projectAPI.delete(id);
      setProjects((prev) => prev.filter((p) => p.id !== id));
    } catch {
      alert("Failed to delete project");
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <main className="max-w-5xl mx-auto px-6 py-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-gray-800">Projects list</h2>
          <button
            onClick={() => setShowForm(!showForm)}
            className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm font-medium"
          >
            <Plus size={16} /> Create Project
          </button>
        </div>

        {/* Form tạo project */}
        {showForm && (
          <form
            onSubmit={handleCreate}
            className="bg-white border rounded-xl p-5 mb-6 shadow-sm space-y-3"
          >
            <h3 className="font-semibold text-gray-700">Create Project</h3>
            <input
              autoFocus
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Project Name *"
              className="w-full border border-gray-300 rounded-lg p-3 text-gray-900 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-300"
              required
            />
            <input
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Description (optional)"
              className="w-full border border-gray-300 rounded-lg p-3 text-gray-900 placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-300"
            />
            <div className="flex gap-3">
              <button
                type="submit"
                disabled={creating}
                className="bg-blue-600 text-white px-5 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 text-sm font-medium"
              >
                {creating ? "Creating..." : "Create"}
              </button>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="bg-gray-200 text-gray-700 px-5 py-2 rounded-lg hover:bg-gray-300 text-sm"
              >
                Cancel
              </button>
            </div>
          </form>
        )}

        {/* Danh sách projects */}
        {loading ? (
          <p className="text-gray-500 text-center py-12">Loading...</p>
        ) : projects.length === 0 ? (
          <div className="text-center py-16 text-gray-400">
            <FolderOpen size={48} className="mx-auto mb-3 opacity-40" />
            <p>No projects available. Create your first project!</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {projects.map((project) => (
              <div
                key={project.id}
                onClick={() => router.push(`/projects/${project.id}`)}
                className="bg-white border rounded-xl p-5 cursor-pointer hover:shadow-md hover:border-blue-300 transition-all group"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-800 group-hover:text-blue-600">
                      {project.name}
                    </h3>
                    {project.description && (
                      <p className="text-sm text-gray-500 mt-1 line-clamp-2">
                        {project.description}
                      </p>
                    )}
                    {project.owner_username && (
                      <p className="text-xs text-amber-600 mt-2 flex items-center gap-1">
                        <Crown size={11} /> {project.owner_username}
                      </p>
                    )}
                  </div>
                  <button
                    onClick={(e) => handleDelete(project.id, e)}
                    className="opacity-0 group-hover:opacity-100 ml-2 text-gray-400 hover:text-red-500 transition-opacity"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
