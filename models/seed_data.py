import sqlite3
import time
from datetime import datetime, timedelta
from config import Config
from models.database import get_db_connection, init_db

def seed_database():
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if students already exist
    cursor.execute("SELECT COUNT(*) FROM students")
    if cursor.fetchone()[0] > 0:
        print("Database already contains student data.")
        conn.close()
        return

    print("Seeding initial student roster and historical classroom sessions...")
    
    # 1. Registered Student Roster
    students_data = [
        ('2024-AI-101', 'Aarav Sharma', 'aarav.sharma@edu.in', 'AI & Data Science', 'Middle Row', 'aarav'),
        ('2024-AI-102', 'Ananya Iyer', 'ananya.iyer@edu.in', 'AI & Data Science', 'Front Row', 'ananya'),
        ('2024-AI-103', 'Rohan Verma', 'rohan.verma@edu.in', 'AI & Data Science', 'Front Row', 'rohan'),
        ('2024-AI-104', 'Sneha Patel', 'sneha.patel@edu.in', 'AI & Data Science', 'Middle Row', 'sneha'),
        ('2024-AI-105', 'Vikram Malhotra', 'vikram.m@edu.in', 'AI & Data Science', 'Back Row', 'vikram'),
        ('2024-AI-106', 'Priya Deshmukh', 'priya.d@edu.in', 'AI & Data Science', 'Middle Row', 'priya'),
        ('2024-AI-107', 'Kabir Mehta', 'kabir.mehta@edu.in', 'AI & Data Science', 'Back Row', 'kabir'),
        ('2024-AI-108', 'Ishita Sengupta', 'ishita.s@edu.in', 'AI & Data Science', 'Front Row', 'ishita'),
        ('2024-AI-109', 'Aditya Joshi', 'aditya.joshi@edu.in', 'AI & Data Science', 'Back Row', 'aditya'),
        ('2024-AI-110', 'Neha Ranganathan', 'neha.r@edu.in', 'AI & Data Science', 'Middle Row', 'neha'),
        ('2024-AI-111', 'Arjun Nambiar', 'arjun.n@edu.in', 'AI & Data Science', 'Front Row', 'arjun'),
        ('2024-AI-112', 'Tanvi Kulkarni', 'tanvi.k@edu.in', 'AI & Data Science', 'Middle Row', 'tanvi'),
        ('2024-AI-113', 'Devendra Rao', 'devendra.rao@edu.in', 'AI & Data Science', 'Back Row', 'devendra'),
        ('2024-AI-114', 'Rhea Chakraborty', 'rhea.c@edu.in', 'AI & Data Science', 'Front Row', 'rhea')
    ]
    
    cursor.executemany('''
    INSERT INTO students (roll_no, name, email, department, assigned_zone, avatar_seed)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', students_data)
    
    # 2. Historical Completed Session
    start_time = datetime.now() - timedelta(hours=2)
    end_time = start_time + timedelta(minutes=50)
    
    cursor.execute('''
    INSERT INTO sessions (
        title, course_code, instructor_name, start_time, end_time, status,
        sustained_threshold_pct, total_enrolled, present_count, late_count,
        fleeting_count, absent_count, avg_engagement, attention_drops_count, interaction_peaks_count
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        'Deep Convolutional Neural Networks & Attention Mechanisms',
        'CS402 - Machine Learning & AI',
        'Dr. Evelyn Vance',
        start_time.strftime('%Y-%m-%d %H:%M:%S'),
        end_time.strftime('%Y-%m-%d %H:%M:%S'),
        'ACTIVE',
        60.0,
        14,
        11, # Present
        1,  # Late
        1,  # Fleeting (Passer-by eliminated)
        1,  # Absent
        74.5,
        2,
        3
    ))
    session_id = cursor.lastrowid
    
    # 3. Attendance Records with Sustained Presence Evaluation
    # Shows Scenario 1 working clearly:
    attendance_data = [
        # (session_id, student_id, name, roll_no, first_seen, last_seen, count, total, ratio, status, conf, sustained_met, notes)
        (session_id, 1, 'Aarav Sharma', '2024-AI-101', start_time + timedelta(minutes=1), end_time, 280, 300, 0.933, 'PRESENT', 0.96, 1, 'Sustained presence verified (93.3% of lecture)'),
        (session_id, 2, 'Ananya Iyer', '2024-AI-102', start_time + timedelta(seconds=30), end_time, 290, 300, 0.967, 'PRESENT', 0.98, 1, 'High visual engagement, active participation'),
        (session_id, 3, 'Rohan Verma', '2024-AI-103', start_time + timedelta(minutes=2), end_time, 265, 300, 0.883, 'PRESENT', 0.94, 1, 'Sustained presence verified'),
        (session_id, 4, 'Sneha Patel', '2024-AI-104', start_time + timedelta(minutes=1), end_time - timedelta(minutes=2), 250, 300, 0.833, 'PRESENT', 0.91, 1, 'Sustained presence verified'),
        (session_id, 5, 'Vikram Malhotra', '2024-AI-105', start_time + timedelta(minutes=3), end_time, 210, 300, 0.700, 'PRESENT', 0.86, 1, 'Periodic downward gaze (notebook notes)'),
        (session_id, 6, 'Priya Deshmukh', '2024-AI-106', start_time + timedelta(minutes=1), end_time, 275, 300, 0.917, 'PRESENT', 0.95, 1, 'Sustained presence verified'),
        (session_id, 7, 'Kabir Mehta', '2024-AI-107', start_time + timedelta(minutes=9), end_time, 215, 300, 0.717, 'LATE', 0.89, 1, 'Arrived at Minute 9 (Late Arrival Grace Cutoff exceeded)'),
        (session_id, 8, 'Ishita Sengupta', '2024-AI-108', start_time + timedelta(seconds=45), end_time, 285, 300, 0.950, 'PRESENT', 0.97, 1, 'Continuous presence & high interaction'),
        (session_id, 9, 'Aditya Joshi', '2024-AI-109', start_time + timedelta(minutes=2), end_time, 230, 300, 0.767, 'PRESENT', 0.88, 1, 'Sustained presence verified'),
        (session_id, 10, 'Neha Ranganathan', '2024-AI-110', start_time + timedelta(minutes=1), end_time, 270, 300, 0.900, 'PRESENT', 0.94, 1, 'Sustained presence verified'),
        (session_id, 11, 'Arjun Nambiar', '2024-AI-111', start_time + timedelta(minutes=1), end_time, 260, 300, 0.867, 'PRESENT', 0.93, 1, 'Sustained presence verified'),
        (session_id, 12, 'Tanvi Kulkarni', '2024-AI-112', start_time + timedelta(minutes=2), end_time, 245, 300, 0.817, 'PRESENT', 0.90, 1, 'Sustained presence verified'),
        (session_id, 13, 'Devendra Rao', '2024-AI-113', None, None, 0, 300, 0.000, 'ABSENT', 0.00, 0, 'No presence detected in session'),
        (session_id, 14, 'Rhea Chakraborty', '2024-AI-114', start_time + timedelta(minutes=1), end_time, 280, 300, 0.933, 'PRESENT', 0.97, 1, 'Sustained presence verified'),
        # Fleeting Visitor (Passer-by eliminated from false positive)
        (session_id, None, 'Visitor / Staff Corridor (Guest)', 'GUEST-TEMP-09', start_time + timedelta(minutes=18), start_time + timedelta(minutes=19, seconds=10), 12, 300, 0.040, 'FLEETING', 0.62, 0, 'Transient appearance (70s) - filtered out to prevent false attendance')
    ]
    
    cursor.executemany('''
    INSERT INTO attendance_records (
        session_id, student_id, student_name, roll_no, first_seen, last_seen,
        detection_count, total_session_intervals, presence_ratio, status, confidence,
        sustained_met, notes
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', attendance_data)
    
    # 4. Realistic Engagement Timeline Points (every 2.5 minutes over 50 minutes = 20 points)
    timeline_data = [
        # (session_id, timestamp, elapsed_sec, comp_eng, pose, gaze, audio, interact_idx, faces, drowsy, drop_flag, peak_flag)
        (session_id, start_time + timedelta(minutes=0), 0, 72.0, 75.0, 70.0, 35.0, 30.0, 12, 0, 0, 0),
        (session_id, start_time + timedelta(minutes=2.5), 150, 78.5, 82.0, 76.0, 40.0, 45.0, 12, 0, 0, 0),
        (session_id, start_time + timedelta(minutes=5.0), 300, 81.0, 85.0, 80.0, 50.0, 60.0, 13, 0, 0, 0),
        (session_id, start_time + timedelta(minutes=7.5), 450, 84.0, 88.0, 82.0, 65.0, 78.0, 13, 0, 0, 1), # Interaction Peak (Concept Q&A)
        (session_id, start_time + timedelta(minutes=10.0), 600, 76.0, 80.0, 74.0, 45.0, 40.0, 13, 0, 0, 0),
        (session_id, start_time + timedelta(minutes=12.5), 750, 71.0, 75.0, 68.0, 30.0, 35.0, 13, 1, 0, 0),
        (session_id, start_time + timedelta(minutes=15.0), 900, 64.0, 70.0, 62.0, 25.0, 25.0, 13, 2, 0, 0),
        (session_id, start_time + timedelta(minutes=17.5), 1050, 52.0, 58.0, 50.0, 20.0, 20.0, 13, 3, 0, 0),
        (session_id, start_time + timedelta(minutes=20.0), 1200, 42.0, 48.0, 40.0, 18.0, 18.0, 13, 4, 1, 0), # Attention Drop (Monologue)
        (session_id, start_time + timedelta(minutes=22.5), 1350, 43.5, 50.0, 42.0, 20.0, 20.0, 13, 4, 1, 0), # Attention Drop
        (session_id, start_time + timedelta(minutes=25.0), 1500, 75.0, 80.0, 72.0, 60.0, 70.0, 13, 1, 0, 0), # Teacher Pivoted to Poll!
        (session_id, start_time + timedelta(minutes=27.5), 1650, 86.5, 90.0, 85.0, 75.0, 88.0, 13, 0, 0, 1), # High Interaction Peak (Debate)
        (session_id, start_time + timedelta(minutes=30.0), 1800, 83.0, 86.0, 82.0, 65.0, 75.0, 13, 0, 0, 1),
        (session_id, start_time + timedelta(minutes=32.5), 1950, 78.0, 82.0, 76.0, 45.0, 48.0, 13, 0, 0, 0),
        (session_id, start_time + timedelta(minutes=35.0), 2100, 73.0, 78.0, 72.0, 38.0, 40.0, 13, 1, 0, 0),
        (session_id, start_time + timedelta(minutes=37.5), 2250, 69.0, 74.0, 68.0, 32.0, 35.0, 13, 2, 0, 0),
        (session_id, start_time + timedelta(minutes=40.0), 2400, 65.0, 70.0, 64.0, 30.0, 30.0, 13, 2, 0, 0),
        (session_id, start_time + timedelta(minutes=42.5), 2550, 74.0, 78.0, 74.0, 52.0, 62.0, 13, 1, 0, 0), # Live coding demo
        (session_id, start_time + timedelta(minutes=45.0), 2700, 80.0, 84.0, 78.0, 68.0, 76.0, 13, 0, 0, 1), # Q&A summary
        (session_id, start_time + timedelta(minutes=47.5), 2850, 77.0, 80.0, 75.0, 55.0, 60.0, 13, 0, 0, 0),
        (session_id, start_time + timedelta(minutes=50.0), 3000, 79.0, 82.0, 78.0, 50.0, 55.0, 13, 0, 0, 0)
    ]
    
    cursor.executemany('''
    INSERT INTO engagement_timeline (
        session_id, timestamp, elapsed_sec, composite_engagement, head_pose_alignment,
        gaze_attention, audio_energy, interaction_index, active_faces, drowsiness_count,
        attention_drop_flag, interaction_peak_flag
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', timeline_data)
    
    # 5. Zone Analytics
    zone_data = [
        (session_id, 'Front Row', 84.2, 88.0, 5, 'HIGH'),
        (session_id, 'Middle Row', 75.1, 78.5, 5, 'NORMAL'),
        (session_id, 'Back Row', 58.4, 62.0, 4, 'DISENGAGED')
    ]
    cursor.executemany('''
    INSERT INTO zone_analytics (session_id, zone_name, avg_engagement, gaze_alignment, student_count, status)
    VALUES (?, ?, ?, ?, ?, ?)
    ''', zone_data)
    
    # 6. Seeded AI Teaching Suggestions
    suggestions_data = [
        (
            session_id,
            (start_time + timedelta(minutes=19)).strftime('%Y-%m-%d %H:%M:%S'),
            1140,
            'Pacing',
            'warning',
            'Extended Monologue Detected (15 min uninterrupted speech)',
            'Instructor vocal stream active without student interchange for 15 minutes. Engagement dropped from 81% down to 52%.',
            'Pause lecture slides. Launch a 90-second Think-Pair-Share exercise on CNN kernel convolutions.',
            'acknowledged'
        ),
        (
            session_id,
            (start_time + timedelta(minutes=21)).strftime('%Y-%m-%d %H:%M:%S'),
            1260,
            'Engagement Dip',
            'critical',
            'Attention Drop Triggered (Composite Engagement 42%)',
            'Sharp 39% dip in visual gaze and head pose alignment across 6 participants in back/middle rows.',
            'Deploy an active learning check: Pose a formative multiple-choice poll or direct a question to the back row.',
            'acknowledged'
        ),
        (
            session_id,
            (start_time + timedelta(minutes=28)).strftime('%Y-%m-%d %H:%M:%S'),
            1680,
            'Interaction Peak',
            'success',
            'High Collaborative Discussion Synergy (86.5%)',
            'Interactive debate peak achieved! Multimodal audio bursts and aligned facial gazes indicate deep active processing.',
            'Maintain discussion flow for 90 seconds, then synthesize key student counter-arguments on the blackboard.',
            'acknowledged'
        ),
        (
            session_id,
            (start_time + timedelta(minutes=38)).strftime('%Y-%m-%d %H:%M:%S'),
            2280,
            'Zone Disparity',
            'info',
            'Seating Zone Disparity: Back Row Lagging (58.4% vs 84.2%)',
            'Learners in back row showing downward head orientation and reduced eye contact compared to front row.',
            'Physically teach from the middle/rear aisle to re-engage peripheral learners and bridge spatial attention.',
            'active'
        )
    ]
    cursor.executemany('''
    INSERT INTO teaching_suggestions (
        session_id, timestamp, elapsed_sec, category, severity, title, message, pedagogical_action, status
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', suggestions_data)
    
    conn.commit()
    conn.close()
    print("Database successfully seeded with realistic students, session dynamics, and AI pedagogical actions!")

if __name__ == '__main__':
    seed_database()
