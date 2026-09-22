# Technical Design Document: Hackathon Winner Upgrade

## Overview

This design document outlines the technical implementation architecture for the Hackathon Winner Upgrade feature set. The upgrade transforms FinMate into a premium fintech application with advanced UI/UX patterns, AI-powered personalization, and engaging gamification elements.

The implementation is organized into 13 interconnected features that work together to create a cohesive user experience. This document excludes the Financial Twin AI Agent (Requirement 6), which will be designed separately.

## Architecture

### High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React + TypeScript)            │
├─────────────────────────────────────────────────────────────┤
│  Landing Page │ Dashboard │ Components │ State Management   │
│  (Vite)       │ (Story    │ (Modular)  │ (Context API +    │
│               │ Layout)   │            │  Local Storage)   │
└────────────────────────┬────────────────────────────────────┘
                         │ REST API
┌────────────────────────▼────────────────────────────────────┐
│                  Backend (FastAPI + Python)                 │
├─────────────────────────────────────────────────────────────┤
│  Auth │ Analytics │ AI Insights │ Gamification │ Export     │
│  (JWT)│ (Trends)  │ (Gemini)    │ (Challenges)│ (PDF/CSV)  │
└────────────────────────┬────────────────────────────────────┘
                         │ SQLAlchemy ORM
┌────────────────────────▼────────────────────────────────────┐
│              Database (SQLite / PostgreSQL)                  │
├─────────────────────────────────────────────────────────────┤
│  Users │ Transactions │ Receipts │ Challenges │ Preferences │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

**Frontend:**
- React 18+ with TypeScript
- Vite (build tool)
- Tailwind CSS (styling)
- Framer Motion (animations)
- Recharts (data visualizations)
- React Router (navigation)

**Backend:**
- FastAPI (REST API)
- SQLAlchemy (ORM)
- Pydantic (validation)
- Google Gemini API (AI insights)
- Pillow (image processing)
- ReportLab (PDF generation)

**Database:**
- SQLite (development)
- PostgreSQL (production)

## Components and Interfaces

### Frontend Component Hierarchy

```
App
├── Landing Page
│   ├── Hero Section
│   ├── Video Placeholder
│   ├── Sandbox Mode Launcher
│   ├── Social Proof Section
│   ├── Feature Showcase
│   └── Live Demo Preview
├── Dashboard (Story Layout)
│   ├── Header (Navigation + User Menu)
│   ├── Hero Metric Section
│   ├── Alerts Section
│   ├── Spending Breakdown
│   ├── Advanced Visualizations
│   │   ├── Bar Chart Race
│   │   ├── Heatmap Calendar
│   │   └── Comparison View
│   ├── Challenges Section
│   ├── Predictive Insights
│   ├── Smart Recommendations
│   ├── Receipt Gallery
│   ├── Onboarding Tutorial
│   └── Export & Sharing
├── Financial Personality Quiz
├── Chat Interface (Financial Twin)
└── Settings & Preferences
```

### Component File Organization

```
frontend/src/
├── components/
│   ├── landing/
│   │   ├── HeroSection.tsx
│   │   ├── VideoPlaceholder.tsx
│   │   ├── SocialProof.tsx
│   │   ├── FeatureShowcase.tsx
│   │   ├── LiveDemoPreview.tsx
│   │   └── SandboxLauncher.tsx
│   ├── dashboard/
│   │   ├── DashboardLayout.tsx (Story Layout)
│   │   ├── HeroMetric.tsx
│   │   ├── AlertsSection.tsx
│   │   ├── SpendingBreakdown.tsx
│   │   └── ScrollReveal.tsx
│   ├── visualizations/
│   │   ├── BarChartRace.tsx
│   │   ├── HeatmapCalendar.tsx
│   │   ├── ComparisonView.tsx
│   │   └── ChartSkeleton.tsx
│   ├── challenges/
│   │   ├── ChallengesSection.tsx
│   │   ├── ChallengeCard.tsx
│   │   ├── CreateChallenge.tsx
│   │   ├── Leaderboard.tsx
│   │   └── ShareAchievement.tsx
│   ├── insights/
│   │   ├── PredictiveInsights.tsx
│   │   ├── SmartRecommendations.tsx
│   │   └── InsightCard.tsx
│   ├── gallery/
│   │   ├── ReceiptGallery.tsx
│   │   ├── ReceiptThumbnail.tsx
│   │   ├── ReceiptViewer.tsx
│   │   └── ReceiptSearch.tsx
│   ├── onboarding/
│   │   ├── PersonalityQuiz.tsx
│   │   ├── InteractiveTutorial.tsx
│   │   └── TutorialOverlay.tsx
│   ├── export/
│   │   ├── ExportMenu.tsx
│   │   ├── YearInReview.tsx
│   │   └── AchievementCard.tsx
│   ├── common/
│   │   ├── MicroInteraction.tsx
│   │   ├── ConfettiAnimation.tsx
│   │   ├── ShakeAnimation.tsx
│   │   ├── FadeInAnimation.tsx
│   │   ├── AccessibilityToggle.tsx
│   │   └── HighContrastMode.tsx
│   └── accessibility/
│       ├── KeyboardNavigation.tsx
│       ├── ScreenReaderAnnouncer.tsx
│       └── FocusIndicator.tsx
├── hooks/
│   ├── useStoryScroll.ts
│   ├── useAnimationPerformance.ts
│   ├── useAccessibility.ts
│   ├── usePredictiveInsights.ts
│   ├── useSmartRecommendations.ts
│   └── useChallenges.ts
├── context/
│   ├── DashboardContext.tsx
│   ├── ChallengesContext.tsx
│   ├── AccessibilityContext.tsx
│   └── AnimationContext.tsx
├── styles/
│   ├── colors.css
│   ├── animations.css
│   ├── accessibility.css
│   └── responsive.css
└── utils/
    ├── colorSystem.ts
    ├── animationConfig.ts
    ├── accessibilityHelpers.ts
    └── exportHelpers.ts
```

