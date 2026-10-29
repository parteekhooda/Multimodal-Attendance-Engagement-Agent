import cv2
import numpy as np
import time
import math
import os
from config import Config

class VisionProcessor:
    def __init__(self, model_path=None):
        self.model_path = model_path or Config.YUNET_MODEL_PATH
        self.detector = None
        self.current_input_size = (640, 480)
        
        if os.path.exists(self.model_path):
            try:
                # Initialize OpenCV YuNet DNN face detector
                self.detector = cv2.FaceDetectorYN_create(
                    self.model_path,
                    "",
                    self.current_input_size,
                    score_threshold=0.55,
                    nms_threshold=0.3,
                    top_k=50
                )
            except Exception as e:
                print(f"Warning: Failed to initialize YuNet detector: {e}")
                self.detector = None
                
        # Centroid tracker state
        self.next_face_id = 1
        self.tracked_faces = {}
        self.max_disappeared = 15
        
    def process_frame(self, frame_bgr, privacy_blur=False):
        """
        Process a single BGR video frame.
        Returns:
            annotated_frame: Frame with cyber HUD overlays
            detected_students: List of detected student metrics
            summary_metrics: Aggregate vision statistics for this frame
        """
        if frame_bgr is None:
            return None, [], {}
            
        h, w = frame_bgr.shape[:2]
        
        # 1. Detect faces using YuNet DNN detector
        raw_faces = []
        if self.detector is not None:
            # Ensure detector input size matches current frame
            if self.current_input_size != (w, h):
                self.current_input_size = (w, h)
                self.detector.setInputSize((w, h))
                
            retval, detected = self.detector.detect(frame_bgr)
            if retval and detected is not None:
                raw_faces = detected
                
        # 2. Extract bounding boxes and centroids
        current_detections = []
        for face in raw_faces:
            # face: [x, y, w, h, rx, ry, lx, ly, nx, ny, rmx, rmy, lmx, lmy, score]
            x, y, fw, fh = int(face[0]), int(face[1]), int(face[2]), int(face[3])
            # Clamp to frame bounds
            x = max(0, min(x, w - 1))
            y = max(0, min(y, h - 1))
            fw = max(10, min(fw, w - x))
            fh = max(10, min(fh, h - y))
            
            cx = int(x + fw / 2)
            cy = int(y + fh / 2)
            current_detections.append((cx, cy, x, y, fw, fh, face))
            
        # 3. Spatial centroid tracking
        matched_tracks = self._update_tracks(current_detections)
        
        # 4. Analyze each detected face
        student_results = []
        total_attention = 0.0
        total_pose_alignment = 0.0
        drowsiness_count = 0
        
        annotated = frame_bgr.copy()
        
        for idx, (face_id, (cx, cy, x, y, fw, fh, face_landmarks)) in enumerate(matched_tracks):
            # Extract landmarks: right eye, left eye, nose, mouth
            rx, ry = float(face_landmarks[4]), float(face_landmarks[5])
            lx, ly = float(face_landmarks[6]), float(face_landmarks[7])
            nx, ny = float(face_landmarks[8]), float(face_landmarks[9])
            conf = float(face_landmarks[14])
            
            # A. Head Pose Estimation
            # Roll angle (eye tilt)
            dx = lx - rx
            dy = ly - ry
            roll_angle = math.degrees(math.atan2(dy, max(1.0, dx)))
            
            # Yaw approximation (horizontal nose position relative to eyes)
            d_right = abs(nx - rx)
            d_left = abs(lx - nx)
            yaw_ratio = (d_right - d_left) / max(1.0, (d_right + d_left)) # 0.0 when facing front
            
            # Pitch approximation (vertical nose relative to eye midpoint)
            eye_mid_y = (ry + ly) / 2.0
            pitch_ratio = (ny - eye_mid_y) / max(1.0, float(fh))
            
            # Head Pose Classification
            if abs(yaw_ratio) < 0.28 and 0.12 <= pitch_ratio <= 0.32:
                head_pose = "FORWARD"
                pose_alignment = 0.95
            elif pitch_ratio > 0.32:
                head_pose = "DOWN"
                pose_alignment = 0.35
            elif pitch_ratio < 0.12:
                head_pose = "UP"
                pose_alignment = 0.55
            else:
                head_pose = "TURNED"
                pose_alignment = 0.45
                
            # B. Visual Gaze & Attention Score (0.0 to 1.0)
            gaze_score = 1.0 - (abs(yaw_ratio) * 0.65) - (abs(roll_angle) / 45.0 * 0.25)
            if head_pose == "DOWN":
                gaze_score -= 0.40
            gaze_score = max(0.15, min(1.0, gaze_score))
            
            # C. Inactivity & Drowsiness Tracker
            track_info = self.tracked_faces.get(face_id, {})
            pose_hist = track_info.setdefault('pose_history', [])
            pose_hist.append((head_pose, gaze_score))
            if len(pose_hist) > 30:
                pose_hist.pop(0)
                
            # Drowsiness flag: continuous downward slump for > 15 checks
            down_count = sum(1 for p, g in pose_hist if p == "DOWN")
            is_drowsy = (len(pose_hist) >= 12 and (down_count / len(pose_hist)) > 0.65)
            if is_drowsy:
                drowsiness_count += 1
                
            # Composite visual engagement
            visual_engagement = 0.55 * gaze_score + 0.45 * pose_alignment
            if is_drowsy:
                visual_engagement = max(0.15, visual_engagement - 0.45)
                
            # Classroom seating zone approximation
            zone_x = "Left Wing" if cx < w*0.33 else ("Right Wing" if cx > w*0.66 else "Center Aisle")
            zone_depth = "Front Row" if fw > w*0.20 else ("Back Row" if fw < w*0.11 else "Middle Row")
            zone_label = f"{zone_depth} ({zone_x})"
            
            student_data = {
                'track_id': face_id,
                'bbox': [int(x), int(y), int(fw), int(fh)],
                'centroid': [int(cx), int(cy)],
                'gaze_score': round(float(gaze_score), 3),
                'head_pose': head_pose,
                'pose_alignment': round(float(pose_alignment), 3),
                'is_drowsy': bool(is_drowsy),
                'visual_engagement': round(float(visual_engagement), 3),
                'confidence': round(float(conf), 2),
                'zone': zone_label,
                'presence_frames': track_info.get('detections', 1),
                'active_seconds': round(track_info.get('active_duration', 1.0), 1)
            }
            student_results.append(student_data)
            total_attention += gaze_score
            total_pose_alignment += pose_alignment
            
            # D. Render HUD Overlay on Frame
            if privacy_blur:
                # Gaussian Blur on face bounding box
                face_sub = annotated[y:y+fh, x:x+fw]
                if face_sub.size > 0:
                    blurred = cv2.GaussianBlur(face_sub, (51, 51), 30)
                    annotated[y:y+fh, x:x+fw] = blurred
                box_color = (180, 180, 180)
            else:
                if is_drowsy:
                    box_color = (60, 60, 245) # Crimson Red
                elif visual_engagement >= 0.70:
                    box_color = (90, 220, 120) # Emerald Green
                elif visual_engagement >= 0.45:
                    box_color = (60, 200, 255) # Cyan
                else:
                    box_color = (60, 140, 255) # Amber/Orange
                    
            self._draw_hud_box(annotated, x, y, fw, fh, box_color, face_id, visual_engagement, head_pose, is_drowsy)
            
        face_count = len(student_results)
        avg_gaze = (total_attention / face_count) if face_count > 0 else 0.70
        avg_pose = (total_pose_alignment / face_count) if face_count > 0 else 0.75
        
        summary_metrics = {
            'face_count': face_count,
            'avg_gaze': round(float(avg_gaze), 3),
            'avg_pose_alignment': round(float(avg_pose), 3),
            'drowsiness_count': drowsiness_count,
            'timestamp': time.time()
        }
        
        return annotated, student_results, summary_metrics

    def _update_tracks(self, current_detections):
        now = time.time()
        matched = []
        
        if len(self.tracked_faces) == 0:
            for cx, cy, x, y, fw, fh, face in current_detections:
                fid = self.next_face_id
                self.next_face_id += 1
                self.tracked_faces[fid] = {
                    'centroid': (cx, cy),
                    'bbox': (x, y, fw, fh),
                    'first_seen': now,
                    'last_seen': now,
                    'detections': 1,
                    'disappeared': 0,
                    'active_duration': 0.1
                }
                matched.append((fid, (cx, cy, x, y, fw, fh, face)))
            return matched
            
        existing_ids = list(self.tracked_faces.keys())
        existing_centroids = [self.tracked_faces[fid]['centroid'] for fid in existing_ids]
        
        if len(current_detections) == 0:
            for fid in existing_ids:
                self.tracked_faces[fid]['disappeared'] += 1
                if self.tracked_faces[fid]['disappeared'] > self.max_disappeared:
                    del self.tracked_faces[fid]
            return []
            
        D = np.zeros((len(existing_centroids), len(current_detections)), dtype=np.float32)
        for i, (ecx, ecy) in enumerate(existing_centroids):
            for j, (cx, cy, x, y, fw, fh, face) in enumerate(current_detections):
                D[i, j] = math.hypot(ecx - cx, ecy - cy)
                
        rows = D.min(axis=1).argsort()
        cols = D.argmin(axis=1)[rows]
        used_rows, used_cols = set(), set()
        
        for r, c in zip(rows, cols):
            if r in used_rows or c in used_cols:
                continue
            if D[r, c] > 180:
                continue
                
            fid = existing_ids[r]
            cx, cy, x, y, fw, fh, face = current_detections[c]
            
            self.tracked_faces[fid]['centroid'] = (cx, cy)
            self.tracked_faces[fid]['bbox'] = (x, y, fw, fh)
            self.tracked_faces[fid]['last_seen'] = now
            self.tracked_faces[fid]['detections'] += 1
            self.tracked_faces[fid]['disappeared'] = 0
            self.tracked_faces[fid]['active_duration'] = now - self.tracked_faces[fid]['first_seen']
            
            matched.append((fid, (cx, cy, x, y, fw, fh, face)))
            used_rows.add(r)
            used_cols.add(c)
            
        unused_cols = set(range(len(current_detections))) - used_cols
        for c in unused_cols:
            cx, cy, x, y, fw, fh, face = current_detections[c]
            fid = self.next_face_id
            self.next_face_id += 1
            self.tracked_faces[fid] = {
                'centroid': (cx, cy),
                'bbox': (x, y, fw, fh),
                'first_seen': now,
                'last_seen': now,
                'detections': 1,
                'disappeared': 0,
                'active_duration': 0.1
            }
            matched.append((fid, (cx, cy, x, y, fw, fh, face)))
            
        unused_rows = set(range(len(existing_ids))) - used_rows
        for r in unused_rows:
            fid = existing_ids[r]
            self.tracked_faces[fid]['disappeared'] += 1
            if self.tracked_faces[fid]['disappeared'] > self.max_disappeared:
                del self.tracked_faces[fid]
                
        return matched

    def _draw_hud_box(self, img, x, y, w, h, color, face_id, engagement, pose, is_drowsy):
        line_len = int(min(w, h) * 0.25)
        thickness = 2
        
        # Corner brackets
        cv2.line(img, (x, y), (x + line_len, y), color, thickness)
        cv2.line(img, (x, y), (x, y + line_len), color, thickness)
        cv2.line(img, (x + w, y), (x + w - line_len, y), color, thickness)
        cv2.line(img, (x + w, y), (x + w, y + line_len), color, thickness)
        cv2.line(img, (x, y + h), (x + line_len, y + h), color, thickness)
        cv2.line(img, (x, y + h), (x, y + h - line_len), color, thickness)
        cv2.line(img, (x + w, y + h), (x + w - line_len, y + h), color, thickness)
        cv2.line(img, (x + w, y + h), (x + w, y + h - line_len), color, thickness)
        
        cv2.rectangle(img, (x, y), (x + w, y + h), color, 1, cv2.LINE_AA)
        
        badge_y = max(18, y - 8)
        badge_text = f"#{face_id} | {int(engagement * 100)}% Engaged"
        if is_drowsy:
            badge_text = f"#{face_id} | DROWSY SLUMP"
            
        (tw, th), _ = cv2.getTextSize(badge_text, cv2.FONT_HERSHEY_SIMPLEX, 0.44, 1)
        cv2.rectangle(img, (x, badge_y - th - 5), (x + tw + 8, badge_y + 3), (15, 20, 30), -1)
        cv2.rectangle(img, (x, badge_y - th - 5), (x + tw + 8, badge_y + 3), color, 1)
        cv2.putText(img, badge_text, (x + 4, badge_y - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.44, (255, 255, 255), 1, cv2.LINE_AA)
        
        sub_text = f"Pose: {pose}"
        (stw, sth), _ = cv2.getTextSize(sub_text, cv2.FONT_HERSHEY_SIMPLEX, 0.36, 1)
        cv2.rectangle(img, (x, y + h + 2), (x + stw + 6, y + h + sth + 5), (10, 15, 24), -1)
        cv2.putText(img, sub_text, (x + 3, y + h + sth + 2), cv2.FONT_HERSHEY_SIMPLEX, 0.36, color, 1, cv2.LINE_AA)
