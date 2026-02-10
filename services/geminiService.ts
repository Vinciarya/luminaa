import { GoogleGenAI, Chat, GenerateContentResponse } from "@google/genai";
import { Message } from "../types";

const getAIClient = () => {
  const apiKey = process.env.API_KEY;
  if (!apiKey) {
    throw new Error("API Key is missing. Please select one.");
  }
  return new GoogleGenAI({ apiKey });
};

export const extractYoutubeId = (url: string): string | null => {
    const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/;
    const match = url.match(regExp);
    return (match && match[2].length === 11) ? match[2] : null;
};

// Robust Retry Wrapper with stronger backoff for Quota limits
async function generateWithRetry(
    fn: () => Promise<GenerateContentResponse>, 
    retries = 4, 
    baseDelay = 5000 
): Promise<GenerateContentResponse> {
    for (let i = 0; i < retries; i++) {
        try {
            return await fn();
        } catch (error: any) {
            // Check for rate limit (429) or temporary server errors (503)
            const isRateLimit = error.status === 429 || error.status === 503 || (error.message && error.message.includes("429"));
            
            if (isRateLimit && i < retries - 1) {
                const delay = baseDelay * Math.pow(2, i); // 5s, 10s, 20s, 40s
                console.warn(`Hit rate limit. Retrying in ${delay/1000}s... (Attempt ${i + 1}/${retries})`);
                await new Promise(resolve => setTimeout(resolve, delay));
                continue;
            }
            throw error;
        }
    }
    throw new Error("Max retries exceeded");
}

export const analyzeVideo = async (url: string): Promise<any> => {
  try {
    const ai = getAIClient();
    
    // Architect Prompt: Best-Effort Analysis
    // Changed strategy to avoid hard failures. 
    // 1. Prioritize Transcript via Search.
    // 2. Fallback to Metadata/Description analysis if transcript is missing.
    // 3. No longer returns explicit "error" JSON unless the video is completely nonexistent.
    const prompt = `
      Role: Advanced Video Content Analyzer.
      Task: Analyze this YouTube video URL: ${url}
      
      OBJECTIVE: Generate a structured study guide for this video.
      
      INSTRUCTIONS:
      1. Use 'googleSearch' to find the **transcript**, **captions**, or **detailed summary** of this video.
      2. If you find a direct transcript/captions, extract key points with timestamps (MM:SS).
      3. **FALLBACK:** If NO direct transcript is found, search for the video title/topic and generate a high-quality summary based on the available metadata, reviews, or articles. 
         - In this case, set timestamps to null or "00:00".
         - Explicitly mention in the summary that this is an AI-generated overview based on available metadata.
      
      OUTPUT FORMAT (JSON ONLY):
      {
        "title": "Video Title",
        "executiveSummary": "Concise summary (3-5 sentences).",
        "keyTerms": ["Term 1", "Term 2"],
        "detailedNotes": [
          { 
            "timestamp": "MM:SS (e.g. 02:15) or null", 
            "topic": "Topic Header", 
            "content": "Detailed point." 
          }
        ]
      }
      
      IMPORTANT: Do NOT return an error message like "Content not found". Always provide the best possible analysis based on whatever information you can gather from Google Search.
    `;

    // Using gemini-3-flash-preview for speed and search capability
    const response = await generateWithRetry(() => 
        ai.models.generateContent({
            model: 'gemini-3-flash-preview',
            contents: prompt,
            config: {
                tools: [{ googleSearch: {} }],
            }
        })
    );

    const text = response.text;
    if (!text) throw new Error("No response from AI");
    
    // Robust JSON extraction
    const firstBrace = text.indexOf('{');
    const lastBrace = text.lastIndexOf('}');
    
    if (firstBrace === -1 || lastBrace === -1) {
        // Fallback if model just returns text (rare with JSON instruction but possible)
        console.warn("AI response was not pure JSON, attempting to parse whole text or fail gracefully.");
        throw new Error("AI did not return a valid JSON object");
    }

    const cleanText = text.substring(firstBrace, lastBrace + 1);
    const data = JSON.parse(cleanText);

    if (data.error) {
        // Should not happen with new prompt, but safety check
        throw new Error(data.error);
    }

    return {
        title: data.title || "Video Analysis",
        summary: data.executiveSummary, 
        executiveSummary: data.executiveSummary,
        keyTerms: data.keyTerms || [],
        detailedNotes: data.detailedNotes || [],
        takeaways: data.detailedNotes?.map((n: any) => 
            `${n.timestamp ? `[${n.timestamp}] ` : ''}**${n.topic}**: ${n.content}`
        ) || []
    };

  } catch (error: any) {
    console.error("Error analyzing video:", error);
    return {
      title: "Analysis Failed",
      summary: `## Unable to Process\n\n${error.message || "Unknown error"}. \n\nThe AI could not retrieve information for this video. It might be private, very new, or age-restricted.`,
      executiveSummary: "Analysis unavailable.",
      keyTerms: [],
      detailedNotes: []
    };
  }
};

export const createChatSession = (systemInstruction: string) => {
    const ai = getAIClient();
    return ai.chats.create({
        model: 'gemini-3-flash-preview', 
        config: {
            systemInstruction
        }
    });
};

export const sendMessageStream = async (chat: Chat, message: string) => {
    return await chat.sendMessageStream({ message });
};

export const transcribeAudio = async (base64Audio: string, mimeType = 'audio/webm'): Promise<string> => {
    const ai = getAIClient();
    try {
        const response = await ai.models.generateContent({
            model: 'gemini-2.5-flash-native-audio-preview-12-2025',
            contents: {
                parts: [
                    {
                        inlineData: {
                            mimeType: mimeType,
                            data: base64Audio
                        }
                    },
                    { text: "Transcribe the spoken audio into text. Return ONLY the transcribed text, no additional commentary." }
                ]
            }
        });
        return response.text || "";
    } catch (error) {
        console.error("Transcription error:", error);
        throw error;
    }
};