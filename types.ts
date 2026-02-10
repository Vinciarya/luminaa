export interface DetailedNote {
  timestamp?: string;
  topic: string;
  content: string;
}

export interface VideoData {
  id: string;
  title: string;
  url: string;
  thumbnail: string;
  dateAdded: string;
  
  // Educational Architect Fields
  executiveSummary?: string;
  keyTerms?: string[];
  detailedNotes?: DetailedNote[];
  
  // Legacy/Fallback
  summary?: string; 
  keyTakeaways?: string[];
  
  processed: boolean;
  is_guest_preview?: boolean;
}

export interface Message {
  id: string;
  role: 'user' | 'model';
  content: string;
  timestamp: number;
  isStreaming?: boolean;
}

export enum ProcessingState {
  IDLE = 'IDLE',
  PROCESSING = 'PROCESSING',
  COMPLETED = 'COMPLETED',
  ERROR = 'ERROR'
}

export interface ChatSession {
  videoId: string;
  messages: Message[];
}