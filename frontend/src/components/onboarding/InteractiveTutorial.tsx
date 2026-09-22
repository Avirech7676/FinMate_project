import { motion, AnimatePresence } from 'framer-motion';
import { useState } from 'react';
import { X, ArrowRight } from 'lucide-react';

interface TutorialStep {
  id: number;
  title: string;
  description: string;
  target: string;
  action: string;
}

const tutorialSteps: TutorialStep[] = [
  {
    id: 1,
    title: 'Welcome to FinMate!',
    description: 'We\'ll take a very quick 4-step tour so you can see how to import data, spot leaks, predict spending, and talk to the coach.',
    target: 'welcome',
    action: 'Next'
  },
  {
    id: 2,
    title: 'Import your transactions',
    description: 'Use the Smart Import card to upload CSVs and receipts. Confirm the column mapping and currency before you import.',
    target: 'data-import',
    action: 'Open Smart Import'
  },
  {
    id: 3,
    title: 'Spot subscription leaks',
    description: 'Visit the Subscriptions tab to see merchants that look like recurring charges and mark them as kept or removed.',
    target: 'subscriptions',
    action: 'Review suspects'
  },
  {
    id: 4,
    title: 'Predict & get advice',
    description: 'Use the Prediction and Coach tabs to see where your spending is headed and ask FinMate for concrete ways to save.',
    target: 'coach',
    action: 'Open FinMate Coach'
  }
];

interface InteractiveTutorialProps {
  isVisible: boolean;
  onComplete: () => void;
  onSkip: () => void;
}

export default function InteractiveTutorial({ isVisible, onComplete, onSkip }: InteractiveTutorialProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);

  const handleNext = () => {
    if (currentStep < tutorialSteps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      onComplete();
    }
  };

  const handleStepComplete = (stepId: number) => {
    if (!completedSteps.includes(stepId)) {
      setCompletedSteps([...completedSteps, stepId]);
    }
    handleNext();
  };

  const progress = ((currentStep + 1) / tutorialSteps.length) * 100;
  const step = tutorialSteps[currentStep];
  const stepImage = `/tutorial/${step.id}.png`;

  if (!isVisible) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4"
      >
        {/* Tutorial Card */}
        <motion.div
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.9, opacity: 0 }}
          className="glass-card p-8 rounded-2xl border border-white/10 max-w-md w-full"
        >
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-cyan-400">
                Step {currentStep + 1} of {tutorialSteps.length}
              </span>
            </div>
            <button
              onClick={onSkip}
              className="text-gray-400 hover:text-white transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Progress Bar */}
          <div className="mb-4">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ duration: 0.5 }}
              className="h-2 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-full"
            />
          </div>

          {/* Intro copy and step pills */}
          <div className="mb-6">
            <p className="text-xs text-gray-400 mb-3">
              A quick 4-step tour to help you get comfortable with your FinMate workspace.
            </p>
            <div className="flex flex-wrap gap-2">
              {tutorialSteps.map((s, index) => (
                <span
                  key={s.id}
                  className={`px-2 py-1 rounded-full text-[11px] border ${
                    index === currentStep
                      ? 'bg-cyan-500/20 border-cyan-400 text-cyan-200'
                      : 'border-white/10 text-gray-400'
                  }`}
                >
                  {s.title}
                </span>
              ))}
            </div>
          </div>

          {/* Content */}
          <motion.div
            key={currentStep}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
          >
            <h3 className="text-2xl font-bold text-white mb-2">{step.title}</h3>
            <p className="text-gray-400 mb-3">{step.description}</p>
            <div className="mb-4">
              <img
                src={stepImage}
                alt={step.title}
                className="w-full rounded-lg border border-white/10 object-cover"
              />
            </div>
            <p className="text-xs text-gray-500 mb-6">
              Focus area: <span className="font-medium text-gray-300">{step.target.replace('-', ' ')}</span>
            </p>

            {/* Action Button */}
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => handleStepComplete(step.id)}
              className="w-full px-6 py-3 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-lg font-semibold hover:shadow-lg hover:shadow-cyan-500/50 transition-shadow flex items-center justify-center gap-2"
            >
              {currentStep === tutorialSteps.length - 1 ? 'Complete' : 'Next'}
              <ArrowRight className="w-4 h-4" />
            </motion.button>
          </motion.div>

          {/* Skip Button */}
          <button
            onClick={onSkip}
            className="w-full mt-4 text-sm text-gray-400 hover:text-white transition"
          >
            Skip tutorial
          </button>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}