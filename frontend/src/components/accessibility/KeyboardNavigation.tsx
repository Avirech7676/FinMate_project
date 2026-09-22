import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface KeyboardShortcut {
  key: string;
  description: string;
  action: () => void;
}

interface KeyboardNavigationProps {
  shortcuts: KeyboardShortcut[];
}

export default function KeyboardNavigation({ shortcuts }: KeyboardNavigationProps) {
  const [showHelp, setShowHelp] = useState(false);
  const [focusedElement, setFocusedElement] = useState<HTMLElement | null>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Show help with ?
      if (e.key === '?' && !e.ctrlKey && !e.altKey && !e.metaKey) {
        e.preventDefault();
        setShowHelp(!showHelp);
        return;
      }

      // Hide help with Escape
      if (e.key === 'Escape' && showHelp) {
        setShowHelp(false);
        return;
      }

      // Execute shortcuts
      const shortcut = shortcuts.find(s => s.key.toLowerCase() === e.key.toLowerCase());
      if (shortcut && !e.ctrlKey && !e.altKey && !e.metaKey) {
        e.preventDefault();
        shortcut.action();
      }
    };

    const handleFocus = (e: FocusEvent) => {
      setFocusedElement(e.target as HTMLElement);
    };

    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('focusin', handleFocus);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('focusin', handleFocus);
    };
  }, [shortcuts, showHelp]);

  return (
    <>
      {/* Focus Indicator */}
      {focusedElement && (
        <div
          className="fixed pointer-events-none z-50 border-2 border-cyan-500 rounded transition-all duration-150"
          style={{
            left: focusedElement.offsetLeft - 2,
            top: focusedElement.offsetTop - 2,
            width: focusedElement.offsetWidth + 4,
            height: focusedElement.offsetHeight + 4,
          }}
        />
      )}

      {/* Keyboard Shortcuts Help */}
      <AnimatePresence>
        {showHelp && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              className="glass-card p-6 rounded-lg border border-white/10 max-w-md w-full"
            >
              <h3 className="text-xl font-bold text-white mb-4">Keyboard Shortcuts</h3>
              
              <div className="space-y-3">
                {shortcuts.map((shortcut, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <span className="text-gray-300">{shortcut.description}</span>
                    <kbd className="px-2 py-1 bg-gray-700 text-white rounded text-sm font-mono">
                      {shortcut.key}
                    </kbd>
                  </div>
                ))}
                <div className="flex items-center justify-between border-t border-white/10 pt-3">
                  <span className="text-gray-300">Show/hide this help</span>
                  <kbd className="px-2 py-1 bg-gray-700 text-white rounded text-sm font-mono">?</kbd>
                </div>
              </div>

              <button
                onClick={() => setShowHelp(false)}
                className="w-full mt-6 px-4 py-2 bg-cyan-500/20 text-cyan-400 rounded-lg hover:bg-cyan-500/30 transition"
              >
                Close (Esc)
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}