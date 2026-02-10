import React from 'react';
import { motion } from 'framer-motion';
import { Message } from '../types';
import ReactMarkdown from 'react-markdown';
import { Bot, Youtube } from './ui/Icons';

interface ChatBubbleProps {
  message: Message;
}

export const ChatBubble: React.FC<ChatBubbleProps> = ({ message }) => {
  const isAi = message.role === 'model';

  return (
    <motion.div
      initial={{ opacity: 0, y: 10, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.3, ease: "easeOut" }}
      className={`flex w-full ${isAi ? 'justify-start' : 'justify-end'} mb-6`}
    >
      <div className={`flex max-w-[85%] md:max-w-[75%] gap-3 ${isAi ? 'flex-row' : 'flex-row-reverse'}`}>
        
        {/* Avatar */}
        <div className={`
          shrink-0 w-8 h-8 rounded-lg flex items-center justify-center border
          ${isAi 
            ? 'bg-indigo-500/10 border-indigo-500/20 text-indigo-400' 
            : 'bg-slate-700/50 border-slate-600/50 text-slate-300'}
        `}>
          {isAi ? <Bot size={18} /> : <span className="text-xs font-bold">ME</span>}
        </div>

        {/* Message Content */}
        <div className={`
          relative px-5 py-3.5 rounded-2xl text-sm leading-relaxed shadow-sm
          ${isAi 
            ? 'bg-white/5 border border-white/10 text-slate-200 rounded-tl-none' 
            : 'bg-blue-600 text-white rounded-tr-none shadow-blue-900/20'}
        `}>
          {isAi ? (
            <div className="prose prose-invert prose-sm max-w-none prose-p:my-1 prose-pre:bg-slate-900/50 prose-pre:border prose-pre:border-white/10">
              <ReactMarkdown>{message.content}</ReactMarkdown>
              {message.isStreaming && <span className="inline-block w-1.5 h-3 ml-1 bg-indigo-400 animate-pulse" />}
            </div>
          ) : (
            <div>{message.content}</div>
          )}
        </div>
      </div>
    </motion.div>
  );
};