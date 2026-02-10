import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Youtube,
  Clock,
  Plus,
  LayoutDashboard,
  X,
  PanelLeftClose,
  Settings,
  LogIn,
} from "./ui/Icons";
import { VideoData } from "../types";
import { useAuth } from "../contexts/AuthContext";

interface SidebarLeftProps {
  videos: VideoData[];
  activeVideoId: string | null;
  onSelectVideo: (video: VideoData) => void;
  onAddNew: () => void;
  isOpen: boolean;
  setIsOpen: (open: boolean) => void;
}

export const SidebarLeft: React.FC<SidebarLeftProps> = ({
  videos,
  activeVideoId,
  onSelectVideo,
  onAddNew,
  isOpen,
  setIsOpen,
}) => {
  const { user, signInWithGoogle } = useAuth();
  return (
    <>
      {/* Mobile Overlay */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-30 md:hidden"
            onClick={() => setIsOpen(false)}
          />
        )}
      </AnimatePresence>

      {/* Sidebar Container */}
      <motion.aside
        initial={false}
        animate={{
          width: isOpen ? 280 : 0,
          x: isOpen ? 0 : 0,
        }}
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
        className={`
          fixed md:relative z-40 h-full
          flex flex-col
          border-r border-white/10
          bg-black/20 backdrop-blur-2xl
          overflow-hidden
          whitespace-nowrap
          shadow-2xl
        `}
        style={{
          position: window.innerWidth < 768 ? "fixed" : undefined,
          left: 0,
          top: 0,
          bottom: 0,
          x: window.innerWidth < 768 && !isOpen ? "-100%" : 0,
        }}
      >
        <div className="p-4 pt-6 flex items-center justify-between">
          <div className="flex items-center gap-2 px-2 text-white font-bold tracking-tight">
            <div className="bg-blue-500/20 p-1.5 rounded-lg">
              <LayoutDashboard className="text-blue-400" size={18} />
            </div>
            <span className="text-lg">Lumina</span>
          </div>
          {/* Close Button - Visible on both Mobile and Desktop now */}
          <button
            onClick={() => setIsOpen(false)}
            className="p-2 text-slate-400 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
            title="Close Sidebar"
          >
            <PanelLeftClose size={20} />
          </button>
        </div>

        <div className="p-4">
          <button
            onClick={onAddNew}
            className="w-full flex items-center gap-3 bg-blue-600/90 hover:bg-blue-500 text-white p-3 rounded-xl transition-all duration-300 shadow-lg shadow-blue-900/20 group border border-blue-400/20"
          >
            <div className="bg-white/20 p-1 rounded-md group-hover:scale-110 transition-transform">
              <Plus size={16} />
            </div>
            <span className="font-semibold text-sm">New Analysis</span>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-3 space-y-1 custom-scrollbar py-2">
          {videos.length > 0 ? (
            <div className="px-3 py-2 text-[10px] font-bold text-slate-500 uppercase tracking-widest">
              Library
            </div>
          ) : (
            <div className="px-4 py-8 text-center text-slate-500 text-sm font-light">
              No videos yet.
            </div>
          )}

          {videos.map((video) => (
            <button
              key={video.id}
              onClick={() => {
                onSelectVideo(video);
                if (window.innerWidth < 768) setIsOpen(false);
              }}
              className={`
                        w-full text-left p-3 rounded-xl transition-all duration-200 group
                        flex items-start gap-3 border
                        ${
                          activeVideoId === video.id
                            ? "bg-white/10 border-white/20 shadow-md backdrop-blur-md"
                            : "hover:bg-white/5 border-transparent hover:border-white/5"
                        }
                    `}
            >
              <div className="relative shrink-0 w-10 h-10 rounded-lg overflow-hidden bg-slate-800 border border-white/10 group-hover:border-white/30 transition-colors shadow-sm">
                <img
                  src={video.thumbnail}
                  alt=""
                  className="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition-opacity"
                />
              </div>
              <div className="flex-1 min-w-0 flex flex-col justify-center gap-0.5">
                <h3
                  className={`text-xs font-medium truncate ${activeVideoId === video.id ? "text-white" : "text-slate-300 group-hover:text-white"}`}
                >
                  {video.title}
                </h3>
                <div className="flex items-center gap-1.5 text-[10px] text-slate-500 group-hover:text-slate-400">
                  <Clock size={10} />
                  <span>{video.dateAdded}</span>
                </div>
              </div>
            </button>
          ))}
        </div>

        <div className="p-4 border-t border-white/5 mt-auto bg-black/20 backdrop-blur-md">
          {user ? (
            <div className="flex items-center gap-3 p-2 rounded-xl hover:bg-white/5 cursor-pointer transition-colors group">
              <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-blue-500 to-purple-500 flex items-center justify-center text-xs font-bold text-white shadow-lg ring-2 ring-transparent group-hover:ring-white/20 transition-all">
                {user.displayName
                  ? user.displayName.charAt(0).toUpperCase()
                  : "U"}
              </div>
              <div className="flex-1 overflow-hidden">
                <p className="text-white text-sm font-medium truncate">
                  {user.displayName || "User"}
                </p>
                <p className="text-blue-300/80 text-[10px] font-medium tracking-wide">
                  PRO MEMBER
                </p>
              </div>
              <Settings
                size={16}
                className="text-slate-500 group-hover:text-white transition-colors"
              />
            </div>
          ) : (
            <button
              onClick={() => signInWithGoogle()}
              className="w-full flex items-center gap-3 p-2 rounded-xl bg-blue-600/20 hover:bg-blue-600/40 text-blue-300 hover:text-white border border-blue-500/30 transition-all group"
            >
              <div className="w-9 h-9 rounded-full bg-blue-500/20 flex items-center justify-center">
                <LogIn size={18} />
              </div>
              <div className="flex-1 text-left">
                <p className="text-sm font-medium">Sign In</p>
                <p className="text-[10px] opacity-70">Save your history</p>
              </div>
            </button>
          )}
        </div>
      </motion.aside>
    </>
  );
};