### Key Component Interfaces

**HeroMetric Component:**
```typescript
interface HeroMetricProps {
  value: number;
  label: string;
  comparison: {
    value: number;
    trend: 'up' | 'down' | 'neutral';
    period: string;
  };
  color: string;
  animate?: boolean;
}
```

**BarChartRace Component:**
```typescript
interface BarChartRaceProps {
  data: CategorySpending[];
  weeks: number;
  animationDuration: number;
  onWeekChange?: (week: number) => void;
}
```

**ChallengeCard Component:**
```typescript
interface ChallengeCardProps {
  challenge: Challenge;
  userProgress: number;
  participants: number;
  onJoin?: () => void;
  onShare?: () => void;
}
```

## Data Models

### Database Schema Extensions

**New Tables Required:**

1. **financial_personalities**
```sql
CREATE TABLE financial_personalities (
  personality_id INTEGER PRIMARY KEY,
  user_id INTEGER UNIQUE FOREIGN KEY,
  personality_type VARCHAR(20), -- 'Saver', 'Spender', 'Investor'
  quiz_score INTEGER,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

2. **challenges**
```sql
CREATE TABLE challenges (
  challenge_id INTEGER PRIMARY KEY,
  creator_id INTEGER FOREIGN KEY,
  name VARCHAR(255),
  description TEXT,
  goal_amount FLOAT,
  duration_days INTEGER,
  start_date TIMESTAMP,
  end_date TIMESTAMP,
  invite_code VARCHAR(20) UNIQUE,
  is_group BOOLEAN,
  max_participants INTEGER,
  created_at TIMESTAMP
);
```

3. **challenge_participants**
```sql
CREATE TABLE challenge_participants (
  participant_id INTEGER PRIMARY KEY,
  challenge_id INTEGER FOREIGN KEY,
  user_id INTEGER FOREIGN KEY,
  current_progress FLOAT,
  rank INTEGER,
  joined_at TIMESTAMP
);
```

4. **receipts**
```sql
CREATE TABLE receipts (
  receipt_id INTEGER PRIMARY KEY,
  user_id INTEGER FOREIGN KEY,
  merchant_name VARCHAR(255),
  amount FLOAT,
  receipt_date TIMESTAMP,
  image_path VARCHAR(500),
  thumbnail_path VARCHAR(500),
  extracted_data JSON,
  created_at TIMESTAMP
);
```

5. **smart_recommendations**
```sql
CREATE TABLE smart_recommendations (
  recommendation_id INTEGER PRIMARY KEY,
  user_id INTEGER FOREIGN KEY,
  recommendation_type VARCHAR(50),
  title VARCHAR(255),
  description TEXT,
  potential_savings FLOAT,
  dismissed_at TIMESTAMP,
  created_at TIMESTAMP
);
```

6. **predictive_insights**
```sql
CREATE TABLE predictive_insights (
  insight_id INTEGER PRIMARY KEY,
  user_id INTEGER FOREIGN KEY,
  insight_type VARCHAR(50),
  message TEXT,
  confidence_level VARCHAR(20), -- 'high', 'medium', 'low'
  predicted_date TIMESTAMP,
  created_at TIMESTAMP
);
```

7. **user_preferences_extended**
```sql
ALTER TABLE users ADD COLUMN (
  financial_twin_name VARCHAR(100),
  financial_twin_avatar VARCHAR(50),
  personality_mode VARCHAR(20), -- 'supportive', 'funny', 'strict'
  sound_effects_enabled BOOLEAN DEFAULT true,
  high_contrast_mode BOOLEAN DEFAULT false,
  reduced_motion BOOLEAN DEFAULT false,
  tutorial_completed BOOLEAN DEFAULT false,
  sandbox_mode_data JSON
);
```

### Updated Models (Python)

```python
class FinancialPersonality(Base):
    __tablename__ = "financial_personalities"
    personality_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), unique=True)
    personality_type = Column(String)  # Saver, Spender, Investor
    quiz_score = Column(Integer)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class Challenge(Base):
    __tablename__ = "challenges"
    challenge_id = Column(Integer, primary_key=True)
    creator_id = Column(Integer, ForeignKey("users.user_id"))
    name = Column(String)
    description = Column(String)
    goal_amount = Column(Float)
    duration_days = Column(Integer)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    invite_code = Column(String, unique=True)
    is_group = Column(Boolean, default=False)
    max_participants = Column(Integer)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    participants = relationship("ChallengeParticipant", back_populates="challenge")

