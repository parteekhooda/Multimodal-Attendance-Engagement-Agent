import time
from config import Config

class AIAgentReasoningEngine:
    def __init__(self):
        # Alert cooldown tracker: category -> timestamp of last alert
        self.last_alert_time = {}
        self.cooldown_seconds = 45 # Minimum 45s between alerts of the same category
        self.generated_suggestions = []
        
    def evaluate_session_dynamics(self, session_id, fusion_result, audio_result):
        """
        Analyzes multimodal dynamics and generates context-aware pedagogical suggestions.
        Acts as an assistive decision-support agent for the educator.
        """
        now = time.time()
        new_suggestions = []
        
        snapshot = fusion_result.get('snapshot', {})
        zones = fusion_result.get('zones', [])
        roster_summary = fusion_result.get('roster_summary', {})
        
        composite_engagement = snapshot.get('composite_engagement', 70.0)
        drowsy_count = snapshot.get('drowsiness_count', 0)
        active_faces = snapshot.get('active_faces', 1)
        elapsed_sec = snapshot.get('elapsed_sec', 0)
        
        # 1. Monologue & Pacing Rule
        monologue_sec = audio_result.get('monologue_seconds', 0.0)
        if monologue_sec >= (Config.MAX_MONOLOGUE_MINUTES * 60):
            if self._can_trigger('Pacing', now):
                sug = {
                    'session_id': session_id,
                    'elapsed_sec': elapsed_sec,
                    'category': 'Pacing',
                    'severity': 'warning',
                    'title': 'Extended Instructor Monologue (12+ min)',
                    'message': f'You have been speaking continuously for {int(monologue_sec // 60)} minutes without student interaction. Attention naturally drops after 10-12 minutes of passive listening.',
                    'pedagogical_action': 'Pause slides and launch a 90-second "Think-Pair-Share" or ask: "Can someone summarize the core trade-off we just covered?"',
                    'timestamp': now,
                    'status': 'active'
                }
                new_suggestions.append(sug)
                self.last_alert_time['Pacing'] = now

        # 2. Attention Drop Rule
        if snapshot.get('attention_drop_flag'):
            if self._can_trigger('Engagement Dip', now):
                sug = {
                    'session_id': session_id,
                    'elapsed_sec': elapsed_sec,
                    'category': 'Engagement Dip',
                    'severity': 'critical',
                    'title': 'Classroom Attention Dip Detected',
                    'message': f'Average engagement has fallen to {composite_engagement}%. Multiple students have diverted gaze downward or away from the presentation.',
                    'pedagogical_action': 'Reset auditory attention: Change vocal pitch, insert a quick poll question, or conduct a cold-call check-in with a student.',
                    'timestamp': now,
                    'status': 'active'
                }
                new_suggestions.append(sug)
                self.last_alert_time['Engagement Dip'] = now

        # 3. Collaborative Interaction Peak Rule
        if snapshot.get('interaction_peak_flag'):
            if self._can_trigger('Interaction Peak', now):
                sug = {
                    'session_id': session_id,
                    'elapsed_sec': elapsed_sec,
                    'category': 'Interaction Peak',
                    'severity': 'success',
                    'title': 'High Collaborative Engagement Peak!',
                    'message': f'Classroom interaction index surged to {snapshot.get("interaction_index")}% with synchronized forward gaze and vocal exchanges.',
                    'pedagogical_action': 'Great discussion momentum! Allow 2 more minutes for students to debate the concept before consolidating key conclusions on the board.',
                    'timestamp': now,
                    'status': 'active'
                }
                new_suggestions.append(sug)
                self.last_alert_time['Interaction Peak'] = now

        # 4. Fatigue & Drowsiness Rule
        drowsy_ratio = (drowsy_count / max(1, active_faces))
        if drowsy_ratio >= Config.DROWSINESS_ALERT_THRESHOLD and active_faces > 0:
            if self._can_trigger('Fatigue/Drowsiness', now):
                sug = {
                    'session_id': session_id,
                    'elapsed_sec': elapsed_sec,
                    'category': 'Fatigue/Drowsiness',
                    'severity': 'warning',
                    'title': 'Physical Fatigue & Drowsiness Indicators',
                    'message': f'{int(drowsy_ratio * 100)}% of tracked participants exhibit low movement and downward head slump.',
                    'pedagogical_action': 'Classroom energy is flagging. Initiate a 30-second stand-up stretch or switch medium from lecture slides to a live interactive demo.',
                    'timestamp': now,
                    'status': 'active'
                }
                new_suggestions.append(sug)
                self.last_alert_time['Fatigue/Drowsiness'] = now

        # 5. Seating Zone Disparity Rule (e.g. Back Row disengaged)
        back_row = next((z for z in zones if 'Back Row' in z['zone_name']), None)
        front_row = next((z for z in zones if 'Front Row' in z['zone_name']), None)
        if back_row and front_row and front_row['avg_engagement'] > 0:
            disparity = front_row['avg_engagement'] - back_row['avg_engagement']
            if disparity >= 25.0 and back_row['avg_engagement'] < 50.0:
                if self._can_trigger('Zone Disparity', now):
                    sug = {
                        'session_id': session_id,
                        'elapsed_sec': elapsed_sec,
                        'category': 'Zone Disparity',
                        'severity': 'info',
                        'title': 'Seating Zone Attention Gap (Back Row Disengagement)',
                        'message': f'Back row engagement ({back_row["avg_engagement"]}%) is {int(disparity)}% lower than front row ({front_row["avg_engagement"]}%).',
                        'pedagogical_action': 'Physically migrate your teaching position towards the rear aisle or direct your next conceptual probe to the back row.',
                        'timestamp': now,
                        'status': 'active'
                    }
                    new_suggestions.append(sug)
                    self.last_alert_time['Zone Disparity'] = now

        for s in new_suggestions:
            self.generated_suggestions.insert(0, s)
            
        return new_suggestions

    def _can_trigger(self, category, current_time):
        last = self.last_alert_time.get(category, 0)
        return (current_time - last) > self.cooldown_seconds

    def answer_copilot_query(self, query, session_context):
        """
        AI Teaching Copilot reasoning engine.
        Answers educator's questions based on real-time and historical session telemetry.
        Runs 100% offline using heuristic pedagogical reasoning models.
        """
        q = query.lower().strip()
        comp_eng = session_context.get('composite_engagement', 72.0)
        monologue_min = session_context.get('monologue_minutes', 4.5)
        attendance_rate = session_context.get('sustained_presence_rate', 88.0)
        present_count = session_context.get('present_count', 12)
        total_students = session_context.get('total_enrolled', 15)
        
        # Pacing query
        if 'pace' in q or 'pacing' in q or 'speed' in q:
            if monologue_min > 10:
                return (
                    f"**Session Pacing Assessment: Monotonous / High Monologue Risk**\n\n"
                    f"- Current continuous monologue: **{monologue_min} minutes**.\n"
                    f"- Cognitive science shows learner attention degrades past 10 minutes of uninterrupted direct instruction.\n\n"
                    f"**Recommended Pedagogical Pivot:**\n"
                    f"1. **Break the cadence**: Ask: *'Before we move forward, write down one lingering ambiguity from this theorem.'*\n"
                    f"2. Give students 60 seconds of silent writing, then call on 2 volunteers.\n"
                    f"3. Your pacing will shift from didactic transmission to active cognitive processing."
                )
            else:
                return (
                    f"**Session Pacing Assessment: Balanced & Engaging**\n\n"
                    f"- Current monologue duration: **{monologue_min} minutes** (well within optimal limits).\n"
                    f"- Classroom engagement level: **{comp_eng}%**.\n\n"
                    f"**Next Move:** Maintain this momentum! Transition smoothly into your next learning objective in 3-4 minutes."
                )
                
        # Quiz / formative question query
        elif 'quiz' in q or 'question' in q or 'check' in q or 'poll' in q:
            return (
                f"**Formative Check-for-Understanding Blueprint**\n\n"
                f"Based on current classroom engagement ({comp_eng}%), here are 3 targeted questions to deploy right now:\n\n"
                f"1. **Conceptual Anchor (Low stakes, whole class):**\n"
                f"   *'Show of hands: If we double the learning rate, will the model converge faster or risk divergence? Explain why.'*\n\n"
                f"2. **Peer Discussion Probe (Think-Pair-Share - 2 min):**\n"
                f"   *'Turn to your neighbor and compare two alternative regularization techniques. Which one handles feature sparsity better?'*\n\n"
                f"3. **Synthesis Check (Cold call check):**\n"
                f"   *'Can someone in the middle row relate today\\'s loss function back to the bias-variance tradeoff we covered on Tuesday?'*"
            )
            
        # Struggling / disengaged students query
        elif 'who' in q or 'struggl' in q or 'disengag' in q or 'attention' in q or 'focus' in q:
            return (
                f"**Participant Attention & Engagement Diagnostics**\n\n"
                f"- **Overall Class Engagement**: **{comp_eng}%**\n"
                f"- **Sustained Presence**: **{present_count}/{total_students} ({attendance_rate}%)**\n\n"
                f"**Key Focus Areas:**\n"
                f"- **Back Row Learners**: Noticeable downward tilt (frequent device checking / notebook distraction).\n"
                f"- **Fleeting / Unconfirmed Attendees**: Ensure participants with under 60% sustained presence remain logged until session conclusion.\n\n"
                f"**Teacher Action**: Physically position yourself closer to the perimeter of the room to re-anchor visual attention without singling out individuals."
            )
            
        # Summary / Report query
        elif 'summar' in q or 'overview' in q or 'status' in q:
            return (
                f"**Real-Time Session Intelligence Summary**\n\n"
                f"- **Attendance Sustained Presence**: {attendance_rate}% ({present_count} verified present out of {total_students})\n"
                f"- **Multimodal Engagement Index**: **{comp_eng}%** (Normative range: 65% - 85%)\n"
                f"- **Current Instructor Monologue**: {monologue_min} minutes\n"
                f"- **Classroom Dynamic**: Active learning atmosphere with localized attention drops in peripheral seating.\n\n"
                f"**Pedagogical Tip for Closing**: Dedicate the final 5 minutes to an *Exit Ticket* (e.g. 1 key takeaway + 1 unanswered question) to solidify learning gains."
            )
            
        # Default smart response
        else:
            return (
                f"**AI Teaching Assistant Decision-Support**\n\n"
                f"I am continuously monitoring your classroom multimodal dynamics in real-time:\n"
                f"- **Classroom Engagement Index**: {comp_eng}%\n"
                f"- **Vocal Interaction Status**: {session_context.get('audio_state', 'Normal Dynamic')}\n"
                f"- **Verified Attendance**: {present_count}/{total_students} students\n\n"
                f"You can ask me to:\n"
                f"- *'Assess my current session pacing'*\n"
                f"- *'Generate 3 formative check questions'*\n"
                f"- *'Identify seating zones that need attention'*\n"
                f"- *'Suggest an active learning exercise for this stage'*."
            )
