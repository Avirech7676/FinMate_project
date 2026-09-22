import { motion } from 'framer-motion';
import { useState } from 'react';
import { ChevronRight } from 'lucide-react';

interface QuizQuestion {
  id: number;
  question: string;
  options: Array<{ text: string; value: number }>;
}

const quizQuestions: QuizQuestion[] = [
  {
    id: 1,
    question: 'When you see something you want, what do you do?',
    options: [
      { text: 'Save up for it first', value: 1 },
      { text: 'Buy it if I have the money', value: 2 },
      { text: 'Invest in it if it has good ROI', value: 3 },
    ],
  },
  {
    id: 2,
    question: 'How do you feel about your current savings?',
    options: [
      { text: 'I wish I had more', value: 1 },
      { text: 'It\'s okay, could be better', value: 2 },
      { text: 'I\'m building wealth strategically', value: 3 },
    ],
  },
  {
    id: 3,
    question: 'What\'s your biggest financial goal?',
    options: [
      { text: 'Build an emergency fund', value: 1 },
      { text: 'Pay off debt', value: 2 },
      { text: 'Grow investments', value: 3 },
    ],
  },
  {
    id: 4,
    question: 'How often do you check your spending?',
    options: [
      { text: 'Weekly or more', value: 1 },
      { text: 'Monthly', value: 2 },
      { text: 'Rarely, I focus on long-term', value: 3 },
    ],
  },
  {
    id: 5,
    question: 'What\'s your approach to budgeting?',
    options: [
      { text: 'Strict and detailed', value: 1 },
      { text: 'Flexible with guidelines', value: 2 },
      { text: 'Focus on income growth', value: 3 },
    ],
  },
];

interface PersonalityQuizProps {
  onComplete?: (personality: 'Saver' | 'Spender' | 'Investor') => void;
}

export default function PersonalityQuiz({ onComplete }: PersonalityQuizProps) {
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<number[]>([]);
  const [showResult, setShowResult] = useState(false);
  const [personality, setPersonality] = useState<'Saver' | 'Spender' | 'Investor' | null>(null);

  const handleAnswer = (value: number) => {
    const newAnswers = [...answers, value];
    setAnswers(newAnswers);

    if (currentQuestion < quizQuestions.length - 1) {
      setCurrentQuestion(currentQuestion + 1);
    } else {
      // Calculate personality
      const total = newAnswers.reduce((a, b) => a + b, 0);
      const average = total / newAnswers.length;

      let result: 'Saver' | 'Spender' | 'Investor';
      if (average < 1.7) {
        result = 'Saver';
      } else if (average < 2.3) {
        result = 'Spender';
      } else {
        result = 'Investor';
      }

      setPersonality(result);
      setShowResult(true);
      onComplete?.(result);
    }
  };

  const progress = ((currentQuestion + 1) / quizQuestions.length) * 100;

  if (showResult && personality) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4"
      >
        <motion.div
          initial={{ y: 20 }}
          animate={{ y: 0 }}
          className="glass-card p-8 rounded-2xl border border-white/10 max-w-md w-full text-center"
        >
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: 'spring', delay: 0.2 }}
            className="w-16 h-16 rounded-full bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center mx-auto mb-6"
          >
            <span className="text-2xl">
              {personality === 'Saver' ? '🏦' : personality === 'Spender' ? '💳' : '📈'}
            </span>
          </motion.div>

          <h2 className="text-3xl font-bold text-white mb-2">You're a {personality}!</h2>
          <p className="text-gray-400 mb-6">
            {personality === 'Saver'
              ? 'You prioritize financial security and building wealth steadily.'
              : personality === 'Spender'
              ? 'You enjoy life now while maintaining a balanced approach to finances.'
              : 'You focus on growth and strategic financial decisions.'}
          </p>

          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setShowResult(false)}
            className="w-full px-6 py-3 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-lg font-semibold hover:shadow-lg hover:shadow-cyan-500/50 transition-shadow"
          >
            Continue
          </motion.button>
        </motion.div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-card p-8 rounded-2xl border border-white/10 max-w-2xl mx-auto"
    >
      {/* Progress */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-400">
            Question {currentQuestion + 1} of {quizQuestions.length}
          </span>
          <span className="text-sm font-medium text-cyan-400">{Math.round(progress)}%</span>
        </div>
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.5 }}
          className="h-2 bg-gradient-to-r from-cyan-500 to-blue-500 rounded-full"
        />
      </div>

      {/* Question */}
      <motion.div
        key={currentQuestion}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <h3 className="text-2xl font-bold text-white mb-6">
          {quizQuestions[currentQuestion].question}
        </h3>

        {/* Options */}
        <div className="space-y-3">
          {quizQuestions[currentQuestion].options.map((option, index) => (
            <motion.button
              key={index}
              whileHover={{ x: 4 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => handleAnswer(option.value)}
              className="w-full p-4 text-left rounded-lg border border-white/10 hover:border-white/20 bg-white/5 hover:bg-white/10 transition-all group flex items-center justify-between"
            >
              <span className="text-white font-medium">{option.text}</span>
              <ChevronRight className="w-5 h-5 text-gray-500 group-hover:text-white transition-colors" />
            </motion.button>
          ))}
        </div>
      </motion.div>
    </motion.div>
  );
}