class Receipt(Base):
    __tablename__ = "receipts"
    receipt_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    merchant_name = Column(String)
    amount = Column(Float)
    receipt_date = Column(DateTime)
    image_path = Column(String)
    thumbnail_path = Column(String)
    extracted_data = Column(String)  # JSON
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
```

## API Endpoints

### Landing Page & Sandbox Mode

```
GET  /api/v1/sandbox/init
     Response: { sampleTransactions: [], sampleGoals: [] }

POST /api/v1/sandbox/explore
     Body: { action: string, data: any }
     Response: { result: any }
```

### Dashboard & Visualizations

```
GET  /api/v1/dashboard/hero-metric
     Response: { value, comparison, trend }

GET  /api/v1/dashboard/analytics/bar-chart-race
     Query: { weeks: 12 }
     Response: { categories: [], weeklyData: [] }

GET  /api/v1/dashboard/analytics/heatmap
     Query: { days: 365 }
     Response: { dailySpending: [] }

GET  /api/v1/dashboard/analytics/comparison
     Response: { userSpending: {}, averageSpending: {} }
```

### Challenges

```
POST /api/v1/challenges
     Body: { name, goalAmount, durationDays, isGroup, maxParticipants }
     Response: { challengeId, inviteCode }

GET  /api/v1/challenges
     Response: { activeChallenges: [], pastChallenges: [] }

POST /api/v1/challenges/{id}/join
     Body: { inviteCode }
     Response: { success: boolean }

GET  /api/v1/challenges/{id}/leaderboard
     Response: { participants: [] }

POST /api/v1/challenges/{id}/share
     Response: { shareUrl: string, imageUrl: string }
```

### Predictive Insights & Recommendations

```
GET  /api/v1/insights/predictive
     Response: { insights: [] }

GET  /api/v1/recommendations/smart
     Response: { recommendations: [] }

POST /api/v1/recommendations/{id}/dismiss
     Response: { success: boolean }
```

### Receipt Gallery

```
GET  /api/v1/receipts
     Query: { page, limit, search, sortBy }
     Response: { receipts: [], total: number }

GET  /api/v1/receipts/{id}
     Response: { receipt: Receipt }

POST /api/v1/receipts/search
     Body: { merchant, amountRange, dateRange }
     Response: { receipts: [] }
```

### Onboarding & Personality

```
POST /api/v1/onboarding/personality-quiz
     Body: { answers: number[] }
     Response: { personalityType: string, score: number }

GET  /api/v1/onboarding/tutorial-status
     Response: { completed: boolean, currentStep: number }

POST /api/v1/onboarding/tutorial-step
     Body: { step: number }
     Response: { success: boolean }
```

### Export & Sharing

```
GET  /api/v1/export/pdf
     Query: { type: 'report' | 'year-in-review' }
     Response: PDF file

GET  /api/v1/export/csv
     Response: CSV file

POST /api/v1/export/achievement-card
     Body: { achievementId }
     Response: { imageUrl: string }

GET  /api/v1/export/year-in-review
     Response: { summary: YearInReview }
```

### Accessibility

```
GET  /api/v1/preferences/accessibility
     Response: { highContrast, reducedMotion, keyboardShortcuts }

POST /api/v1/preferences/accessibility
     Body: { highContrast, reducedMotion }
     Response: { success: boolean }
```

## State Management

### Context Structure

**DashboardContext:**
```typescript
interface DashboardContextType {
  heroMetric: HeroMetric;
  alerts: Alert[];
  spendingBreakdown: SpendingCategory[];
  visualizationData: VisualizationData;
  isLoading: boolean;
  error: string | null;
  refreshDashboard: () => Promise<void>;
}
```

**ChallengesContext:**
```typescript
interface ChallengesContextType {
  activeChallenges: Challenge[];
  pastChallenges: Challenge[];
  userProgress: Map<number, number>;
  leaderboards: Map<number, Participant[]>;
  createChallenge: (data: CreateChallengeData) => Promise<void>;
  joinChallenge: (inviteCode: string) => Promise<void>;
  shareAchievement: (challengeId: number) => Promise<ShareData>;
}
```

**AccessibilityContext:**
```typescript
interface AccessibilityContextType {
  highContrastMode: boolean;
  reducedMotion: boolean;
  keyboardShortcutsEnabled: boolean;
  toggleHighContrast: () => void;
  toggleReducedMotion: () => void;
  announceToScreenReader: (message: string) => void;
}
```

### Local Storage Schema

```typescript
interface LocalStorageSchema {
  'finmate:user': User;
  'finmate:dashboard:cache': DashboardData;
  'finmate:challenges:cache': Challenge[];
  'finmate:accessibility': AccessibilityPreferences;
  'finmate:tutorial:progress': TutorialProgress;
  'finmate:sandbox:data': SandboxData;
}
```

## Animation & Transition Specifications

### Color System

**Primary Colors:**
- Success Green: `#00D4AA` (RGB: 0, 212, 170)
- Success Green Alt: `#10B981` (RGB: 16, 185, 129)
- Warning Orange: `#FF6B35` (RGB: 255, 107, 53)
- Warning Orange Alt: `#FF8C42` (RGB: 255, 140, 66)
- Premium Purple: `#6B4CE6` (RGB: 107, 76, 230)
- Premium Purple Alt: `#8B5CF6` (RGB: 139, 92, 246)
- Critical Red: `#FF4D6D` (RGB: 255, 77, 109)

