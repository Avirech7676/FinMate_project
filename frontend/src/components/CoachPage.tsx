import ChatInterface from './ChatInterface';

export default function CoachPanel() {
  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-2xl font-bold mb-1">FinMate Coach</h2>
        <p className="text-sm text-gray-400">
          Ask questions about your spending, subscriptions and future projections. The coach will answer in simple, concrete steps.
        </p>
      </div>
      <ChatInterface />
    </div>
  );
}

