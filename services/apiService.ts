/**
 * API Service for Frontend
 * Replaces direct Gemini API calls with FastAPI backend calls
 */

import { auth } from "./firebase";

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const getHeaders = async () => {
  const token = await auth.currentUser?.getIdToken();
  return {
    'Content-Type': 'application/json',
    'Authorization': token ? `Bearer ${token}` : ''
  };
};

export interface VideoData {
  id: string;
  title: string;
  url: string;
  thumbnail: string;
  dateAdded: string;
  executiveSummary: string;
  summary: string;
  keyTerms: string[];
  detailedNotes: Array<{
    timestamp?: string;
    topic: string;
    content: string;
  }>;
  processed: boolean;
  cached?: boolean;
}

export interface ChatSession {
  session_id: string;
  message: string;
}

export interface ChatMessage {
  response: string;
  session_id: string;
}

export interface StatsData {
  cache: {
    total_videos: number;
    popular_videos: number;
    total_views: number;
    cache_enabled: boolean;
  };
  api_keys: Record<string, {
    requests_last_minute: number;
    requests_today: number;
    rpm_remaining: number;
    rpd_remaining: number;
  }>;
  total_capacity: {
    rpm: number;
    rpd: number;
  };
}

/**
 * Extract YouTube video ID from URL
 */
export const extractYoutubeId = (url: string): string | null => {
  const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/;
  const match = url.match(regExp);
  return (match && match[2].length === 11) ? match[2] : null;
};

/**
 * Analyze YouTube video
 * 
 * @param url - YouTube video URL
 * @returns Video analysis data
 */
export const analyzeVideo = async (url: string): Promise<VideoData> => {
  const headers = await getHeaders();
  const response = await fetch(`${API_BASE_URL}/api/videos/analyze`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ url }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to analyze video');
  }

  const data = await response.json();
  
  return {
    id: data.video_id,
    title: data.title,
    url: data.url,
    thumbnail: data.thumbnail,
    dateAdded: data.dateAdded,
    executiveSummary: data.executiveSummary,
    summary: data.summary,
    keyTerms: data.keyTerms,
    detailedNotes: data.detailedNotes,
    processed: data.processed,
    cached: data.cached,
  };
};

/**
 * Get cached video data
 * 
 * @param videoId - YouTube video ID
 * @returns Video data if cached
 */
export const getVideo = async (videoId: string): Promise<VideoData> => {
  const headers = await getHeaders();
  const response = await fetch(`${API_BASE_URL}/api/videos/${videoId}`, {
    headers
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Video not found');
  }

  const data = await response.json();
  
  return {
    id: data.video_id,
    title: data.title,
    url: data.url,
    thumbnail: data.thumbnail,
    dateAdded: data.dateAdded,
    executiveSummary: data.executiveSummary,
    summary: data.summary,
    keyTerms: data.keyTerms,
    detailedNotes: data.detailedNotes,
    processed: data.processed,
    cached: data.cached,
  };
};

/**
 * Create chat session for a video
 * 
 * @param videoId - YouTube video ID
 * @returns Session ID
 */
export const createChatSession = async (videoId: string): Promise<string> => {
  const headers = await getHeaders();
  const response = await fetch(`${API_BASE_URL}/api/chat/create`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ video_id: videoId }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create chat session');
  }

  const data: ChatSession = await response.json();
  return data.session_id;
};

/**
 * Send message to chat session
 * 
 * @param sessionId - Chat session ID
 * @param message - User message
 * @returns AI response
 */
export const sendChatMessage = async (
  sessionId: string,
  message: string
): Promise<string> => {
  const headers = await getHeaders();
  const response = await fetch(`${API_BASE_URL}/api/chat/message`, {
    method: 'POST',
    headers,
    body: JSON.stringify({
      session_id: sessionId,
      message,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to send message');
  }

  const data: ChatMessage = await response.json();
  return data.response;
};

/**
 * Get usage statistics
 * 
 * @returns Usage stats and cost estimates
 */
export const getStats = async (): Promise<StatsData> => {
  const response = await fetch(`${API_BASE_URL}/api/stats`);

  if (!response.ok) {
    throw new Error('Failed to fetch statistics');
  }

  return response.json();
};

/**
 * Health check
 * 
 * @returns Health status
 */
export const healthCheck = async (): Promise<{
  status: string;
  redis: string;
  api_keys: number;
  environment: string;
}> => {
  const response = await fetch(`${API_BASE_URL}/health`);

  if (!response.ok) {
    throw new Error('Backend is not healthy');
  }

  return response.json();
};