**Neutral Colors:**
- Gray 600: `#4B5563` (RGB: 75, 85, 99)
- Gray 700: `#6B7280` (RGB: 107, 114, 128)
- Gray 800: `#9CA3AF` (RGB: 156, 163, 175)

**Contrast Ratios:**
- WCAG AA: 4.5:1 (minimum for normal text)
- WCAG AAA: 7:1 (high contrast mode)

### Animation Specifications

**Micro-interactions:**
```css
/* Confetti Animation (3 seconds) */
@keyframes confetti-fall {
  0% { transform: translateY(0) rotate(0deg); opacity: 1; }
  100% { transform: translateY(500px) rotate(720deg); opacity: 0; }
}

/* Shake Animation (budget exceeded) */
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-10px); }
  75% { transform: translateX(10px); }
}

/* Progress Bar Animation (800ms) */
@keyframes progress-fill {
  0% { width: 0%; }
  100% { width: var(--progress-value); }
}
animation: progress-fill 800ms cubic-bezier(0.4, 0, 0.2, 1);

/* Hover Scale (150ms) */
.interactive-card:hover {
  transform: scale(1.02);
  transition: transform 150ms ease-out;
}

/* Fade In (300ms) */
@keyframes fade-in {
  0% { opacity: 0; }
  100% { opacity: 1; }
}
animation: fade-in 300ms ease-in;

/* Color Transition (200ms) */
.color-changing-element {
  transition: background-color 200ms ease-in-out,
              color 200ms ease-in-out,
              border-color 200ms ease-in-out;
}
```

**Performance Constraints:**
- Maximum 3 concurrent animations
- Minimum 60fps target
- Respect `prefers-reduced-motion` media query
- Disable animations on low-end devices

### Sound Effects

- Success sound: 1 second max duration
- Toggle in settings: `sound_effects_enabled`
- File format: MP3 (compressed)
- Volume: -6dB (normalized)

## Accessibility Implementation

### Keyboard Navigation

**Keyboard Shortcuts:**
- `C`: Open chat with Financial Twin
- `G`: Navigate to goals
- `D`: Go to dashboard
- `?`: Show help/shortcuts
- `Tab`: Navigate forward
- `Shift+Tab`: Navigate backward
- `Enter`: Activate button/link
- `Space`: Toggle checkbox/button
- `Escape`: Close modal/menu

**Focus Management:**
- Visible focus indicators (2px outline, color: `#6B4CE6`)
- Logical tab order (top-to-bottom, left-to-right)
- Focus trap in modals
- Focus restoration after modal close

### ARIA Implementation

```typescript
// ARIA Labels
<button aria-label="Open navigation menu">
  <MenuIcon />
</button>

// ARIA Live Regions
<div aria-live="polite" aria-atomic="true" role="status">
  {dynamicContent}
</div>

// ARIA Descriptions
<div aria-describedby="chart-description">
  <Chart />
</div>
<p id="chart-description">
  Your spending increased 15% this month
</p>

// ARIA Hidden
<span aria-hidden="true">→</span>
```

### Screen Reader Support

- All icons have text alternatives
- Form labels associated with inputs
- Dynamic content announced via live regions
- Chart data available as text alternative
- Skip links for main content

### High Contrast Mode

```css
.high-contrast-mode {
  --text-color: #000000;
  --bg-color: #FFFFFF;
  --border-color: #000000;
  --focus-color: #0000FF;
  
  /* Increase contrast ratios to 7:1 */
  --success-color: #008000;
  --warning-color: #FF0000;
  --info-color: #0000FF;
}
```

### Motion Preferences

