import os
import cv2
import numpy as np
import base64
import time
import json
import io
import csv
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response, send_file

from config import Config
from models.database import get_db_connection, init_db
from models.seed_data import seed_database
from core.vision_processor import VisionProcessor
from core.audio_processor import AudioSignalProcessor
from core.multimodal_fusion import MultimodalFusionEngine
from core.agent_reasoning import AIAgentReasoningEngine

app = Flask(__name__)
app.config.from_object(Config)

# Ensure database and seed data are initialized
init_db()
seed_database()

# Initialize Core Processors
vision_processor = VisionProcessor()
audio_processor = AudioSignalProcessor()
fusion_engine = MultimodalFusionEngine()
agent_reasoning = AIAgentReasoningEngine()

# Active Session State
current_session = {
    'id': 1,
    'title': 'Deep Convolutional Neural Networks & Attention Mechanisms',
    'course_code': 'CS402 - Machine Learning & AI',
    'instructor_name': 'Dr. Evelyn Vance',
    'start_time': time.time(),
    'is_active': True,
    'privacy_mode': Config.DEFAULT_PRIVACY_BLUR,
    'sustained_threshold_pct': Config.SUSTAINED_PRESENCE_RATIO_THRESHOLD * 100.0,
    'last_update': time.time()
}

# Load registered students for live fusion engine
def refresh_roster():
    conn = get_db_connection()
    students = conn.execute("SELECT * FROM students ORDER BY roll_no ASC").fetchall()
    conn.close()
    student_list = [dict(s) for s in students]
    fusion_engine.reset_session(student_list)
    return student_list

active_roster = refresh_roster()

# ----------------- WEB ROUTES ----------------- #

@app.route('/')
def index():
    return render_template('index.html', session=current_session)

@app.route('/attendance')
def attendance():
    conn = get_db_connection()
    sessions = conn.execute("SELECT * FROM sessions ORDER BY id DESC").fetchall()
    latest_records = conn.execute('''
        SELECT * FROM attendance_records 
        WHERE session_id = ? 
        ORDER BY status ASC, roll_no ASC
    ''', (current_session['id'],)).fetchall()
    students = conn.execute("SELECT * FROM students ORDER BY roll_no ASC").fetchall()
    conn.close()
    return render_template(
        'attendance.html',
        session=current_session,
        sessions=sessions,
        records=latest_records,
        students=students
    )

@app.route('/engagement')
def engagement():
    conn = get_db_connection()
    zones = conn.execute("SELECT * FROM zone_analytics WHERE session_id = ?", (current_session['id'],)).fetchall()
    timeline = conn.execute('''
        SELECT * FROM engagement_timeline 
        WHERE session_id = ? 
        ORDER BY elapsed_sec ASC
    ''', (current_session['id'],)).fetchall()
    conn.close()
    return render_template(
        'engagement.html',
        session=current_session,
        zones=zones,
        timeline_count=len(timeline)
    )

@app.route('/suggestions')
def suggestions():
    conn = get_db_connection()
    sugs = conn.execute('''
        SELECT * FROM teaching_suggestions 
        WHERE session_id = ? 
        ORDER BY id DESC
    ''', (current_session['id'],)).fetchall()
    conn.close()
    return render_template(
        'suggestions.html',
        session=current_session,
        suggestions=sugs
    )

@app.route('/report/<int:session_id>')
def session_report(session_id):
    conn = get_db_connection()
    sess = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
    if not sess:
        conn.close()
        return "Session not found", 404
        
    records = conn.execute("SELECT * FROM attendance_records WHERE session_id = ? ORDER BY roll_no ASC", (session_id,)).fetchall()
    suggestions_list = conn.execute("SELECT * FROM teaching_suggestions WHERE session_id = ? ORDER BY elapsed_sec ASC", (session_id,)).fetchall()
    timeline = conn.execute("SELECT * FROM engagement_timeline WHERE session_id = ? ORDER BY elapsed_sec ASC", (session_id,)).fetchall()
    zones = conn.execute("SELECT * FROM zone_analytics WHERE session_id = ?", (session_id,)).fetchall()
    conn.close()
    
    return render_template(
        'session_report.html',
        session=sess,
        records=records,
        suggestions=suggestions_list,
        timeline=timeline,
        zones=zones
    )

@app.route('/settings')
def settings():
    return render_template('settings.html', config=Config, session=current_session)

# ----------------- API ENDPOINTS ----------------- #

