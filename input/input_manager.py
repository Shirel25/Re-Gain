import numpy as np

from input.keyboard import KeyboardInput
from config import MAC_ADDRESS, EMG_BASELINE, EMG_MAX_ACTIVATION
from config import REST, ACTIVE, OVERLOAD
from input.fake_emg import FakeEMGInput
from input.emg import EMGInput, DualEMGInput, FatigueTracker
from models.k_means_model import KMeansModel

# ============================================================================================
# INPUT MANAGER
# Interprets input signals (keyboard, fake EMG, or real EMG)
    # and converts them into gameplay intentions.

    # Architecture:
    # - Short loop (loop 1): real-time interpretation (move, speed, jump)
    # - Long loop  (loop 2): performance aggregation and difficulty adaptation

    # NOTE:
    # - Signal generation (FakeEMGInput) is independent from interpretation.
    # - K-means is used ONLY to learn user-specific activation levels.
# ============================================================================================

class InputManager:
    def __init__(self, mode="keyboard", calibration=None, device=None):
        # -------------------------------------------------
        # Global mode
        # -------------------------------------------------
        self.mode = mode
        self.calibration = calibration
        self.device = device

        # -------------------------------------------------
        # Instantaneous gameplay decisions (loop 1 outputs)
        # -------------------------------------------------
        self.move = False # should the player move forward this frame
        self.jump = False # should the player jump this frame

        # -------------------------------------------------
        # Jump regulation 
        # -------------------------------------------------
        # self.prev_leg_act = 0.0
        self.jump_cooldown = 0.0 # seconds before another jump is allowed

        self.good_jumps = 0
        self.bad_jumps = 0

        self.jump_intent_time = 0.0  # buffered jump intention (seconds)


        # -------------------------------------------------
        # Arm stability tracking 
        # -------------------------------------------------
        self.frame_count = 0
        self.arm_stable_time = 0.0
        self.STABILITY_SHORT = 0.25
        self.ARM_STABILITY_THRESHOLD = 0.25  # secondes

        self.arm_variance_buffer = []
        self.VARIANCE_WINDOW = 120  # ~2s

        # Vitesse
        # --- Short-loop control parameters ---
        self.SPEED_NORMAL = 1.0
        self.SPEED_BOOST = 1.8
        self.STABILITY_LONG = 0.5

        self.effective_speed_sum = 0.0
        self.effective_speed_samples = 0

        # -------------------------------------------------
        # BOUCLE LONGUE (loop 2- adaptation)
        # -------------------------------------------------
        self.control_time = 0.0
        self.total_time = 0.0

        self.mean_speed = 0.0
        self.speed_samples = 0

        self.mean_arm_activation = 0.0
        self.arm_samples = 0
        
        self.fatigue_enabled_global = True # UPDATED; MAKE IT FALSE TO DISABLE FATIGUE SIMULATION!!!
        self.fatigue_allowed = True # UPDATED; fatigue allowed only from session 2
        # -------------------------------------------------
        
       
        self.fatigue_tracker = FatigueTracker(fps=60, window_sec=20.0)
        self.fatigue_score = 0.0
        self.fatigued = False
        self.session_index = 1
        
        
        self._dbg_t = 0.0



        # -------------------------------------------------
        # Input source initialization
        # -------------------------------------------------
        if self.mode == "keyboard":
            self.input = KeyboardInput()
        
        # elif self.mode == "emg":
        #     self.input = EMGInput(
        #         mac_address=MAC_ADDRESS,
        #         baseline=EMG_BASELINE,
        #         max_activation=EMG_MAX_ACTIVATION
        #     )
        

        elif self.mode == "fake_emg":
            print("FAKE EMG active")
            # beginner | intermediate | advanced
            # self.input = FakeEMGInput(profile="beginner") 
            self.input = FakeEMGInput(profile="intermediate")
            # self.input = FakeEMGInput(profile="advanced")
            print(f"Profile: {self.input.profile}")

            # Unsupervised models to discretize EMG activations:
            # Accumulate raw EMG activations over time.
            # These samples are later clustered to learn
            # what "low / medium / high" activation means for THIS user.
            self.arm_model = KMeansModel(n_clusters=3) # REST / ACTIVE / OVERLOAD
            self.leg_model = KMeansModel(n_clusters=2) # REST / ACTIVE
    
        elif self.mode == "dual_emg":
            self.input = DualEMGInput(
                    device=self.device,
                    arm_channel=5,  # A5
                    leg_channel=2,  # A2
                    calibration=calibration
                )
            self.arm_model = KMeansModel(n_clusters=3)
            self.leg_model = KMeansModel(n_clusters=2)

        else:
            raise ValueError("Unknown input mode")

    def update(self, events=None):
        # Reset frame decisions
        self.move = False
        self.jump = False

        # -------------------------------------------------
        # Keyboard mode (baseline, no adaptation)
        # -------------------------------------------------
        if self.mode == "keyboard":
            self.input.update(events)
            self.move = self.input.move_right_pressed()
            self.jump = self.input.jump_pressed()
        
        elif self.mode == "fake_emg":
            # ---------------------------------------------
            # Read simulated EMG signals
            # ---------------------------------------------
            arm_act, leg_act = self.input.update()
            
            dt = 1 / 60
            # decay jump intention buffer
            if self.jump_intent_time > 0:
                self.jump_intent_time -= dt


            # ---------------------------------------------
            # Unsupervised learning (K-means)
            # The system learns what "low / medium / high"
            # activation means for THIS user
            # ---------------------------------------------
            self.arm_model.add_sample([arm_act])
            self.leg_model.add_sample([leg_act])

            self.frame_count += 1

            # Periodically re-fit K-means models every 30 frames (~0.5s) so that
            # activation thresholds (clusters) adapt to the user's behavior.
            # This avoids fixed, arbitrary thresholds.
            if self.frame_count % 30 == 0:
                self.arm_model.fit()
                self.leg_model.fit()

            # ---------------------------------------------
            # Discretization of EMG signals into states
            # ---------------------------------------------
            arm_cluster = self.arm_model.predict([arm_act])
            arm_order = self.arm_model.get_cluster_order()

            if arm_order is not None:
                # K-means only provides clusters.
                # We impose a semantic meaning by ordering clusters
                # from lowest to highest activation:
                #   lowest  -> REST
                #   middle  -> ACTIVE
                #   highest -> OVERLOAD
                arm_state_map = {
                    arm_order[0]: REST,
                    arm_order[1]: ACTIVE,
                    arm_order[2]: OVERLOAD,
                }
                arm_state = arm_state_map.get(arm_cluster, REST)
            else:
                arm_state = REST

            # --------------------------------------------------
            # PHYSIOLOGICAL INHIBITION (ANTI NORMALISATION)
            # --------------------------------------------------
            MIN_ARM_ACTIVATION = 0.15  # seuil physiologique minimal

            if arm_act < MIN_ARM_ACTIVATION:
                arm_state = REST


            # --- LEG ---
            leg_cluster = self.leg_model.predict([leg_act])
            leg_order = self.leg_model.get_cluster_order()
            if leg_order is not None:
                leg_state_map = {
                    leg_order[0]: REST,
                    leg_order[1]: ACTIVE,
                }
                leg_state = leg_state_map.get(leg_cluster, REST)
            else:
                leg_state = REST
            
            
            # ---- Gameplay ----
            # --- ARM ---
            # ============================
            # BOUCLE COURTE – CONTINUOUS CONTROL
            # ============================
            dt = 1 / 60

            MIN_ARM_ACTIVATION = 0.15

            if arm_act > MIN_ARM_ACTIVATION:
                self.move = True

                # vitesse proportionnelle à l’effort
                self.move_speed = (
                    self.SPEED_NORMAL
                    + arm_act * (self.SPEED_BOOST - self.SPEED_NORMAL)
                )

                self.move_speed = min(self.move_speed, self.SPEED_BOOST)
            else:
                self.move = False
                self.move_speed = 0.0



            if self.fatigue_enabled_global and self.fatigue_allowed:
                score, fat = self.fatigue_tracker.update(arm_activation=arm_act, move_intent=self.move)
                self.fatigue_score, self.fatigued = score, fat
            else:
                self.fatigue_score = 0.0
                self.fatigued = False



            self.effective_speed_sum += self.move_speed
            self.effective_speed_samples += 1

            self.arm_variance_buffer.append(arm_act)
            if len(self.arm_variance_buffer) > self.VARIANCE_WINDOW:
                self.arm_variance_buffer.pop(0)


            # --- LEG ---
            # Jump is allowed only:
            # - if leg is ACTIVE
            # - if the player is already moving
            # - if cooldown is over
            if self.jump_cooldown > 0:
                self.jump_cooldown -= dt
                # self.jump = False
            else:
                if leg_state == ACTIVE and self.move:
                    # self.jump = True
                    self.jump_intent_time = 0.25  # secondes
                    self.jump_cooldown = 0.6
                # else:
                #     self.jump = False

            
            # ============================
            # BOUCLE LONGUE – metrics
            # ============================
            dt = 1 / 60
            self.mean_speed += self.move_speed * dt
            self.speed_samples += 1
            self.total_time += dt

            # Contrôle actif même pendant un saut
            if self.move:
                self.control_time += dt


        elif self.mode == "dual_emg":
            arm_act, leg_act = self.input.update()
            
            score, fat = self.fatigue_tracker.update(arm_activation=arm_act, move_intent=self.move)
            if self.fatigue_allowed:
                self.fatigue_score, self.fatigued = score, fat
            else:
                # session 1: learn baseline silently but never trigger fatigue state
                self.fatigue_score = 0.0
                self.fatigued = False


            # temporaire : on utilise l’activation comme feature
            arm_features = [arm_act]
            leg_features = [leg_act]

            # Ajouter les données au buffer
            self.arm_model.add_sample(arm_features)
            self.leg_model.add_sample(leg_features)

            # Entraîner si possible
            self.arm_model.fit()
            self.leg_model.fit()

            # Prédiction
            arm_cluster = self.arm_model.predict(arm_features)
            leg_cluster = self.leg_model.predict(leg_features)

            # Si le modèle n'est pas prêt, on ne fait rien
            if arm_cluster is None or leg_cluster is None:
                return

            # Interprétation SIMPLE (temporaire)
            # cluster le plus élevé = ACTIVE (heuristique provisoire)
            arm_state = arm_cluster
            leg_state = leg_cluster

            self.move = (arm_state == ACTIVE)
            self.jump = (leg_state == ACTIVE)

            # --- Continuous effort tracking (LONG LOOP) ---
            self.mean_arm_activation += arm_act
            self.arm_samples += 1

            print(
                f"ARM act={arm_act:.2f} | cluster={arm_cluster} || "
                f"LEG act={leg_act:.2f} | cluster={leg_cluster}",
                end="\r"
            )

    def get_control_precision(self):
        if self.total_time == 0:
            return 0.0
        return self.control_time / self.total_time
       
    def get_mean_speed(self):
        if self.speed_samples == 0:
            return 0.0
        return self.mean_speed / self.speed_samples
    
    def jump_pressed(self):
        return self.jump_intent_time > 0
        # return self.jump
        # return self.input.jump_pressed()
    
    def move_right_pressed(self):
        # return self.input.move_right_pressed()
        return self.move
    
    def reset_long_term_metrics(self):
        self.control_time = 0.0
        self.total_time = 0.0

    def get_difficulty_score(self):
        """
        Returns value in [0,1]
        """
        speed = self.get_effective_speed() / self.SPEED_BOOST
        stability = self.get_control_precision()
        # variability = self.get_arm_variability()
        jump_quality = self.get_jump_quality()

        speed = min(speed, 1.0)
        # stability = max(0.0, 1.0 - variability * 2)  # inverse variance

        return (
            0.4 * speed +
            0.4 * stability +
            0.2 * jump_quality
        )

    def get_effective_speed(self): # average effective speed during the session
        if self.effective_speed_samples == 0:
            return 0.0
        return self.effective_speed_sum / self.effective_speed_samples


    def get_jump_quality(self):
        total = self.good_jumps + self.bad_jumps
        if total == 0:
            return 0.5
        return self.good_jumps / total
    
    def get_difficulty_label(self): # for the continue session
        d = self.get_difficulty_score()
        if d < 0.33:
            return "beginner"
        elif d < 0.66:
            return "intermediate"
        return "advanced"


    def is_fatigued(self): # fatigue state getter
        return self.fatigued

    def get_fatigue_score(self):
        return self.fatigue_score

    def reset_fatigue_after_rest(self):
        self.fatigue_tracker.reset_after_rest()
        self.fatigue_score = 0.0
        self.fatigued = False
    
    def start_session(self, session_index: int, fresh: bool): # session management
        self.session_index = session_index
        self.fatigue_allowed = (session_index >= 2)

        # enable fatigue simulation ONLY from session 2 (fake EMG)
        if isinstance(self.input, FakeEMGInput):
            self.input.set_fatigue_enabled(self.fatigue_allowed)

        if fresh:

            self.fatigue_tracker = FatigueTracker(fps=60, window_sec=20.0)
            self.fatigue_score = 0.0
            self.fatigued = False


            