```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

## Testing Strategy

### Unit Testing

**Focus Areas:**
- Color contrast validation
- Animation timing calculations
- Data transformation functions
- Accessibility helper functions
- Export formatting logic

**Example Test:**
```typescript
describe('ColorSystem', () => {
  it('should maintain WCAG AA contrast ratio', () => {
    const contrast = getContrastRatio('#FF6B35', '#FFFFFF');
    expect(contrast).toBeGreaterThanOrEqual(4.5);
  });
});
```

### Property-Based Testing

**Property 1: Color Contrast Invariant**
*For any* color pair used in the design system, the contrast ratio should meet WCAG AA standards (4.5:1 minimum)
**Validates: Requirements 3.5**

**Property 2: Animation Performance**
*For any* dashboard state change, the number of concurrent animations should not exceed 3 to maintain 60fps performance
**Validates: Requirements 4.8**

**Property 3: Accessibility Round Trip**
*For any* user preference setting (high contrast, reduced motion), toggling it on then off should restore the original state
**Validates: Requirements 14.3**

**Property 4: Receipt Gallery Lazy Loading**
*For any* receipt gallery with N receipts, only visible thumbnails plus 10 ahead should be loaded in memory
**Validates: Requirements 10.7**

**Property 5: Challenge Progress Consistency**
*For any* challenge, the sum of all participant progress should not exceed the total goal amount multiplied by participant count
**Validates: Requirements 7.6**

**Property 6: Recommendation Dismissal**
*For any* dismissed recommendation, it should not reappear for 30 days from dismissal date
**Validates: Requirements 9.6**

**Property 7: Predictive Insight Accuracy**
*For any* predictive insight with "high" confidence, the prediction should be based on at least 12 weeks of consistent data
**Validates: Requirements 8.7**

**Property 8: Export Data Integrity**
*For any* exported report, all transactions included should match the date range and category filters applied
**Validates: Requirements 13.1**

### Integration Testing

- Landing page → Sandbox mode transition
- Dashboard data loading and caching
- Challenge creation and participant joining
- Receipt upload and gallery display
- Export generation and download

### Accessibility Testing

- Keyboard navigation through all interactive elements
- Screen reader compatibility (NVDA, JAWS, VoiceOver)
- Color contrast verification
- Motion preference respect
- Focus indicator visibility

## Performance Considerations

### Frontend Optimization

- Code splitting by route
- Lazy loading of visualizations
- Image optimization (WebP with fallbacks)
- CSS-in-JS for dynamic theming
- Virtual scrolling for long lists

### Backend Optimization

- Database indexing on frequently queried fields
- Caching layer for analytics data
- Pagination for large datasets
- Async processing for exports
- Rate limiting on API endpoints

### Monitoring

- Core Web Vitals tracking
- Error logging and reporting
- Performance metrics dashboard
- User session analytics

## Deployment Considerations

### Frontend Deployment

- Build optimization with Vite
- CDN distribution for static assets
- Service worker for offline support
- Environment-based configuration

### Backend Deployment

- Database migration strategy
- API versioning for backward compatibility
- Health check endpoints
- Graceful shutdown handling

## Security Considerations

- Input validation on all API endpoints
- SQL injection prevention via ORM
- XSS protection via React's built-in escaping
- CSRF tokens for state-changing operations
- Rate limiting on sensitive endpoints
- Secure password hashing (bcrypt)
- JWT token expiration and refresh

## Future Enhancements

- Real-time collaboration on challenges
- Mobile app native implementation
- Advanced ML models for predictions
- Integration with banking APIs
- Multi-currency support
- Dark mode theme
- Internationalization (i18n)


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Video Placeholder Aspect Ratio

*For any* video placeholder component, the computed aspect ratio (width / height) should equal 16/9 (approximately 1.778)

**Validates: Requirements 1.2**

### Property 2: Sandbox Mode Data Population

*For any* user clicking "Try without signup", the sandbox mode should initialize with pre-populated sample data containing at least 10 sample transactions

**Validates: Requirements 1.3**

### Property 3: Feature Showcase Card Count

*For any* landing page render, the feature showcase section should display at least 6 animated feature cards

**Validates: Requirements 1.5**

### Property 4: Responsive Design Adaptation

*For any* viewport width between 320px and 1920px, the landing page layout should adapt correctly without horizontal scrolling or content overflow

**Validates: Requirements 1.7**

### Property 5: Dashboard Story Layout Structure

*For any* dashboard render, the content should be organized in a vertically scrollable layout (not tab-based) with sections appearing in order: Hero Metric, Alerts, Spending Breakdown, Analytics

**Validates: Requirements 2.1, 2.3**

### Property 6: Hero Metric Font Size

*For any* hero metric component, the computed font size should be at least 48px

**Validates: Requirements 2.2**

### Property 7: Initial Visible Sections

*For any* dashboard on initial load, only 3 primary sections should be visible in the viewport before user scrolling

**Validates: Requirements 2.4**

### Property 8: Scroll-Reveal Animation

*For any* dashboard section revealed by scrolling, a fade-in animation should be applied with 300ms duration

**Validates: Requirements 2.5**

### Property 9: Content Priority Ordering

*For any* dashboard render, actionable insights should appear before raw data visualizations in the DOM

**Validates: Requirements 2.6**

### Property 10: Card Spacing Consistency

*For any* dashboard card, the computed margin or padding should be exactly 16px between adjacent sections

**Validates: Requirements 2.7**

### Property 11: Warning Color Range

*For any* spending alert element, the background or text color should fall within the hex range #FF6B35 to #FF8C42

**Validates: Requirements 3.1**

### Property 12: Premium Color Range

*For any* premium feature or achievement element, the color should fall within the hex range #6B4CE6 to #8B5CF6

**Validates: Requirements 3.2**

### Property 13: Success Color Range

*For any* savings win or positive outcome element, the color should fall within the hex range #00D4AA to #10B981

**Validates: Requirements 3.3**

### Property 14: Critical Warning Color

*For any* critical warning or overspending indicator, the color should be exactly #FF4D6D

**Validates: Requirements 3.4**

### Property 15: WCAG AA Contrast Ratio

*For any* text element on a colored background, the contrast ratio should be at least 4.5:1 (WCAG AA standard)

**Validates: Requirements 3.5**

### Property 16: Color Transition Duration

*For any* element changing color state, the CSS transition duration should be exactly 200ms

**Validates: Requirements 3.6**

### Property 17: Secondary Information Color Range

*For any* secondary information element, the color should fall within the hex range #6B7280 to #9CA3AF

**Validates: Requirements 3.7**

### Property 18: Confetti Animation Duration

*For any* goal achievement event, the confetti animation should trigger and last exactly 3 seconds

**Validates: Requirements 4.1**

### Property 19: Budget Overspend Shake Animation

*For any* metric where spending exceeds budget by 10% or more, a shake animation should be applied

**Validates: Requirements 4.2**

### Property 20: Progress Bar Animation Easing

*For any* progress bar, the animation should use cubic-bezier easing and complete in exactly 800ms

**Validates: Requirements 4.3**

### Property 21: Sound Effects Toggle

*For any* user toggling sound effects on/off, the setting should persist and affect subsequent achievement notifications

**Validates: Requirements 4.4**

### Property 22: Achievement Sound Duration

*For any* achievement unlock with sound effects enabled, the success sound should play with duration at most 1 second

**Validates: Requirements 4.5**

### Property 23: Interactive Card Hover Scale

*For any* interactive card on hover, the transform scale should be exactly 1.02x with 150ms transition

**Validates: Requirements 4.6**

### Property 24: Fade-In Animation for New Content

*For any* newly loaded content, a fade-in animation should be applied with exactly 300ms duration

**Validates: Requirements 4.7**

### Property 25: Concurrent Animation Limit

*For any* dashboard state, the number of concurrent animations should never exceed 3 to maintain 60fps performance

**Validates: Requirements 4.8**

### Property 26: Bar Chart Race Data

*For any* bar chart race visualization, it should display the top 5 spending categories animated over exactly 12 weeks of data

**Validates: Requirements 5.1**

### Property 27: Heatmap Calendar Coverage

*For any* heatmap calendar visualization, it should display spending intensity data for exactly 365 days

**Validates: Requirements 5.2**

### Property 28: Comparison View Data Completeness

*For any* comparison view, both user spending and average user spending should be displayed for all categories

**Validates: Requirements 5.3**

### Property 29: Interactive Chart Tooltips

*For any* interactive chart, hovering over data points should reveal tooltips with exact values and dates

**Validates: Requirements 5.4**

### Property 30: Consistent Category Color Mapping

*For any* spending category, the color used should be identical across all visualizations (bar chart, heatmap, comparison view)

**Validates: Requirements 5.5**

### Property 31: Responsive Chart Layout

*For any* chart on a viewport with width below 768px, the layout should adapt (e.g., stacked bars instead of side-by-side)

**Validates: Requirements 5.6**

### Property 32: Loading Skeleton Dimensions

*For any* chart loading state, the skeleton placeholder should have dimensions matching the final rendered chart

**Validates: Requirements 5.7**

### Property 33: Active Challenges Display Limit

*For any* challenges section, at most 3 active challenges should be displayed

**Validates: Requirements 7.1**

### Property 34: Challenge Duration Bounds

*For any* custom challenge created, the duration should be between 7 and 90 days inclusive

**Validates: Requirements 7.2**

### Property 35: Unique Invite Code Generation

*For any* challenge created, a unique invite code should be generated that doesn't match any existing challenge code

**Validates: Requirements 7.3**

### Property 36: Leaderboard Ranking Accuracy

*For any* challenge leaderboard, participants should be ranked in descending order by progress amount

**Validates: Requirements 7.4**

### Property 37: Achievement Card Shareability

*For any* achievement card, it should be shareable to social media with pre-formatted text and image

**Validates: Requirements 7.5**

### Property 38: Challenge Progress Calculation

*For any* challenge, the percentage completion should equal (current progress / goal amount) * 100, updated daily

**Validates: Requirements 7.6**

### Property 39: Challenge Completion XP Award

*For any* challenge that completes, the top 3 participants should receive bonus XP

**Validates: Requirements 7.7**

### Property 40: Group Challenge Participant Bounds

*For any* group challenge, the participant count should be between 2 and 10 inclusive

**Validates: Requirements 7.8**

### Property 41: Budget Overspend Prediction

*For any* user with spending exceeding monthly budget, a predictive insight should display the projected overspend amount

**Validates: Requirements 8.1**

### Property 42: Budget Exhaustion Date Prediction

*For any* user with current spending rate, the predicted budget exhaustion date should be calculated as (remaining budget / daily spending rate) days from today

**Validates: Requirements 8.2**

### Property 43: Recurring Pattern Detection

*For any* recurring spending pattern detected, the next occurrence date should be predicted based on historical frequency

**Validates: Requirements 8.3**

### Property 44: Pattern Display with Supporting Data

*For any* detected spending pattern, it should be displayed with at least 3 supporting transactions as evidence

**Validates: Requirements 8.4**

### Property 45: Proactive Budget Alert Timing

*For any* user with predicted budget exhaustion, an alert should be sent exactly 3 days before the predicted date

**Validates: Requirements 8.5**

### Property 46: Prediction Data Window

*For any* predictive insight, the calculation should use exactly the last 12 weeks of transaction data

**Validates: Requirements 8.6**

### Property 47: Prediction Confidence Assignment

*For any* predictive insight, the confidence level should be assigned based on data consistency: high (>80% consistency), medium (50-80%), low (<50%)

**Validates: Requirements 8.7**

### Property 48: Subscription Consolidation Recommendation

*For any* user with multiple subscriptions in the same category, a consolidation recommendation should be displayed

**Validates: Requirements 9.1**

### Property 49: Bill Optimization Suggestions

*For any* bill with optimization opportunity, a recommendation should include the specific savings amount

**Validates: Requirements 9.2**

### Property 50: Category Spending Comparison Tips

*For any* category where user spending differs from average, a tip should be generated with the percentage difference

**Validates: Requirements 9.3**

### Property 51: Recommendation Ranking by Savings

*For any* set of recommendations, they should be sorted in descending order by potential savings amount

**Validates: Requirements 9.4**

### Property 52: Weekly Recommendation Updates

*For any* user with new transactions, recommendations should be recalculated and updated weekly

**Validates: Requirements 9.5**

### Property 53: Recommendation Dismissal Duration

*For any* dismissed recommendation, it should not reappear for exactly 30 days from dismissal date

**Validates: Requirements 9.6**

### Property 54: Minimum Recommendations Display

*For any* user with 30+ days of transaction data, at least 3 actionable recommendations should be displayed

**Validates: Requirements 9.7**

### Property 55: Receipt Gallery Grid Layout

*For any* receipt gallery on desktop (viewport >= 768px), receipts should display in 3 columns; on mobile (< 768px), in 2 columns

**Validates: Requirements 10.1**

### Property 56: Receipt Thumbnail Overlay

*For any* receipt thumbnail, merchant name and amount should be overlaid on the image

**Validates: Requirements 10.2**

### Property 57: Receipt Detail View

*For any* receipt thumbnail tapped, the full receipt image and extracted data should be displayed

**Validates: Requirements 10.3**

### Property 58: Receipt Progress Indicator

*For any* receipt gallery, a progress indicator should display the total number of receipts scanned

**Validates: Requirements 10.4**

### Property 59: Receipt Search Functionality

*For any* receipt search query (merchant, amount range, or date range), only matching receipts should be displayed

**Validates: Requirements 10.5**

### Property 60: Receipt Sorting Options

*For any* receipt gallery, receipts should be sortable by date (newest/oldest) or amount (highest/lowest)

**Validates: Requirements 10.6**

### Property 61: Receipt Lazy Loading

*For any* receipt gallery, only visible thumbnails plus 10 ahead should be loaded in memory at any time

**Validates: Requirements 10.7**

### Property 62: Personality Quiz Question Count

*For any* new user after signup, the personality quiz should present exactly 5 questions

**Validates: Requirements 11.1**

### Property 63: Personality Classification

*For any* completed personality quiz, responses should be classified into exactly one of: "Saver", "Spender", or "Investor"

**Validates: Requirements 11.2**

### Property 64: Personality Storage

*For any* user completing the personality quiz, the classification should be stored in user preferences

**Validates: Requirements 11.3**

### Property 65: Personality Badge Display

*For any* user profile, the personality badge should display the user's classified personality type

**Validates: Requirements 11.4**

### Property 66: Personality-Based Twin Responses

*For any* Financial Twin response, the tone and content should vary based on the user's personality type

**Validates: Requirements 11.5**

### Property 67: Personality-Tailored Recommendations

*For any* smart recommendation, the type and aggressiveness should match the user's personality (e.g., aggressive savings for Savers)

**Validates: Requirements 11.6**

### Property 68: Quiz Retake and Update

*For any* user retaking the personality quiz from settings, their personality classification should be updated

**Validates: Requirements 11.7**

### Property 69: Tutorial Display on First Access

*For any* new user accessing the dashboard for the first time, an interactive tutorial overlay should be displayed

**Validates: Requirements 12.1**

### Property 70: Sample Transaction Population

*For any* new user, exactly 10 sample transactions should be pre-populated for exploration

**Validates: Requirements 12.2**

### Property 71: Tutorial Step Guidance

*For any* tutorial, it should guide users through exactly 4 key actions: viewing analytics, scanning receipt, setting goal, chatting with Financial Twin

**Validates: Requirements 12.3**

### Property 72: Tutorial Progress Indicators

*For any* tutorial step, a progress indicator should display the current step (e.g., "Step 2 of 4")

**Validates: Requirements 12.4**

### Property 73: First Transaction Achievement

*For any* user completing their first real transaction, an achievement should be awarded and 50 XP unlocked

**Validates: Requirements 12.5**

### Property 74: Tutorial Skip Persistence

*For any* user skipping the tutorial, it should not reappear unless manually restarted from settings

**Validates: Requirements 12.6**

### Property 75: Sample Data Removal

*For any* user creating their first real transaction, all sample transactions should be removed from their account

**Validates: Requirements 12.7**

### Property 76: PDF Report Generation

*For any* export request, a PDF report should be generated with branding, charts, and transaction summaries

**Validates: Requirements 13.1**

### Property 77: Year In Review Completeness

*For any* year-end Year In Review, it should include total spending, top 5 categories, and all achievements unlocked that year

**Validates: Requirements 13.2**

### Property 78: Achievement Card Dimensions

*For any* achievement card generated, the PNG image should be exactly 1200x630px

**Validates: Requirements 13.3**

### Property 79: LinkedIn Achievement Formatting

*For any* achievement shared to LinkedIn, the text should include hashtags and emojis

**Validates: Requirements 13.4**

### Property 80: CSV Export Completeness

*For any* CSV export, all transaction fields should be included (date, amount, category, description, etc.)

**Validates: Requirements 13.5**

### Property 81: Goal Completion Share Button

*For any* goal completion screen, a "Share Milestone" button should be present and functional

**Validates: Requirements 13.6**

### Property 82: Year In Review Animations

*For any* Year In Review render, animated transitions should be applied to content sections

**Validates: Requirements 13.7**

### Property 83: Full Keyboard Navigation

*For any* interactive element on the dashboard, it should be accessible via keyboard navigation with visible focus indicators

**Validates: Requirements 14.1**

### Property 84: ARIA Label Coverage

*For any* icon, button, or interactive component, an appropriate ARIA label should be present

**Validates: Requirements 14.2**

### Property 85: High Contrast Mode Contrast Ratio

*For any* element in high contrast mode, the contrast ratio should be at least 7:1 (WCAG AAA)

**Validates: Requirements 14.3**

### Property 86: Dynamic Content Screen Reader Announcement

*For any* dynamic content change, it should be announced to screen readers via ARIA live regions

**Validates: Requirements 14.4**

### Property 87: Keyboard Shortcuts Functionality

*For any* keyboard shortcut (e.g., "C" for chat, "G" for goals), pressing it should trigger the corresponding action

**Validates: Requirements 14.5**

### Property 88: Reduced Motion Respect

*For any* user with prefers-reduced-motion enabled, animations should be disabled or significantly reduced

**Validates: Requirements 14.6**

### Property 89: Visualization Text Alternatives

*For any* data visualization, a text alternative should be available describing key insights

**Validates: Requirements 14.7**

### Property 90: Logical Tab Order

*For any* dashboard render, the tab order should follow visual hierarchy from top to bottom, left to right

**Validates: Requirements 14.8**

## Error Handling

### Frontend Error Handling

**API Error Responses:**
- 400 Bad Request: Display user-friendly validation error message
- 401 Unauthorized: Redirect to login page
- 403 Forbidden: Display permission denied message
- 404 Not Found: Display "Resource not found" message
- 500 Server Error: Display "Something went wrong" with retry option
- Network timeout: Display offline message with retry button

**Component Error Boundaries:**
- Wrap major sections in error boundaries
- Display fallback UI with error message
- Log errors to monitoring service
- Provide "Try again" button

**Form Validation:**
- Real-time validation feedback
- Clear error messages below fields
- Prevent submission with invalid data
- Highlight invalid fields with red border

### Backend Error Handling

**Database Errors:**
- Connection failures: Retry with exponential backoff
- Constraint violations: Return 400 with specific field error
- Transaction failures: Rollback and return 500

**API Errors:**
- Input validation: Return 400 with field-level errors
- Authentication failures: Return 401
- Authorization failures: Return 403
- Rate limiting: Return 429 with Retry-After header

**External Service Errors:**
- Gemini API failures: Fall back to cached insights
- Image processing failures: Return 400 with retry option
- PDF generation failures: Return 500 with retry option

## Testing Strategy

### Unit Testing

**Focus Areas:**
- Color contrast calculations
- Animation timing and easing functions
- Data transformation and calculations
- Accessibility helper functions
- Export formatting logic
- Personality classification algorithm
- Recommendation ranking logic
- Prediction calculations

**Example Tests:**
```typescript
describe('ColorContrast', () => {
  it('should calculate correct contrast ratio', () => {
    const ratio = getContrastRatio('#FF6B35', '#FFFFFF');
    expect(ratio).toBeGreaterThanOrEqual(4.5);
  });
});

