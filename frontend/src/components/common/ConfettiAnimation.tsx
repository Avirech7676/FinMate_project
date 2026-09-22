import { motion } from 'framer-motion';
import { useEffect, useState } from 'react';

interface ConfettiPiece {
  id: number;
  x: number;
  y: number;
  color: string;
  rotation: number;
  size: number;
  duration: number;
  swayAmount: number;
}

interface ConfettiAnimationProps {
  trigger: boolean;
  onComplete?: () => void;
}

const colors = ['#00D4AA', '#4F8FE8', '#A78BFA', '#FF4D6D', '#F59E0B'];

export default function ConfettiAnimation({ trigger, onComplete }: ConfettiAnimationProps) {
  const [pieces, setPieces] = useState<ConfettiPiece[]>([]);

  useEffect(() => {
    if (trigger) {
      const newPieces: ConfettiPiece[] = [];
      
      for (let i = 0; i < 80; i++) {
        newPieces.push({
          id: i,
          x: Math.random() * window.innerWidth,
          y: -10,
          color: colors[Math.floor(Math.random() * colors.length)],
          rotation: Math.random() * 360,
          size: Math.random() * 8 + 4,
          duration: Math.random() * 2 + 2.5, // 2.5-4.5 seconds
          swayAmount: Math.random() * 100 + 50, // 50-150px horizontal sway
        });
      }
      
      setPieces(newPieces);
      
      const timer = setTimeout(() => {
        setPieces([]);
        onComplete?.();
      }, 4500);
      
      return () => clearTimeout(timer);
    }
  }, [trigger, onComplete]);

  if (pieces.length === 0) return null;

  return (
    <div className="fixed inset-0 pointer-events-none z-50 overflow-hidden">
      {pieces.map((piece) => (
        <motion.div
          key={piece.id}
          initial={{
            x: piece.x,
            y: piece.y,
            rotate: piece.rotation,
            opacity: 1,
          }}
          animate={{
            y: window.innerHeight + 100,
            x: piece.x + (Math.random() > 0.5 ? piece.swayAmount : -piece.swayAmount),
            rotate: piece.rotation + (Math.random() * 720 + 360),
            opacity: 0,
          }}
          transition={{
            duration: piece.duration,
            ease: 'easeIn',
          }}
          className="absolute"
          style={{
            width: piece.size,
            height: piece.size,
            backgroundColor: piece.color,
            borderRadius: Math.random() > 0.5 ? '50%' : '0%',
          }}
        />
      ))}
    </div>
  );
}