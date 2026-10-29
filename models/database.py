import sqlite3
import os
from datetime import datetime
from config import Config

def get_db_connection():
    os.makedirs(Config.DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Registered Students Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        roll_no TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        email TEXT,
        department TEXT DEFAULT 'Computer Science & AI',
        avatar_seed TEXT,
        assigned_zone TEXT DEFAULT 'Middle Row',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 2. Classroom Sessions Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        course_code TEXT DEFAULT 'CS402 - Machine Learning & AI',
        instructor_name TEXT DEFAULT 'Dr. Evelyn Vance',
        start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        end_time TIMESTAMP,
        status TEXT DEFAULT 'ACTIVE', -- 'ACTIVE', 'COMPLETED'
        sustained_threshold_pct REAL DEFAULT 60.0,
        total_enrolled INTEGER DEFAULT 0,
        present_count INTEGER DEFAULT 0,
        late_count INTEGER DEFAULT 0,
        fleeting_count INTEGER DEFAULT 0,
        absent_count INTEGER DEFAULT 0,
        avg_engagement REAL DEFAULT 0.0,
        attention_drops_count INTEGER DEFAULT 0,
        interaction_peaks_count INTEGER DEFAULT 0
    )
    ''')
    
    # 3. Sustained Presence Attendance Records
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS attendance_records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL,
        student_id INTEGER,
        student_name TEXT NOT NULL,
        roll_no TEXT,
        first_seen TIMESTAMP,
        last_seen TIMESTAMP,
        detection_count INTEGER DEFAULT 0,
        total_session_intervals INTEGER DEFAULT 0,
        presence_ratio REAL DEFAULT 0.0, -- Sustained Presence %
        status TEXT DEFAULT 'ABSENT', -- 'PRESENT', 'LATE', 'FLEETING', 'ABSENT'
        confidence REAL DEFAULT 0.0,
        sustained_met INTEGER DEFAULT 0, -- 1 if >= sustained threshold
        notes TEXT,
        FOREIGN KEY (session_id) REFERENCES sessions(id),
        FOREIGN KEY (student_id) REFERENCES students(id)
    )
    ''')
    
    # 4. Multimodal Engagement Timeline
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS engagement_timeline (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        elapsed_sec INTEGER NOT NULL,
        composite_engagement REAL NOT NULL,
        head_pose_alignment REAL NOT NULL,
        gaze_attention REAL NOT NULL,
        audio_energy REAL NOT NULL,
        interaction_index REAL NOT NULL,
        active_faces INTEGER DEFAULT 0,
        drowsiness_count INTEGER DEFAULT 0,
        attention_drop_flag INTEGER DEFAULT 0,
        interaction_peak_flag INTEGER DEFAULT 0,
        FOREIGN KEY (session_id) REFERENCES sessions(id)
    )
    ''')
    
    # 5. Seating Zone Dynamics
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS zone_analytics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL,
        zone_name TEXT NOT NULL, -- 'Front Row', 'Middle Row', 'Back Row', 'Left Wing', 'Right Wing'
        avg_engagement REAL DEFAULT 0.0,
        gaze_alignment REAL DEFAULT 0.0,
        student_count INTEGER DEFAULT 0,
        status TEXT DEFAULT 'NORMAL', -- 'HIGH', 'NORMAL', 'DISENGAGED'
        FOREIGN KEY (session_id) REFERENCES sessions(id)
    )
    ''')
    
    # 6. AI Teaching Suggestions & Pedagogical Alerts
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS teaching_suggestions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        elapsed_sec INTEGER DEFAULT 0,
        category TEXT NOT NULL, -- 'Pacing', 'Engagement Dip', 'Interaction Peak', 'Fatigue/Drowsiness', 'Zone Disparity'
        severity TEXT NOT NULL, -- 'info', 'warning', 'critical', 'success'
        title TEXT NOT NULL,
        message TEXT NOT NULL,
        pedagogical_action TEXT NOT NULL,
        status TEXT DEFAULT 'active', -- 'active', 'acknowledged', 'dismissed'
        FOREIGN KEY (session_id) REFERENCES sessions(id)
    )
    ''')
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    print("Database initialized successfully at:", Config.DATABASE_PATH)
