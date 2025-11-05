# Study Pal - Complete Workflow Implementation Roadmap

## Overview
This document outlines the implementation plan to complete the full Study Pal workflow, integrating all components into a seamless user experience.

---

## Phase 1: User Onboarding System

### Objective
Build an interactive onboarding flow that guides new users through profile creation.

### Tasks

#### 1.1 Create Onboarding Module
**File:** `agents/onboarding.py`

**Implementation:**
- Create `OnboardingAgent` class
- Implement interactive CLI questionnaire
- Methods to implement:
  - `run_onboarding()` - Main entry point
  - `collect_basic_info()` - Name, academic field
  - `select_persona()` - Display persona options with descriptions
  - `collect_learning_goals()` - What user wants to achieve
  - `collect_study_topics()` - Current subjects
  - `identify_pain_points()` - Procrastination, anxiety, etc.
  - `save_profile()` - Create and save UserProfile

**Persona Options to Present:**
- Feynman (simplicity, curiosity)
- Socrates (critical thinking)
- Maya Angelou (empowerment)
- Steve Jobs (innovation)
- Marcus Aurelius (discipline)
- Marie Curie (persistence)

#### 1.2 Add Profile Detection
**File:** `main.py`

**Modifications:**
- Add startup profile check
- If no profile exists for user_id → trigger onboarding
- If profile exists → load and continue
- Add `--onboard` flag to force re-onboarding

#### 1.3 Testing
- Test new user flow
- Test existing user flow
- Test profile validation
- Test persona selection

**Estimated Time:** 1-2 days

---

## Phase 2: Weakness Tracking & Session Analysis

### Objective
Enable the tutor to identify topics where the user struggles and generate recommendations.

### Tasks

#### 2.1 Create Weakness Analyzer
**File:** `core/weakness_analyzer.py`

**Data Models:**
```python
@dataclass
class WeakPoint:
    topic: str
    difficulty_level: str  # "mild", "moderate", "severe"
    evidence: list[str]  # quotes from conversation
    frequency: int  # how many times topic came up

@dataclass
class SessionRecommendations:
    weak_points: list[WeakPoint]
    priority_topics: list[str]
    suggested_focus_time: dict[str, int]  # topic -> minutes
    study_approach_tips: list[str]
```

**Implementation:**
- Create `WeaknessAnalyzer` class
- Methods:
  - `analyze_conversation(messages: list[BaseMessage])` -> WeakPoints
  - `detect_struggle_indicators(message: str)` -> bool
  - `extract_topics(messages: list)` -> dict[str, int]
  - `generate_recommendations(weak_points: list[WeakPoint])` -> SessionRecommendations

**Struggle Indicators to Detect:**
- Repeated questions on same topic
- Keywords: "confused", "don't understand", "still unclear", "lost"
- Multiple explanations needed for same concept
- User asking for simpler explanations

#### 2.2 Integrate with Tutor Chatbot
**File:** `agents/tutor_chatbot.py`

**Modifications:**
- Add `WeaknessAnalyzer` instance
- Track session start time
- Add `/finish` command to end session
- On session finish:
  - Run weakness analysis on conversation history
  - Generate recommendations
  - Display summary to user
  - Return structured data for scheduler

**New Methods:**
- `start_session(user_id: str)` -> Session
- `end_session()` -> tuple[WeakPoints, SessionRecommendations]
- `get_session_summary()` -> dict

#### 2.3 Create Session Manager
**File:** `agents/session_manager.py`

**Implementation:**
- Track active sessions per user
- Save session transcripts to disk
- Store weak points history
- Methods:
  - `create_session(user_id: str)` -> Session
  - `save_session(session: Session)`
  - `get_session_history(user_id: str)` -> list[Session]
  - `get_weak_points_over_time(user_id: str)` -> dict

**Storage Structure:**
```
data/
  sessions/
    {user_id}/
      2025-01-15_session_001.json
      2025-01-16_session_002.json
  weak_points/
    {user_id}_weak_points.json
```

#### 2.4 Testing
- Test weakness detection with sample conversations
- Test recommendation generation
- Test session persistence
- Verify data structures match spec

**Estimated Time:** 2-3 days

---

## Phase 3: Scheduler Integration with Tutor Feedback

### Objective
Make the scheduler prioritize weak subjects when creating study plans.

### Tasks

#### 3.1 Extend Scheduler Agent
**File:** `agents/scheduler_agent.py`

**Modifications:**
- Modify `generate_schedule()` signature:
  ```python
  def generate_schedule(
      user_input: str,
      weak_points: list[WeakPoint] | None = None,
      recommendations: SessionRecommendations | None = None
  ) -> dict
  ```
