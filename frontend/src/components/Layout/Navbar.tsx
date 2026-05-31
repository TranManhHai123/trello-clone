"use client";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/authStore";

export default function Navbar() {
  const { user, logout } = useAuthStore();
  const router = useRouter();

  const handleLogout = () => {
    logout();
    router.push("/");
  };

  return (
    <nav className="bg-blue-600 text-white px-6 py-3 flex items-center justify-between shadow-md">
      <span
        onClick={() => router.push("/dashboard")}
        className="font-bold text-lg cursor-pointer hover:opacity-80"
      >
        🗂️ Trello Clone
      </span>
      <div className="flex items-center gap-4">
        <span className="text-sm opacity-90">👤 {user?.username ?? "..."}</span>
        <button
          onClick={handleLogout}
          className="bg-white text-blue-600 text-sm font-medium px-3 py-1 rounded-lg hover:bg-blue-50"
        >
          Logout
        </button>
      </div>
    </nav>
  );
}
