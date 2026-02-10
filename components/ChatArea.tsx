import React, { useRef, useEffect, useState } from 'react';
import { Message, ProcessingState } from '../types';
import { ChatBubble } from './ChatBubble';
import { Send, Sparkles, Mic, Loader2 } from './ui/Icons';
import { motion, AnimatePresence } from 'framer-motion';
import { transcribeAudio } from '../services/geminiService';

interface ChatAreaProps {
  messages: Message[];
  processingState: ProcessingState;
  onSendMessage: (text: string) => void;
  videoTitle?: string;
}

export const ChatArea: React.FC<ChatAreaProps> = ({ 
  messages, 
  processingState, 
  onSendMessage,
  videoTitle
}) => {
  const [input, setInput] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Focus input when video changes
  useEffect(() => {
      if (processingState === ProcessingState.COMPLETED) {
          inputRef.current?.focus();
      }
  }, [processingState, videoTitle]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || processingState !== ProcessingState.COMPLETED) return;
    onSendMessage(input);
    setInput('');
  };

  // --- Audio Recording Logic ---
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        // Stop all tracks to release mic
        stream.getTracks().forEach(track => track.stop());
        await handleTranscription(audioBlob);
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error("Error accessing microphone:", error);
      alert("Could not access microphone. Please ensure permissions are granted.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const toggleRecording = () => {
    if (isRecording) {
        stopRecording();
    } else {
        startRecording();
    }
  };

  const handleTranscription = async (audioBlob: Blob) => {
      setIsTranscribing(true);
      try {
          const base64Audio = await blobToBase64(audioBlob);
          const text = await transcribeAudio(base64Audio);
          if (text) {
              setInput(prev => prev + (prev ? " " : "") + text);
          }
      } catch (e) {
          console.error("Transcription failed", e);
          alert("Failed to transcribe audio.");
      } finally {
          setIsTranscribing(false);
          // Focus input after transcription
          setTimeout(() => inputRef.current?.focus(), 100);
      }
  };

  const blobToBase64 = (blob: Blob): Promise<string> => {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => {
            const result = reader.result as string;
            // Remove data url prefix (e.g. "data:audio/webm;base64,")
            const base64 = result.split(',')[1];
            resolve(base64);
        };
        reader.onerror = reject;
        reader.readAsDataURL(blob);
    });
  };
  // -----------------------------

  const isProcessing = processingState === ProcessingState.PROCESSING;

  return (
    <div className="flex-1 flex flex-col h-full relative overflow-hidden bg-transparent">
      
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-4 md:px-8 py-6 custom-scrollbar scroll-smooth">
        {messages.length === 0 && processingState === ProcessingState.COMPLETED && (
            <div className="h-full flex flex-col items-center justify-center text-slate-400 opacity-60">
                <div className="bg-white/5 p-4 rounded-3xl mb-4 backdrop-blur-sm border border-white/5">
                    <Sparkles size={24} className="text-white" />
                </div>
                <p className="text-sm font-light">Start the conversation</p>
            </div>
        )}
        
        <div className="space-y-6 pt-4">
            {messages.map((msg) => (
            <ChatBubble key={msg.id} message={msg} />
            ))}
            <div ref={messagesEndRef} className="h-4" />
        </div>
      </div>

      {/* Processing Indicator Overlay */}
      <AnimatePresence>
        {isProcessing && (
            <motion.div 
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="absolute inset-0 z-20 bg-black/20 backdrop-blur-sm flex items-center justify-center"
            >
                <div className="flex items-center gap-3 bg-black/60 px-6 py-3 rounded-full border border-white/10 text-white shadow-xl">
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" />
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce delay-100" />
                    <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce delay-200" />
                    <span className="text-sm font-medium ml-2">Thinking...</span>
                </div>
            </motion.div>
        )}
      </AnimatePresence>

      {/* Input Area */}
      <div className="p-4 md:p-6 bg-gradient-to-t from-black/20 to-transparent">
        <form onSubmit={handleSubmit} className="relative max-w-4xl mx-auto">
            <div className={`
                relative flex items-center gap-2 bg-[#1e1e1e]/80 border rounded-2xl p-2 pl-4 shadow-lg backdrop-blur-xl transition-all 
                ${isRecording ? 'border-red-500/50 shadow-red-900/20' : 'border-white/10 hover:bg-[#1e1e1e] hover:border-white/20'}
                focus-within:ring-1 focus-within:ring-white/20
            `}>
                <input
                    ref={inputRef}
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder={isRecording ? "Listening..." : "Ask a follow-up..."}
                    disabled={processingState !== ProcessingState.COMPLETED || isRecording || isTranscribing}
                    className="flex-1 bg-transparent border-none focus:ring-0 text-white placeholder:text-slate-500 px-2 py-3 text-sm font-light disabled:opacity-50"
                />
                
                {/* Microphone Button */}
                <button
                    type="button"
                    onClick={toggleRecording}
                    disabled={processingState !== ProcessingState.COMPLETED || isTranscribing}
                    className={`
                        p-2.5 rounded-xl transition-all shadow-md active:scale-95
                        ${isRecording 
                            ? 'bg-red-500/20 text-red-400 animate-pulse' 
                            : 'hover:bg-white/10 text-slate-400 hover:text-white'}
                        disabled:opacity-30
                    `}
                    title={isRecording ? "Stop Recording" : "Dictate with Voice"}
                >
                    {isTranscribing ? (
                        <Loader2 size={18} className="animate-spin text-blue-400" />
                    ) : (
                        <Mic size={18} />
                    )}
                </button>

                {/* Send Button */}
                <button
                    type="submit"
                    disabled={!input.trim() || processingState !== ProcessingState.COMPLETED || isRecording || isTranscribing}
                    className="p-2.5 rounded-xl bg-white text-black hover:bg-slate-200 disabled:opacity-30 disabled:bg-white disabled:text-black transition-all shadow-md active:scale-95"
                >
                    <Send size={16} />
                </button>
            </div>
            {isRecording && (
                <motion.div 
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="absolute -top-8 left-0 right-0 text-center"
                >
                    <span className="text-xs font-bold text-red-400 tracking-wider bg-black/60 px-3 py-1 rounded-full border border-red-500/20 backdrop-blur-sm">
                        RECORDING
                    </span>
                </motion.div>
            )}
        </form>
      </div>
    </div>
  );
};