describe('PersonalityClassification', () => {
  it('should classify Saver personality correctly', () => {
    const answers = [1, 1, 2, 1, 2]; // Saver-leaning answers
    const personality = classifyPersonality(answers);
    expect(personality).toBe('Saver');
  });
});
```

### Property-Based Testing

All 90 correctness properties listed above should be implemented as property-based tests using the appropriate testing library for the target language (Jest for JavaScript/TypeScript, pytest for Python).

**Configuration:**
- Minimum 100 iterations per property test
- Each test tagged with: `Feature: hackathon-winner-upgrade, Property {number}: {property_text}`
- Generators for realistic data (transactions, users, challenges)
- Shrinking enabled for failure analysis

**Example Property Test:**
```typescript
describe('Property: WCAG AA Contrast Ratio', () => {
  it('should maintain 4.5:1 contrast for all text on colored backgrounds', () => {
    fc.assert(
      fc.property(
        fc.hexaString({ minLength: 6, maxLength: 6 }),
        fc.hexaString({ minLength: 6, maxLength: 6 }),
        (bgColor, textColor) => {
          const ratio = getContrastRatio(`#${bgColor}`, `#${textColor}`);
          return ratio >= 4.5;
        }
      ),
      { numRuns: 100 }
    );
  });
});
```

### Integration Testing

- Landing page → Sandbox mode transition
- Dashboard data loading and caching
- Challenge creation and participant joining
- Receipt upload and gallery display
- Export generation and download
- Personality quiz completion and storage
- Tutorial progression and sample data removal

### Accessibility Testing

- Keyboard navigation through all interactive elements
- Screen reader compatibility (NVDA, JAWS, VoiceOver)
- Color contrast verification across all color combinations
- Motion preference respect (prefers-reduced-motion)
- Focus indicator visibility and logical order
- ARIA label and live region functionality

### Performance Testing

- Landing page load time < 2 seconds
- Dashboard initial render < 1 second
- Chart rendering < 500ms
- Animation frame rate >= 60fps
- Memory usage with 1000+ receipts < 50MB

### Visual Regression Testing

- Landing page hero section
- Dashboard layout at different viewport sizes
- Chart visualizations
- Animation sequences
- High contrast mode rendering
- Dark mode (future enhancement)