@app.route('/api/process_frame', methods=['POST'])
def process_frame():
    """
    Receives base64 webcam frame and microphone audio metrics.
    Executes Vision Processing, Audio Processing, Multimodal Fusion,
    Sustained Presence Tracking, and AI Agent Reasoning in real time.
    """
    data = request.json or {}
    image_b64 = data.get('image', '')
    audio_vol = float(data.get('audio_volume', 0.2))
    audio_rms = float(data.get('audio_rms', 0.15))
    speech_ratio = float(data.get('speech_ratio', 0.3))
    privacy_blur = data.get('privacy_blur', current_session['privacy_mode'])
    
    if not image_b64:
        return jsonify({'error': 'No image data'}), 400
        
    try:
        # Decode base64 image
        if ',' in image_b64:
            image_b64 = image_b64.split(',')[1]
        img_bytes = base64.b64decode(image_b64)
        nparr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return jsonify({'error': 'Could not decode image'}), 400
            
        # 1. Vision Processing
        annotated_frame, detections, vision_summary = vision_processor.process_frame(
            frame, privacy_blur=privacy_blur
        )
        
        # 2. Audio Signal Processing
        audio_summary = audio_processor.process_audio_metrics(
            volume=audio_vol, rms=audio_rms, speech_ratio=speech_ratio
        )
        
        # 3. Multimodal Signal Fusion & Sustained Presence Tracking
        fusion_result = fusion_engine.fuse_signals(vision_summary, detections, audio_summary)
        
        # 4. AI Agent Reasoning Engine
        new_suggestions = agent_reasoning.evaluate_session_dynamics(
            current_session['id'], fusion_result, audio_summary
        )
        
        # Encode annotated image back to base64
        _, buffer = cv2.imencode('.jpg', annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        annotated_b64 = "data:image/jpeg;base64," + base64.b64encode(buffer).decode('utf-8')
        
        return jsonify({
            'annotated_image': annotated_b64,
            'detections': detections,
            'vision_summary': vision_summary,
            'audio_summary': audio_summary,
            'fusion': fusion_result,
            'new_suggestions': new_suggestions
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/simulation/step', methods=['POST'])
def simulation_step():
    """
    Generates a live multimodal telemetry step for presentation / offline demo mode.
    Simulates multi-student presence, head poses, attention dynamics, and audio patterns.
    """
    req_data = request.json or {}
    sim_mode = req_data.get('scenario', 'normal') # 'normal', 'monologue_drop', 'interactive_peak', 'drowsiness'
    step_num = req_data.get('step', fusion_engine.total_intervals + 1)
    
    # Generate realistic simulated multi-face vision dynamics based on mode
    num_students = 12
    detections = []
    zones = ['Front Row (Center Aisle)', 'Middle Row (Center Aisle)', 'Back Row (Center Aisle)', 'Middle Row (Left Wing)', 'Front Row (Right Wing)', 'Back Row (Left Wing)']
    
    # Dynamics variation
    if sim_mode == 'monologue_drop':
        base_gaze = 0.42
        base_pose = 0.48
        audio_energy = 0.45
        speech_state = 'SPEECH_MONOLOGUE'
        audio_interaction = 0.22
        monologue_sec = 820.0
        drowsy_candidates = [2, 5, 8]
    elif sim_mode == 'interactive_peak':
        base_gaze = 0.88
        base_pose = 0.92
        audio_energy = 0.72
        speech_state = 'SPEECH_INTERACTION'
        audio_interaction = 0.88
        monologue_sec = 0.0
        drowsy_candidates = []
    elif sim_mode == 'drowsiness':
        base_gaze = 0.35
        base_pose = 0.40
        audio_energy = 0.15
        speech_state = 'SILENCE_OR_STUDY'
        audio_interaction = 0.18
        monologue_sec = 400.0
        drowsy_candidates = [1, 3, 5, 7, 9]
    else: # normal
        # Oscillate smoothly
        osc = np.sin(step_num * 0.15)
        base_gaze = float(0.72 + osc * 0.12)
        base_pose = float(0.75 + osc * 0.10)
        audio_energy = float(0.35 + osc * 0.15)
        speech_state = 'SPEECH_MONOLOGUE' if osc < 0.2 else 'SPEECH_INTERACTION'
        audio_interaction = 0.45 if osc < 0.2 else 0.78
        monologue_sec = 320.0 if osc < 0.2 else 0.0
        drowsy_candidates = [4] if osc < -0.6 else []
        
    for i in range(num_students):
        is_drowsy = i in drowsy_candidates
        gaze = max(0.2, min(0.98, base_gaze + (np.random.rand() - 0.5) * 0.15))
        pose = max(0.3, min(0.98, base_pose + (np.random.rand() - 0.5) * 0.12))
        if is_drowsy:
            gaze = 0.25
            pose = 0.30
            
        vis_eng = max(0.15, min(1.0, 0.55 * gaze + 0.45 * pose - (0.4 if is_drowsy else 0.0)))
        
        detections.append({
            'track_id': i + 1,
            'bbox': [100 + (i % 4) * 160, 80 + (i // 4) * 130, 90, 90],
            'centroid': [145 + (i % 4) * 160, 125 + (i // 4) * 130],
            'gaze_score': round(float(gaze), 3),
            'head_pose': "DOWN" if is_drowsy else ("FORWARD" if pose > 0.7 else "PARTIAL_TURN"),
            'pose_alignment': round(float(pose), 3),
            'is_drowsy': is_drowsy,
            'visual_engagement': round(float(vis_eng), 3),
            'zone': zones[i % len(zones)],
            'presence_frames': step_num,
            'active_seconds': step_num * 2.0
        })
        
    vision_summary = {
        'face_count': num_students,
        'avg_gaze': round(float(np.mean([d['gaze_score'] for d in detections])), 3),
        'avg_pose_alignment': round(float(np.mean([d['pose_alignment'] for d in detections])), 3),
        'drowsiness_count': len(drowsy_candidates),
        'timestamp': time.time()
    }
    
    audio_summary = {
        'state': speech_state,
        'energy': round(float(audio_energy), 3),
        'interaction_index': round(float(audio_interaction), 3),
        'is_speaking': speech_state != 'SILENCE_OR_STUDY',
        'monologue_seconds': monologue_sec,
        'monologue_minutes': round(monologue_sec / 60.0, 1),
        'monologue_alert': monologue_sec > (Config.MAX_MONOLOGUE_MINUTES * 60),
        'timestamp': time.time()
    }
    
    fusion_result = fusion_engine.fuse_signals(vision_summary, detections, audio_summary)
    new_suggestions = agent_reasoning.evaluate_session_dynamics(
        current_session['id'], fusion_result, audio_summary
    )
    
    return jsonify({
        'detections': detections,
        'vision_summary': vision_summary,
        'audio_summary': audio_summary,
        'fusion': fusion_result,
        'new_suggestions': new_suggestions
    })

@app.route('/api/copilot/query', methods=['POST'])
def copilot_query():
    """
    Offline AI Teaching Copilot query endpoint.
    Answers queries using session context and pedagogical reasoning heuristics.
    """
    data = request.json or {}
    query = data.get('query', '')
    
    if not query:
        return jsonify({'error': 'No query provided'}), 400
        
    # Gather real-time context
    timeline = fusion_engine.timeline_records
    current_composite = timeline[-1]['composite_engagement'] if timeline else 74.5
    monologue_min = audio_processor.current_monologue_sec / 60.0
    
    roster_list = list(fusion_engine.roster_tracking.values())
    present_cnt = sum(1 for r in roster_list if r['status'] in ['PRESENT', 'LATE'])
    total_cnt = max(1, len(roster_list))
    presence_rate = round(present_cnt / total_cnt * 100.0, 1)
    
    context = {
        'composite_engagement': current_composite,
        'monologue_minutes': round(monologue_min, 1),
        'present_count': present_cnt,
        'total_enrolled': total_cnt,
        'sustained_presence_rate': presence_rate,
        'audio_state': audio_processor.history[-1][1] if audio_processor.history else 'SPEECH_MONOLOGUE'
    }
    
    reply = agent_reasoning.answer_copilot_query(query, context)
    
    return jsonify({
        'query': query,
        'response': reply,
        'timestamp': datetime.now().strftime('%H:%M:%S'),
        'context_snapshot': context
    })

@app.route('/api/session/start', methods=['POST'])
def start_session():
    data = request.json or {}
    title = data.get('title', 'Advanced AI & Pattern Recognition')
    course = data.get('course_code', 'CS402')
    instructor = data.get('instructor_name', 'Dr. Evelyn Vance')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO sessions (title, course_code, instructor_name, start_time, status, sustained_threshold_pct)
    VALUES (?, ?, ?, CURRENT_TIMESTAMP, 'ACTIVE', ?)
    ''', (title, course, instructor, Config.SUSTAINED_PRESENCE_RATIO_THRESHOLD * 100.0))
    session_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    current_session['id'] = session_id
    current_session['title'] = title
    current_session['course_code'] = course
    current_session['instructor_name'] = instructor
    current_session['start_time'] = time.time()
    current_session['is_active'] = True
    
    refresh_roster()
    
    return jsonify({'status': 'success', 'session': current_session})

@app.route('/api/session/stop', methods=['POST'])
def stop_session():
    """Concludes session, writes sustained attendance records and metrics to DB"""
    now = datetime.now()
    session_id = current_session['id']
    
    # Calculate final stats from fusion engine
    roster = list(fusion_engine.roster_tracking.values())
    present_count = sum(1 for r in roster if r['status'] == 'PRESENT')
    late_count = sum(1 for r in roster if r['status'] == 'LATE')
    fleeting_count = sum(1 for r in roster if r['status'] == 'FLEETING')
    absent_count = sum(1 for r in roster if r['status'] == 'ABSENT')
    
    timeline = fusion_engine.timeline_records
    avg_eng = round(float(np.mean([t['composite_engagement'] for t in timeline])), 1) if timeline else 72.0
    drops = fusion_engine.attention_drops_count
    peaks = fusion_engine.interaction_peaks_count
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Update session summary
    cursor.execute('''
    UPDATE sessions SET
        end_time = ?,
        status = 'COMPLETED',
        total_enrolled = ?,
        present_count = ?,
        late_count = ?,
        fleeting_count = ?,
        absent_count = ?,
        avg_engagement = ?,
        attention_drops_count = ?,
        interaction_peaks_count = ?
    WHERE id = ?
    ''', (
        now.strftime('%Y-%m-%d %H:%M:%S'),
        len(roster),
        present_count,
        late_count,
        fleeting_count,
        absent_count,
        avg_eng,
        drops,
        peaks,
        session_id
    ))
    
    # Save individual attendance records
    for r in roster:
        first_s = datetime.fromtimestamp(r['first_seen']).strftime('%Y-%m-%d %H:%M:%S') if r['first_seen'] else None
        last_s = datetime.fromtimestamp(r['last_seen']).strftime('%Y-%m-%d %H:%M:%S') if r['last_seen'] else None
        
        note = f"Sustained presence: {round(r['presence_ratio']*100, 1)}% ({r['detection_count']}/{fusion_engine.total_intervals} checks)"
        if r['status'] == 'FLEETING':
            note = f"Transient appearance ({round(r['presence_ratio']*100, 1)}%) - filtered out to prevent false attendance"
            
        cursor.execute('''
        INSERT INTO attendance_records (
            session_id, student_id, student_name, roll_no, first_seen, last_seen,
            detection_count, total_session_intervals, presence_ratio, status, confidence,
            sustained_met, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id,
            r.get('student_id'),
            r['name'],
            r['roll_no'],
            first_s,
            last_s,
            r['detection_count'],
            fusion_engine.total_intervals,
            r['presence_ratio'],
            r['status'],
            0.92 if r['sustained_met'] else 0.50,
            1 if r['sustained_met'] else 0,
            note
        ))
        
    conn.commit()
    conn.close()
    
    current_session['is_active'] = False
    return jsonify({'status': 'completed', 'session_id': session_id})

@app.route('/api/export/attendance_csv')
def export_attendance_csv():
    """Generates and serves CSV export of sustained attendance records"""
    session_id = request.args.get('session_id', current_session['id'], type=int)
    conn = get_db_connection()
    records = conn.execute('''
        SELECT ar.*, s.title as session_title, s.course_code
        FROM attendance_records ar
        JOIN sessions s ON s.id = ar.session_id
        WHERE ar.session_id = ?
        ORDER BY ar.status ASC, ar.roll_no ASC
    ''', (session_id,)).fetchall()
    conn.close()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'Session ID', 'Course Code', 'Student Roll No', 'Student Name',
        'Attendance Status', 'Sustained Presence Ratio (%)', 'Sustained Threshold Met',
        'First Seen', 'Last Seen', 'Detections Count', 'Verification Notes'
    ])
    
    for r in records:
        writer.writerow([
            r['session_id'],
            r['course_code'],
            r['roll_no'],
            r['student_name'],
            r['status'],
            round(r['presence_ratio'] * 100, 1),
            'YES' if r['sustained_met'] else 'NO',
            r['first_seen'] or 'N/A',
            r['last_seen'] or 'N/A',
            r['detection_count'],
            r['notes'] or ''
        ])
        
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=attendance_session_{session_id}.csv"}
    )

@app.route('/api/settings/update', methods=['POST'])
def update_settings():
    data = request.json or {}
    if 'privacy_mode' in data:
        current_session['privacy_mode'] = bool(data['privacy_mode'])
    if 'sustained_threshold' in data:
        thresh = float(data['sustained_threshold']) / 100.0
        Config.SUSTAINED_PRESENCE_RATIO_THRESHOLD = thresh
        fusion_engine.sustained_ratio_threshold = thresh
        current_session['sustained_threshold_pct'] = float(data['sustained_threshold'])
        
    return jsonify({'status': 'success', 'config': {
        'privacy_mode': current_session['privacy_mode'],
        'sustained_threshold_pct': current_session['sustained_threshold_pct']
    }})

if __name__ == '__main__':
    print("=" * 60)
    print("Multimodal Attendance & Engagement Agent - Offline Intelligence System")
    print("Running at: http://127.0.0.1:5000")
    print("=" * 60)
    app.run(host='127.0.0.1', port=5000, debug=True)