- Add prioritization logic:
  - Allocate more time to topics in weak_points
  - Follow suggested_focus_time from recommendations
  - Place harder topics during user's peak hours

#### 3.2 Tomorrow-Specific Planning
**Modifications:**
- Add date handling (use tomorrow's date)
- Ask user: "What time slots are you available tomorrow?"
- Parse natural language like "2-4pm and 7-9pm tomorrow"
- Display schedule with actual dates/times

#### 3.3 Testing
- Test with weak_points input
- Test without weak_points (fallback behavior)
- Test tomorrow date parsing
- Verify calendar sync includes correct dates

**Estimated Time:** 1 day

---

## Phase 4: Workflow Orchestration

### Objective
Create a unified workflow that connects all components according to spec.

### Tasks

#### 4.1 Create Workflow Orchestrator
**File:** `core/workflow_orchestrator.py`

**Implementation:**
```python
class WorkflowOrchestrator:
    def __init__(self):
        self.profile_store = UserProfileStore()
        self.motivator = MotivatorAgent()
        self.tutor = TutorChatbot()
        self.scheduler = SchedulerAgent()
        self.session_manager = SessionManager()

    def run_daily_workflow(self, user_id: str) -> DailyPlan:
        # Step 1: Profile check
        profile = self._ensure_profile(user_id)

        # Step 2: Daily motivation
        motivation = self._generate_motivation(profile)

        # Step 3: Tutoring session
        weak_points, recommendations = self._run_tutor_session(user_id)

        # Step 4: Schedule creation
        schedule = self._create_schedule(user_id, weak_points, recommendations)

        # Step 5: Calendar sync
        self._sync_to_calendar(schedule)

        return DailyPlan(
            motivation=motivation,
            session_summary=weak_points,
            recommendations=recommendations,
            schedule=schedule
        )
```

**Key Methods:**
- `_ensure_profile(user_id)` - Load or trigger onboarding
- `_generate_motivation(profile)` - Call motivator with persona
- `_run_tutor_session(user_id)` - Launch chatbot, wait for completion
- `_create_schedule(...)` - Generate tomorrow's plan
- `_sync_to_calendar(schedule)` - Push to Google Calendar

#### 4.2 Replace GraphManager Stub
**File:** `core/graph_manager.py`

**Decision:** Either replace with WorkflowOrchestrator or keep as wrapper.

**Option A:** Delete `graph_manager.py`, use `workflow_orchestrator.py` directly

**Option B:** Keep GraphManager as facade:
```python
class GraphManager:
    def __init__(self):
        self.orchestrator = WorkflowOrchestrator()

    def run_daily_cycle(self, user_id: str):
        return self.orchestrator.run_daily_workflow(user_id)
```

#### 4.3 Update Main Entry Point
**File:** `main.py`

**New CLI Structure:**
```
python main.py --workflow [user_id]     # Full integrated flow
python main.py --onboard [user_id]      # Force onboarding
python main.py --chat [user_id]         # Tutor only (existing)
python main.py --motivate [user_id]     # Motivator only (existing)
python main.py --schedule [user_id]     # Scheduler only (existing)
```

**Implementation:**
- Add `--workflow` mode
- Load profile at startup
- Call `WorkflowOrchestrator.run_daily_workflow()`
- Display results at each step
- Allow user to request additional motivations mid-flow

#### 4.4 Testing
- End-to-end test: new user flow
- End-to-end test: returning user flow
- Integration test: all agents communicate
- Verify data flows correctly between components

**Estimated Time:** 2-3 days

---

## Phase 5: Data Persistence & Polish

### Objective
Ensure all session data is saved and retrievable.

### Tasks

#### 5.1 Session History Storage
**Implementation:**
- Save conversation transcripts to JSON
- Store weak_points with timestamps
- Keep recommendation history
- Add retrieval methods

**Files to Create:**
- Session data in `data/sessions/{user_id}/`
- Weak points in `data/weak_points/{user_id}.json`
- Recommendations in `data/recommendations/{user_id}/`

#### 5.2 Conversation Persistence
**File:** `agents/tutor_chatbot.py`

**Modification:**
- Replace in-memory `ChatMessageHistory` with persistent storage
- Use SQLite or JSON for message history
- Load previous sessions on startup

#### 5.3 Analytics Methods (Optional)
**File:** `agents/user_profile.py` or new `core/analytics.py`

**Methods:**
- `get_progress_over_time(user_id)` -> dict
- `get_weak_points_trend(user_id)` -> dict
- `get_study_time_stats(user_id)` -> dict

#### 5.4 Configuration Management
**File:** `config/settings.yaml`

**Add configurations:**
- Default study session length
- Break intervals
- LLM models per agent
- Storage paths

#### 5.5 Testing
- Test session retrieval
- Test data persistence across restarts
- Verify no data loss

**Estimated Time:** 1-2 days

---

## Testing Strategy

### Unit Tests
- `test_onboarding.py` - Profile creation flow
- `test_weakness_analyzer.py` - Struggle detection
- `test_session_manager.py` - Session persistence
- `test_scheduler_integration.py` - Weak points prioritization
- `test_workflow_orchestrator.py` - Component integration

### Integration Tests
- `test_full_workflow.py` - End-to-end new user journey
- `test_returning_user.py` - Returning user with history
- `test_data_flow.py` - Verify data passes correctly between agents

### Manual Testing Checklist
- [ ] New user onboarding completes successfully
- [ ] Motivator displays personalized message
- [ ] Tutor chatbot starts with uploaded PDFs
- [ ] Weakness detection identifies struggle topics
- [ ] Recommendations are generated after session
- [ ] Scheduler receives weak_points and prioritizes them
- [ ] Tomorrow's schedule is created with correct dates
- [ ] Calendar sync works
- [ ] Session history is saved and retrievable
- [ ] Returning user loads profile correctly

---

## Implementation Order

### Week 1
- **Days 1-2:** Phase 1 - Onboarding System
- **Days 3-5:** Phase 2 - Weakness Tracking (core feature)

### Week 2
- **Day 1:** Phase 3 - Scheduler Integration
- **Days 2-4:** Phase 4 - Workflow Orchestration
- **Day 5:** Phase 5 - Data Persistence

### Week 3
- **Days 1-2:** Testing & Bug Fixes
- **Days 3-5:** Polish, documentation, edge cases

---

## Success Criteria

The implementation is complete when:

1. ✅ A new user can run `python main.py --workflow` and be guided through:
   - Profile creation (onboarding)
   - Daily motivation message
   - Tutoring session with PDFs
   - Weakness analysis
   - Tomorrow's schedule generation
   - Calendar sync

2. ✅ A returning user runs the same command and:
   - Profile loads automatically
   - Motivation is personalized to their persona
   - Tutor remembers previous weak points
   - Scheduler prioritizes weak subjects

3. ✅ All data is persisted:
   - User profiles
   - Session transcripts
   - Weak points history
   - Recommendations

4. ✅ The system matches the spec exactly:
   - 4 main components working together
   - Data flows as specified
   - Tomorrow-specific scheduling
   - Real quotes from personas

---

## Notes & Considerations

### Design Decisions
- **Storage:** Using JSON for simplicity (can migrate to SQLite later)
- **LLM Calls:** Each agent keeps its own LLM instance
- **Conversation Memory:** Switching from in-memory to persistent
- **Dates:** Using Python `datetime` for tomorrow calculation

### Future Enhancements (Post-MVP)
- Multi-day planning (weekly schedules)
- Spaced repetition algorithm
- Progress visualization dashboard
- Email notifications
- Mobile app integration
- Quiz generation (currently stubbed)

### Known Limitations
- Calendar integration requires Google OAuth setup
- Web scraping for quotes may hit rate limits
- LLM costs may increase with full workflow

---

## File Creation Checklist

**New Files to Create:**
- [ ] `agents/onboarding.py`
- [ ] `core/weakness_analyzer.py`
- [ ] `agents/session_manager.py`
- [ ] `core/workflow_orchestrator.py`
- [ ] `test_onboarding.py`
- [ ] `test_weakness_analyzer.py`
- [ ] `test_session_manager.py`
- [ ] `test_workflow_orchestrator.py`
- [ ] `test_full_workflow.py`

**Files to Modify:**
- [ ] `main.py` - Add workflow mode
- [ ] `agents/tutor_chatbot.py` - Add weakness tracking
- [ ] `agents/scheduler_agent.py` - Accept weak_points
- [ ] `core/graph_manager.py` - Replace or refactor

**Data Directories to Create:**
- [ ] `data/sessions/`
- [ ] `data/weak_points/`
- [ ] `data/recommendations/`

---

## Getting Started Tomorrow

1. Start with Phase 1 (Onboarding)
2. Create `agents/onboarding.py`
3. Test with manual profile creation
4. Move to Phase 2 once onboarding works
5. Iterate through phases sequentially

Good luck! 🚀