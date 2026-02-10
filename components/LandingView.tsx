import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Youtube, Sparkles, ChevronRight, Link } from './ui/Icons';

interface LandingViewProps {
  onUrlSubmit: (url: string) => void;
  isProcessing: boolean;
}

export const LandingView: React.FC<LandingViewProps> = ({ onUrlSubmit, isProcessing }) => {
  const [url, setUrl] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (url.trim()) {
      onUrlSubmit(url);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center h-full w-full px-6 relative z-10 text-center">
      
      <motion.div 
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.8, ease: "easeOut" }}
        className="w-full max-w-[90vw] mx-auto"
      >
        {/* Badge */}
        <motion.div 
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.8 }}
            className="inline-flex items-center justify-center gap-3 mb-[2vh]"
        >
            <div className="bg-white/10 p-2.5 rounded-full backdrop-blur-xl border border-white/20 shadow-[0_0_20px_rgba(147,197,253,0.3)]">
                <Sparkles className="text-blue-200" size={22} />
            </div>
            <span className="text-sm md:text-base font-bold tracking-[0.2em] text-blue-100 uppercase drop-shadow-[0_2px_10px_rgba(0,0,0,0.5)]">
                AI Knowledge Engine
            </span>
        </motion.div>

        {/* Massive Headline using VW for adjustment */}
        <h1 className="font-black text-white mb-[3vh] tracking-tighter leading-[0.9] drop-shadow-2xl" style={{ fontSize: '11vw' }}>
            Unlock the <br className="hidden md:block" />
            <span className="text-transparent bg-clip-text bg-gradient-to-b from-white via-blue-100 to-blue-300">
                knowledge inside.
            </span>
        </h1>

        {/* Subtext */}
        <p className="text-slate-100 mb-[6vh] max-w-4xl mx-auto leading-relaxed font-light drop-shadow-lg text-shadow-sm" style={{ fontSize: 'clamp(1rem, 1.5vw, 2rem)' }}>
            Paste a YouTube link. Get instant insights, summaries, and answers powered by next-gen AI.
        </p>

        {/* Input Form */}
        <form onSubmit={handleSubmit} className="relative max-w-3xl mx-auto group w-full">
            {/* Input Container */}
            <div className="relative flex items-center bg-black/30 border border-white/30 backdrop-blur-2xl rounded-full p-2 pl-6 md:pl-8 transition-all duration-300 focus-within:bg-black/50 focus-within:border-white/60 focus-within:shadow-[0_0_40px_rgba(59,130,246,0.4)]">
                <Link className="text-white/70 mr-3 md:mr-4 shrink-0" size={24} />
                <input 
                    type="url" 
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    placeholder="Paste YouTube URL here..."
                    className="flex-1 bg-transparent border-none outline-none text-white placeholder-white/50 font-light h-12 md:h-14 min-w-0"
                    style={{ fontSize: 'clamp(1rem, 1.2vw, 1.5rem)' }}
                    required
                />
                <button 
                    type="submit"
                    disabled={isProcessing}
                    className="bg-white hover:bg-blue-50 text-black transition-all duration-300 rounded-full w-12 h-12 md:w-16 md:h-16 ml-3 shrink-0 flex items-center justify-center disabled:opacity-70 shadow-lg hover:scale-105 active:scale-95"
                >
                    {isProcessing ? (
                        <div className="w-5 h-5 md:w-6 md:h-6 border-[3px] border-slate-900 border-t-transparent rounded-full animate-spin" />
                    ) : (
                        <ChevronRight className="w-6 h-6 md:w-8 md:h-8" strokeWidth={2.5} />
                    )}
                </button>
            </div>
        </form>

        {/* Footer Info */}
        <div className="mt-[6vh] flex flex-wrap items-center justify-center gap-4 md:gap-12 text-white/90 font-medium tracking-wide drop-shadow-md" style={{ fontSize: 'clamp(0.8rem, 1vw, 1.1rem)' }}>
            <span className="flex items-center gap-3 bg-black/20 px-4 py-2 rounded-full backdrop-blur-sm border border-white/5">
                <div className="w-2 md:w-2.5 h-2 md:h-2.5 rounded-full bg-green-400 shadow-[0_0_12px_rgba(74,222,128,0.8)] animate-pulse"></div>
                Gemini 3 Flash
            </span>
            <span className="flex items-center gap-3 bg-black/20 px-4 py-2 rounded-full backdrop-blur-sm border border-white/5">
                <div className="w-2 md:w-2.5 h-2 md:h-2.5 rounded-full bg-blue-400 shadow-[0_0_12px_rgba(96,165,250,0.8)] animate-pulse"></div>
                Real-time Analysis
            </span>
        </div>

      </motion.div>
    </div>
  );
};