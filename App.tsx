import React, { useState, useEffect, useRef } from "react";
import { SidebarLeft } from "./components/SidebarLeft";
import { ChatArea } from "./components/ChatArea";
import { NewVideoModal } from "./components/NewVideoModal";
import { LoginModal } from "./components/LoginModal";
import { useAuth } from "./contexts/AuthContext";
import { YouTubePlayer } from "./components/YouTubePlayer";
import {
  analyzeVideo,
  extractYoutubeId,
  createChatSession,
  sendChatMessage,
} from "./services/apiService";
import { VideoData, Message, ProcessingState } from "./types";
import {
  Menu,
  Sparkles,
  Link,
  ChevronRight,
  Play,
  Clock,
  FileText,
  Settings,
  Bot,
} from "./components/ui/Icons";
import { GenerateContentResponse, Chat } from "@google/genai";
import { AnimatePresence, motion } from "framer-motion";
import ReactMarkdown from "react-markdown";

const App: React.FC = () => {
  const { user, loading } = useAuth();
  const [showLogin, setShowLogin] = useState(false);
  const [hasApiKey, setHasApiKey] = useState(false);

  useEffect(() => {
    // Only show login if explicitly requested or if valid session check fails for protected route (not implemented yet)
    // For Guest Mode, we do NOT force login on load.
    // if (!loading && !user) {
    //   setShowLogin(true);
    // }
  }, [user, loading]);
  // Data State
  const [videos, setVideos] = useState<VideoData[]>([]);
  const [activeVideoId, setActiveVideoId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [processingState, setProcessingState] = useState<ProcessingState>(
    ProcessingState.IDLE,
  );

  // UI State
  const [leftSidebarOpen, setLeftSidebarOpen] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [chatSessionId, setChatSessionId] = useState<string | null>(null);

  // Player State
  const [player, setPlayer] = useState<any>(null);

  // Input State (Landing)
  const [urlInput, setUrlInput] = useState("");

  // Refs
  const chatSessionRef = useRef<Chat | null>(null);

  // Check for API Key on mount
  useEffect(() => {
    const checkApiKey = async () => {
      if (
        (window as any).aistudio &&
        (window as any).aistudio.hasSelectedApiKey
      ) {
        const hasKey = await (window as any).aistudio.hasSelectedApiKey();
        setHasApiKey(hasKey);
      } else {
        setHasApiKey(!!process.env.API_KEY);
      }
    };
    checkApiKey();
  }, []);

  const handleConnectApiKey = async () => {
    if ((window as any).aistudio) {
      try {
        await (window as any).aistudio.openSelectKey();
        setHasApiKey(true);
      } catch (e) {
        console.error("Failed to select key", e);
      }
    }
  };

  const handleSelectVideo = async (video: VideoData) => {
    setActiveVideoId(video.id);
    setMessages([]);
    setProcessingState(ProcessingState.COMPLETED);
    initChat(video);

    if (window.innerWidth < 768) {
      setLeftSidebarOpen(false);
    }
  };

  const initChat = async (video: VideoData) => {
    try {
      const sessionId = await createChatSession(video.id);
      setChatSessionId(sessionId);
      console.log("Chat session created:", sessionId);
    } catch (error) {
      console.error("Failed to create chat session:", error);
    }
  };

  const handleAddVideo = async (url: string) => {
    if (!url.trim()) return;

    setProcessingState(ProcessingState.PROCESSING);

    try {
      const analysis = await analyzeVideo(url);

      setVideos((prev) => [analysis, ...prev]);
      setActiveVideoId(analysis.id);

      await initChat(analysis);
      setProcessingState(ProcessingState.COMPLETED);
      setUrlInput("");
    } catch (error) {
      console.error("Error adding video:", error);
      setProcessingState(ProcessingState.ERROR);
      setActiveVideoId(null);
      alert(`Failed to analyze video. ${(error as Error).message}`);
    }
  };

  const handleLandingSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleAddVideo(urlInput);
  };

  const handleSendMessage = async (text: string) => {
    if (!chatSessionId) {
      console.error("No chat session");
      return;
    }

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: text,
      timestamp: Date.now(),
    };
    setMessages((prev) => [...prev, userMsg]);

    const aiMsgId = (Date.now() + 1).toString();
    const aiPlaceholder: Message = {
      id: aiMsgId,
      role: "model",
      content: "",
      timestamp: Date.now(),
      isStreaming: true,
    };
    setMessages((prev) => [...prev, aiPlaceholder]);

    try {
      const response = await sendChatMessage(chatSessionId, text);
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === aiMsgId
            ? { ...msg, content: response, isStreaming: false }
            : msg,
        ),
      );
    } catch (error) {
      console.error("Chat error:", error);
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === aiMsgId
            ? {
                ...msg,
                content: "Error processing request.",
                isStreaming: false,
              }
            : msg,
        ),
      );
    }
  };

  const copyToClipboard = () => {
    if (!activeVideo) return;
    const text = `
# ${activeVideo.title}
## Executive Summary
${activeVideo.executiveSummary}

## Key Terms
${activeVideo.keyTerms?.join(", ")}

## Detailed Notes
${activeVideo.detailedNotes?.map((n) => `### ${n.timestamp ? `[${n.timestamp}] ` : ""}${n.topic}\n${n.content}`).join("\n\n")}
      `;
    navigator.clipboard.writeText(text);
    alert("Notes copied to clipboard!");
  };

  // Timestamp seeking logic
  const handleTimestampClick = (timestamp: string) => {
    if (!player || !timestamp) return;

    const parts = timestamp.split(":").map(Number);
    let seconds = 0;
    if (parts.length === 3) {
      seconds = parts[0] * 3600 + parts[1] * 60 + parts[2];
    } else if (parts.length === 2) {
      seconds = parts[0] * 60 + parts[1];
    } else {
      seconds = parts[0];
    }

    if (typeof player.seekTo === "function") {
      player.seekTo(seconds, true);
      player.playVideo();
    }
  };

  const activeVideo = videos.find((v) => v.id === activeVideoId) || null;

  if (loading) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-black text-white">
        <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <>
      <LoginModal isOpen={showLogin} onClose={() => setShowLogin(false)} />
      <div
        className="moving-background"
        style={{
          backgroundImage: `url('https://images.unsplash.com/photo-1620641788421-7a1c3103428f?q=80&w=2560&auto=format&fit=crop')`,
        }}
      />
      <div className="fixed inset-0 z-[-1] bg-black/60 backdrop-blur-[40px]" />

      <div className="flex h-screen w-full relative overflow-hidden font-sans text-slate-200 selection:bg-blue-500/30">
        <SidebarLeft
          videos={videos}
          activeVideoId={activeVideoId}
          onSelectVideo={handleSelectVideo}
          onAddNew={() => setIsModalOpen(true)}
          isOpen={leftSidebarOpen}
          setIsOpen={setLeftSidebarOpen}
        />

        <main className="flex-1 flex flex-col relative overflow-hidden transition-all duration-300">
          {/* Global Menu Trigger */}
          <div
            className={`absolute top-4 left-4 z-50 ${leftSidebarOpen ? "md:hidden" : "block"}`}
          >
            <button
              onClick={() => setLeftSidebarOpen(!leftSidebarOpen)}
              className="p-2 bg-black/40 hover:bg-white/10 rounded-lg text-white backdrop-blur-md border border-white/5 transition-colors shadow-lg"
              title={leftSidebarOpen ? "Close Menu" : "Open Menu"}
            >
              <Menu size={20} />
            </button>
          </div>

          <AnimatePresence mode="wait">
            {!activeVideo ? (
              <motion.div
                key="hero"
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 1.05, filter: "blur(10px)" }}
                transition={{ duration: 0.5 }}
                className="flex-1 flex flex-col items-center justify-center p-6 relative z-10"
              >
                <div className="w-full max-w-4xl text-center">
                  <motion.div
                    initial={{ y: 20, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    transition={{ delay: 0.2 }}
                    className="inline-flex items-center justify-center gap-2 mb-8 bg-white/5 border border-white/10 px-4 py-1.5 rounded-full backdrop-blur-md"
                  >
                    <Sparkles size={14} className="text-blue-400" />
                    <span className="text-xs font-medium tracking-widest uppercase text-blue-100/80">
                      Gemini 3 Flash
                    </span>
                  </motion.div>

                  <motion.h1
                    initial={{ y: 20, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    transition={{ delay: 0.3 }}
                    className="text-6xl md:text-8xl font-black text-white tracking-tighter mb-6 leading-[0.9]"
                  >
                    Study{" "}
                    <span className="text-transparent bg-clip-text bg-gradient-to-br from-blue-300 to-purple-400">
                      Architect.
                    </span>
                  </motion.h1>

                  <motion.form
                    initial={{ y: 20, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    transition={{ delay: 0.5 }}
                    onSubmit={handleLandingSubmit}
                    className="relative max-w-2xl mx-auto group"
                  >
                    <div className="absolute inset-0 bg-gradient-to-r from-blue-500/20 via-purple-500/20 to-blue-500/20 rounded-2xl blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-700" />
                    <div className="relative flex items-center bg-white/5 border border-white/10 rounded-2xl p-2 pl-6 shadow-2xl backdrop-blur-xl transition-all hover:bg-white/10 hover:border-white/20">
                      <Link className="text-slate-500 mr-4" size={20} />
                      <input
                        type="url"
                        value={urlInput}
                        onChange={(e) => setUrlInput(e.target.value)}
                        placeholder="Paste YouTube URL..."
                        className="flex-1 bg-transparent border-none outline-none text-white placeholder-slate-500 h-12 text-lg font-light"
                        required
                      />
                      <button
                        type="submit"
                        disabled={
                          processingState === ProcessingState.PROCESSING
                        }
                        className="bg-white text-black h-12 w-12 rounded-xl flex items-center justify-center hover:bg-blue-50 transition-colors shadow-lg disabled:opacity-50"
                      >
                        {processingState === ProcessingState.PROCESSING ? (
                          <div className="w-5 h-5 border-2 border-slate-900 border-t-transparent rounded-full animate-spin" />
                        ) : (
                          <ChevronRight size={24} />
                        )}
                      </button>
                    </div>
                    {/* Status Text under input */}
                    {processingState === ProcessingState.PROCESSING && (
                      <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="absolute left-0 right-0 top-full mt-4 text-sm text-blue-300/80 font-medium tracking-wide"
                      >
                        Analyzing video with AI...
                      </motion.div>
                    )}
                  </motion.form>
                </div>
              </motion.div>
            ) : (
              <motion.div
                key="dashboard"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.8 }}
                className="flex-1 flex flex-col lg:flex-row h-full w-full p-4 lg:p-6 gap-6 pt-16 lg:pt-6"
              >
                {/* Context Panel (LEFT: Video + Notes) */}
                <div className="w-full lg:w-[480px] shrink-0 flex flex-col gap-6 overflow-y-auto custom-scrollbar lg:pr-2 pb-10 lg:pb-0">
                  {/* YouTube Player */}
                  <div className="aspect-video w-full shrink-0">
                    <YouTubePlayer
                      videoId={activeVideo.id}
                      setPlayerRef={setPlayer}
                    />
                  </div>

                  {/* Video Info */}
                  <div className="px-1">
                    <h2 className="text-lg font-bold text-white leading-tight mb-2">
                      {activeVideo.title}
                    </h2>

                    {/* Guest Preview Banner */}
                    {activeVideo.is_guest_preview && (
                      <div className="mb-4 bg-gradient-to-r from-blue-900/40 to-purple-900/40 border border-blue-500/30 rounded-xl p-3 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Sparkles size={16} className="text-yellow-400" />
                          <div className="text-xs">
                            <span className="font-bold text-white">
                              Guest Preview (30%)
                            </span>
                            <p className="text-blue-200/70">
                              Sign in to unlock full analysis & chat.
                            </p>
                          </div>
                        </div>
                        <button
                          onClick={() => setShowLogin(true)}
                          className="bg-white text-black text-xs font-bold px-3 py-1.5 rounded-lg hover:bg-blue-50 transition-colors"
                        >
                          Unlock Full
                        </button>
                      </div>
                    )}

                    <div className="flex justify-between items-center">
                      <div className="flex items-center gap-3 text-xs font-medium text-slate-400">
                        <span className="flex items-center gap-1.5">
                          <Clock size={12} /> {activeVideo.dateAdded}
                        </span>
                      </div>
                      <button
                        onClick={copyToClipboard}
                        className="text-xs bg-white/10 hover:bg-white/20 text-blue-200 px-2 py-1 rounded border border-white/10 transition-colors"
                      >
                        Copy Notes
                      </button>
                    </div>
                  </div>

                  {/* Executive Summary */}
                  <div className="bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur-md shrink-0">
                    <div className="flex items-center gap-2 mb-3 text-emerald-300 font-bold uppercase text-xs tracking-wider">
                      <Sparkles size={14} />
                      <span>Summary</span>
                    </div>
                    <div className="text-sm text-slate-300 leading-relaxed font-light">
                      {activeVideo.executiveSummary || activeVideo.summary}
                    </div>
                  </div>

                  {/* Detailed Notes (Timestamped) */}
                  {activeVideo.detailedNotes &&
                    activeVideo.detailedNotes.length > 0 && (
                      <div className="bg-white/5 border border-white/10 rounded-2xl p-6 backdrop-blur-md flex-1">
                        <div className="flex items-center gap-2 mb-4 text-blue-300 font-bold uppercase text-xs tracking-wider">
                          <FileText size={14} />
                          <span>Timestamped Notes</span>
                        </div>
                        <div className="space-y-6">
                          {activeVideo.detailedNotes.map((note, i) => (
                            <div
                              key={i}
                              className="group relative pl-4 border-l border-white/10 hover:border-blue-500/50 transition-colors"
                            >
                              <div className="absolute -left-[5px] top-0 w-2.5 h-2.5 rounded-full bg-slate-800 border border-slate-600 group-hover:bg-blue-500 group-hover:border-blue-400 transition-colors" />
                              <div className="flex items-center gap-2 mb-1 flex-wrap">
                                {note.timestamp && (
                                  <button
                                    onClick={() =>
                                      handleTimestampClick(note.timestamp!)
                                    }
                                    className="text-[10px] font-mono font-bold bg-blue-500/20 text-blue-300 hover:bg-blue-500 hover:text-white px-2 py-0.5 rounded border border-blue-500/30 transition-all cursor-pointer"
                                  >
                                    {note.timestamp}
                                  </button>
                                )}
                                <h4 className="text-sm font-semibold text-white group-hover:text-blue-200 transition-colors">
                                  {note.topic}
                                </h4>
                              </div>
                              <p className="text-sm text-slate-400 font-light leading-relaxed">
                                {note.content}
                              </p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                </div>

                {/* Chat Area (RIGHT) */}
                <div className="flex-1 bg-white/5 border border-white/10 rounded-3xl backdrop-blur-xl shadow-2xl overflow-hidden flex flex-col min-h-[500px]">
                  <ChatArea
                    messages={messages}
                    processingState={processingState}
                    onSendMessage={handleSendMessage}
                    videoTitle={activeVideo.title}
                  />
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </main>

        <NewVideoModal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          onSubmit={handleAddVideo}
        />
      </div>
    </>
  );
};

export default App;
