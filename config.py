import os

class Config:
    # Base directory
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    MODELS_DIR = os.path.join(BASE_DIR, 'models')
    
    # Database
    DATABASE_PATH = os.path.join(DATA_DIR, 'classroom_intelligence.db')
    
    # Model Paths
    YUNET_MODEL_PATH = os.path.join(MODELS_DIR, 'face_detection_yunet_2023mar.onnx')
    FACE_CASCADE_PATH = os.path.join(MODELS_DIR, 'haarcascade_frontalface_default.xml')
    EYE_CASCADE_PATH = os.path.join(MODELS_DIR, 'haarcascade_eye.xml')
    
    # Scenario 1: Sustained Presence Thresholds
    # In live/production: e.g. 60% of total session time
    # In interactive demo mode: minimum 8 detections / 12 seconds sustained presence
    SUSTAINED_PRESENCE_RATIO_THRESHOLD = 0.60  # Must be present for >= 60% of checkpoints
    MIN_SUSTAINED_DETECTIONS = 6               # Minimum continuous detections for demo
    FLEETING_PRESENCE_MAX_RATIO = 0.25        # <= 25% presence tagged as Fleeting / Passer-by
    LATE_ARRIVAL_GRACE_PERIOD_SEC = 300       # 5 minutes late arrival cutoff
    
    # Scenario 2: Multimodal Engagement Weights
    # Composite Score = w_gaze * Gaze + w_pose * HeadPose + w_audio * Audio - w_penalty * Inactivity
    WEIGHT_GAZE = 0.35
    WEIGHT_HEAD_POSE = 0.25
    WEIGHT_AUDIO = 0.25
    WEIGHT_INACTIVITY_PENALTY = 0.15
    
    # Attention Drop & Peak Triggers
    ATTENTION_DROP_THRESHOLD = 45.0           # Score below 45% = Attention Drop
    ATTENTION_DROP_MIN_DURATION_SEC = 60      # Lasting for >= 1 min
    INTERACTION_PEAK_THRESHOLD = 75.0         # Score above 75% = High Engagement Peak
    
    # Scenario 3: AI Teaching Suggestions Config
    MAX_MONOLOGUE_MINUTES = 12                # Warning if teacher speaks continuously > 12 mins
    DROWSINESS_ALERT_THRESHOLD = 0.25         # If >= 25% of class displays drowsiness
    DISENGAGED_ZONE_THRESHOLD = 40.0          # If any classroom zone drops below 40%
    
    # Privacy Settings
    DEFAULT_PRIVACY_BLUR = False              # Anonymize/blur faces if requested
    OFFLINE_ONLY_MODE = True                  # Strictly 0 external cloud transmissions
    STORE_RAW_VIDEO = False                   # Do NOT record raw video feeds, extract features only
