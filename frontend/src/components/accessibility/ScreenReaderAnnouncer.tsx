import { useEffect, useRef } from 'react';

interface ScreenReaderAnnouncerProps {
  message: string;
  priority?: 'polite' | 'assertive';
  clearAfter?: number;
}

export default function ScreenReaderAnnouncer({ 
  message, 
  priority = 'polite', 
  clearAfter = 3000 
}: ScreenReaderAnnouncerProps) {
  const announcerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (message && announcerRef.current) {
      announcerRef.current.textContent = message;
      
      if (clearAfter > 0) {
        const timer = setTimeout(() => {
          if (announcerRef.current) {
            announcerRef.current.textContent = '';
          }
        }, clearAfter);
        
        return () => clearTimeout(timer);
      }
    }
  }, [message, clearAfter]);

  return (
    <div
      ref={announcerRef}
      aria-live={priority}
      aria-atomic="true"
      className="sr-only"
      role="status"
    />
  );
}