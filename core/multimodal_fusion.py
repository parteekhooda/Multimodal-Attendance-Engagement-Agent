import time
from config import Config

class MultimodalFusionEngine:
    def __init__(self, sustained_ratio_threshold=None):
        self.sustained_ratio_threshold = sustained_ratio_threshold or Config.SUSTAINED_PRESENCE_RATIO_THRESHOLD
        self.session_start_time = time.time()
        self.total_intervals = 0
        
        # Student tracker: roll_no/id -> {first_seen, last_seen, detection_count, last_score, zone, name}
        self.roster_tracking = {}
        
        # Anomaly tracking
        self.consecutive_low_attention = 0
        self.attention_drops_count = 0
        self.interaction_peaks_count = 0
        
        # Rolling timeline history
        self.timeline_records = []
        
    def reset_session(self, enrolled_students=None):
        """Resets or initializes tracker for a new session"""
        self.session_start_time = time.time()
        self.total_intervals = 0
        self.consecutive_low_attention = 0
        self.attention_drops_count = 0
        self.interaction_peaks_count = 0
        self.timeline_records = []
        self.roster_tracking = {}
        
        if enrolled_students:
            for s in enrolled_students:
                self.roster_tracking[s['roll_no']] = {
                    'student_id': s['id'],
                    'name': s['name'],
                    'roll_no': s['roll_no'],
                    'department': s.get('department', 'Computer Science & AI'),
                    'first_seen': None,
                    'last_seen': None,
                    'detection_count': 0,
                    'presence_ratio': 0.0,
                    'status': 'ABSENT',
                    'sustained_met': False,
                    'avg_engagement': 0.0,
                    'last_engagement': 0.0,
                    'zone': s.get('assigned_zone', 'Middle Row'),
                    'drowsiness_count': 0
                }
                
    def fuse_signals(self, vision_summary, student_detections, audio_summary):
        """
        Fuses multimodal signals from Vision and Audio into unified engagement metrics,
        and updates sustained presence attendance logs.
        """
        self.total_intervals += 1
        now = time.time()
        elapsed_sec = int(now - self.session_start_time)
        
        # 1. Component Extraction
        avg_gaze = vision_summary.get('avg_gaze', 0.70)
        avg_pose = vision_summary.get('avg_pose_alignment', 0.75)
        drowsy_count = vision_summary.get('drowsiness_count', 0)
        face_count = vision_summary.get('face_count', 0)
        
        audio_energy = audio_summary.get('energy', 0.20)
        interaction_idx = audio_summary.get('interaction_index', 0.30)
        
        # 2. Multimodal Fusion Formula
        # Inactivity/drowsiness penalty
        penalty = 0.0
        if face_count > 0 and drowsy_count > 0:
            penalty = (drowsy_count / face_count) * Config.WEIGHT_INACTIVITY_PENALTY
            
        composite_score = (
            Config.WEIGHT_GAZE * avg_gaze +
            Config.WEIGHT_HEAD_POSE * avg_pose +
            Config.WEIGHT_AUDIO * interaction_idx -
            penalty
        ) * 100.0
        
        composite_score = max(5.0, min(100.0, round(composite_score, 1)))
        
        # 3. Detect Anomalies (Scenario 2)
        is_attention_drop = False
        is_interaction_peak = False
        
        if composite_score < Config.ATTENTION_DROP_THRESHOLD:
            self.consecutive_low_attention += 1
            if self.consecutive_low_attention >= 3:
                is_attention_drop = True
                self.attention_drops_count += 1
        else:
            self.consecutive_low_attention = 0
            
        if composite_score >= Config.INTERACTION_PEAK_THRESHOLD or (interaction_idx >= 0.75 and composite_score >= 65.0):
            is_interaction_peak = True
            self.interaction_peaks_count += 1
            
        # 4. Update Sustained Presence Attendance Roster (Scenario 1)
        # Match detections to roster or create unassigned entries
        detected_keys = set()
        roster_keys = list(self.roster_tracking.keys())
        
        for idx, det in enumerate(student_detections):
            # Map by index or track_id to enrolled students
            if idx < len(roster_keys):
                student_key = roster_keys[idx]
            else:
                student_key = f"GUEST-{det['track_id']}"
                if student_key not in self.roster_tracking:
                    self.roster_tracking[student_key] = {
                        'student_id': None,
                        'name': f"Visitor / Guest #{det['track_id']}",
                        'roll_no': student_key,
                        'department': 'Auditor / Guest',
                        'first_seen': None,
                        'last_seen': None,
                        'detection_count': 0,
                        'presence_ratio': 0.0,
                        'status': 'ABSENT',
                        'sustained_met': False,
                        'avg_engagement': 0.0,
                        'last_engagement': 0.0,
                        'zone': det.get('zone', 'Middle Row'),
                        'drowsiness_count': 0
                    }
                    
            rec = self.roster_tracking[student_key]
            detected_keys.add(student_key)
            
            if rec['first_seen'] is None:
                rec['first_seen'] = now
            rec['last_seen'] = now
            rec['detection_count'] += 1
            
            # Individual engagement computation
            ind_engagement = det.get('visual_engagement', 0.7) * 80 + interaction_idx * 20
            rec['last_engagement'] = round(ind_engagement, 1)
            rec['avg_engagement'] = round(
                (rec['avg_engagement'] * (rec['detection_count'] - 1) + ind_engagement) / rec['detection_count'], 1
            )
            rec['zone'] = det.get('zone', rec['zone'])
            if det.get('is_drowsy'):
                rec['drowsiness_count'] += 1
                
        # Re-evaluate sustained presence status for ALL roster students
        present_count = 0
        late_count = 0
        fleeting_count = 0
        absent_count = 0
        
        for key, rec in self.roster_tracking.items():
            if self.total_intervals > 0:
                rec['presence_ratio'] = round((rec['detection_count'] / self.total_intervals), 3)
            else:
                rec['presence_ratio'] = 0.0
                
            # Sustained presence classification logic:
            # - Must exceed threshold (e.g. 60% of checks or minimum detection count)
            # - Transient appearances (<= 25%) are categorized as FLEETING (passers-by)
            if rec['detection_count'] == 0:
                rec['status'] = 'ABSENT'
                rec['sustained_met'] = False
                absent_count += 1
            elif rec['presence_ratio'] <= Config.FLEETING_PRESENCE_MAX_RATIO and rec['detection_count'] < Config.MIN_SUSTAINED_DETECTIONS:
                rec['status'] = 'FLEETING'
                rec['sustained_met'] = False
                fleeting_count += 1
            elif rec['presence_ratio'] >= self.sustained_ratio_threshold or rec['detection_count'] >= Config.MIN_SUSTAINED_DETECTIONS:
                rec['sustained_met'] = True
                # Check for late arrival
                if rec['first_seen'] and (rec['first_seen'] - self.session_start_time) > Config.LATE_ARRIVAL_GRACE_PERIOD_SEC:
                    rec['status'] = 'LATE'
                    late_count += 1
                else:
                    rec['status'] = 'PRESENT'
                    present_count += 1
            else:
                # In-progress / Partial
                if self.total_intervals < Config.MIN_SUSTAINED_DETECTIONS * 2:
                    rec['status'] = 'PRESENT' # early in session
                    rec['sustained_met'] = True
                    present_count += 1
                else:
                    rec['status'] = 'PARTIAL'
                    absent_count += 1
                    
        # 5. Zone Analytics
        zone_stats = {
            'Front Row': {'sum': 0.0, 'count': 0},
            'Middle Row': {'sum': 0.0, 'count': 0},
            'Back Row': {'sum': 0.0, 'count': 0}
        }
        for det in student_detections:
            z = det.get('zone', 'Middle Row')
            depth = 'Front Row' if 'Front' in z else ('Back Row' if 'Back' in z else 'Middle Row')
            zone_stats[depth]['sum'] += det.get('visual_engagement', 0.7) * 100.0
            zone_stats[depth]['count'] += 1
            
        zones_summary = []
        for z_name, z_val in zone_stats.items():
            z_avg = round(z_val['sum'] / z_val['count'], 1) if z_val['count'] > 0 else composite_score
            status = 'DISENGAGED' if z_avg < Config.DISENGAGED_ZONE_THRESHOLD else ('HIGH' if z_avg > 75 else 'NORMAL')
            zones_summary.append({
                'zone_name': z_name,
                'avg_engagement': z_avg,
                'student_count': z_val['count'],
                'status': status
            })
            
        # Snapshot for time-series charts
        snapshot = {
            'timestamp': now,
            'elapsed_sec': elapsed_sec,
            'composite_engagement': composite_score,
            'head_pose_alignment': round(avg_pose * 100.0, 1),
            'gaze_attention': round(avg_gaze * 100.0, 1),
            'audio_energy': round(audio_energy * 100.0, 1),
            'interaction_index': round(interaction_idx * 100.0, 1),
            'active_faces': face_count,
            'drowsiness_count': drowsy_count,
            'attention_drop_flag': is_attention_drop,
            'interaction_peak_flag': is_interaction_peak
        }
        
        self.timeline_records.append(snapshot)
        if len(self.timeline_records) > 600:
            self.timeline_records.pop(0)
            
        return {
            'snapshot': snapshot,
            'roster_summary': {
                'total_enrolled': len(self.roster_tracking),
                'present_count': present_count,
                'late_count': late_count,
                'fleeting_count': fleeting_count,
                'absent_count': absent_count,
                'sustained_presence_rate': round((present_count + late_count) / max(1, len(self.roster_tracking)) * 100.0, 1)
            },
            'zones': zones_summary,
            'roster_list': list(self.roster_tracking.values())
        }
