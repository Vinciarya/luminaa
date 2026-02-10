import React, { useEffect, useRef } from 'react';

declare global {
  interface Window {
    YT: any;
    onYouTubeIframeAPIReady: () => void;
  }
}

interface YouTubePlayerProps {
  videoId: string;
  setPlayerRef: (player: any) => void;
}

export const YouTubePlayer: React.FC<YouTubePlayerProps> = ({ videoId, setPlayerRef }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const playerInstanceRef = useRef<any>(null);

  useEffect(() => {
    const initPlayer = () => {
       if (!containerRef.current) return;
       
       // Avoid double initialization
       if (playerInstanceRef.current) {
           if (typeof playerInstanceRef.current.cueVideoById === 'function') {
               playerInstanceRef.current.cueVideoById(videoId);
           }
           return;
       }

       playerInstanceRef.current = new window.YT.Player(containerRef.current, {
          height: '100%',
          width: '100%',
          videoId: videoId,
          playerVars: {
             modestbranding: 1,
             rel: 0,
             playsinline: 1
          },
          events: {
             onReady: (e: any) => {
                 setPlayerRef(e.target);
             }
          }
       });
    };

    if (!window.YT) {
      const tag = document.createElement('script');
      tag.src = "https://www.youtube.com/iframe_api";
      const firstScriptTag = document.getElementsByTagName('script')[0];
      firstScriptTag.parentNode?.insertBefore(tag, firstScriptTag);
      window.onYouTubeIframeAPIReady = initPlayer;
    } else {
      initPlayer();
    }
  }, []);

  // Handle video ID changes
  useEffect(() => {
      if (playerInstanceRef.current && typeof playerInstanceRef.current.loadVideoById === 'function') {
          playerInstanceRef.current.loadVideoById(videoId);
      }
  }, [videoId]);

  return (
    <div className="relative w-full h-full bg-black rounded-2xl overflow-hidden shadow-2xl border border-white/10">
        <div ref={containerRef} className="absolute inset-0 w-full h-full" />
    </div>
  );
};