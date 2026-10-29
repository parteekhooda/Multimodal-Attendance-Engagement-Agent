import time
from collections import deque
from config import Config

class AudioSignalProcessor:
    def __init__(self, window_size=30):
        # Rolling buffer of audio energy and speech classifications
        self.history = deque(maxlen=window_size)
        
        # Monologue & interaction tracking
        self.monologue_start_time = None
        self.current_monologue_sec = 0.0
        self.last_interaction_time = time.time()
        self.interaction_peaks_count = 0
        
    def process_audio_metrics(self, volume=0.0, rms=0.0, spectral_entropy=0.5, speech_ratio=0.0):
        """
        Processes normalized audio metrics received from client microphone analyzer
        or audio signal stream.
        
        Args:
            volume: 0.0 to 1.0 amplitude
            rms: Root-mean-square energy (normalized 0.0 - 1.0)
            spectral_entropy: Measure of spectral distribution
            speech_ratio: Percentage of frame containing voiced speech
            
        Returns:
            dict containing processed audio dynamics
        """
        now = time.time()
        energy = max(0.0, min(1.0, float(rms or volume)))
        
        # Audio state classification
        if energy < 0.12:
            state = "SILENCE_OR_STUDY"
            is_speaking = False
        elif energy > 0.65 and spectral_entropy > 0.75:
            state = "NOISE_DISTURBANCE"
            is_speaking = False
        elif speech_ratio > 0.50 or energy >= 0.20:
            is_speaking = True
            # Determine if monologue vs interactive discussion
            # Look at volatility in recent energy buffer
            recent_energies = [e for e, s, t in list(self.history)[-10:]] if self.history else []
            if len(recent_energies) >= 5:
                volatility = max(recent_energies) - min(recent_energies)
                if volatility > 0.35:
                    state = "SPEECH_INTERACTION"
                else:
                    state = "SPEECH_MONOLOGUE"
            else:
                state = "SPEECH_MONOLOGUE"
        else:
            state = "AMBIENT_BACKGROUND"
            is_speaking = False
            
        # Update monologue counter
        if state == "SPEECH_MONOLOGUE":
            if self.monologue_start_time is None:
                self.monologue_start_time = now
            self.current_monologue_sec = now - self.monologue_start_time
        elif state == "SPEECH_INTERACTION":
            self.monologue_start_time = None
            self.current_monologue_sec = 0.0
            self.last_interaction_time = now
        else: # Silence
            if self.monologue_start_time is not None and (now - self.monologue_start_time) > 15:
                # brief pause doesn't immediately reset unless pause > 15s
                pass
            else:
                self.monologue_start_time = None
                self.current_monologue_sec = 0.0
                
        # Calculate Interaction Index (0.0 = passive/monologue, 1.0 = highly collaborative)
        if state == "SPEECH_INTERACTION":
            interaction_index = min(1.0, 0.75 + energy * 0.25)
            self.interaction_peaks_count += 1
        elif state == "SPEECH_MONOLOGUE":
            # Instructor speaking alone
            interaction_index = 0.35
        elif state == "SILENCE_OR_STUDY":
            interaction_index = 0.20
        else:
            interaction_index = 0.25
            
        self.history.append((energy, state, now))
        
        return {
            'state': state,
            'energy': round(energy, 3),
            'interaction_index': round(interaction_index, 3),
            'is_speaking': is_speaking,
            'monologue_seconds': round(self.current_monologue_sec, 1),
            'monologue_minutes': round(self.current_monologue_sec / 60.0, 1),
            'monologue_alert': bool(self.current_monologue_sec >= (Config.MAX_MONOLOGUE_MINUTES * 60)),
            'timestamp': now
        }
