"""
Multi-Target Detection System - Core Detection System Extension
Sistema di detection gioielli da integrare con YOLO11 esistente
"""

import cv2
import numpy as np
from ultralytics import YOLO
import logging
from datetime import datetime
import json
import threading
from pathlib import Path
import time

class DetectionTarget:
    """Definisce un target di detection specifico"""
    
    def __init__(self, name: str, config: dict):
        self.name = name
        self.config = config
        self.enabled = config.get('enabled', False)
        self.model_path = config.get('model_path', None)
        self.confidence_threshold = config.get('confidence_threshold', 0.5)
        self.alert_threshold = config.get('alert_threshold', 0.8)
        self.classes = config.get('classes', {})
        self.database_source = config.get('database_source', 'local')
        self.alert_rules = config.get('alert_rules', {})

class MultiTargetDetectionSystem:
    """Sistema principale di detection multi-target"""
    
    def __init__(self, config_path: str = "config/detection_config.json"):
        self.setup_logging()
        
        # Inizializza componenti
        self.targets = {}
        self.models = {}
        
        # Scenario attivo
        self.active_scenario = None
        self.active_targets = []
        
        # Stats e monitoring
        self.detection_stats = {}
        self.detection_history = []
        
        # Thread safety
        self.detection_lock = threading.Lock()
        
        # Carica configurazione
        self.config_path = config_path
        self.load_configuration()
        
    def setup_logging(self):
        """Setup logging system"""
        self.logger = logging.getLogger('MultiTargetDetection')
        self.logger.setLevel(logging.INFO)
        
        # File handler
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / f"detection_{datetime.now().strftime('%Y%m%d')}.log"
        
        if not self.logger.handlers:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
            self.logger.addHandler(file_handler)
    
    def load_configuration(self):
        """Carica configurazione da file"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
                
            # Carica targets
            for target_name, target_config in config.get('targets', {}).items():
                self.targets[target_name] = DetectionTarget(target_name, target_config)
            
            # Carica scenario attivo
            if 'active_scenario' in config:
                self.set_active_scenario(config['active_scenario'])
                
            self.logger.info(f"Configuration loaded: {len(self.targets)} targets")
            
        except FileNotFoundError:
            self.logger.warning("Config file not found, creating default")
            self.create_default_configuration()
    
    def create_default_configuration(self):
        """Crea configurazione di default"""
        default_config = {
            'active_scenario': 'jewelry_security',
            'targets': {
                'people': {
                    'enabled': True,
                    'model_path': None,  # Usa YOLO standard
                    'confidence_threshold': 0.5,
                    'alert_threshold': 0.7,
                    'database_source': 'ultralytics',
                    'alert_rules': {
                        'immediate_alert': True,
                        'track_movement': True
                    }
                },
                'jewelry': {
                    'enabled': False,  # Richiede training custom
                    'model_path': 'models/custom/jewelry_yolo11.pt',
                    'confidence_threshold': 0.6,
                    'alert_threshold': 0.8,
                    'database_source': 'local',
                    'classes': {
                        0: {'name': 'ring', 'value_multiplier': 1.2},
                        1: {'name': 'necklace', 'value_multiplier': 1.5},
                        2: {'name': 'bracelet', 'value_multiplier': 1.3},
                        3: {'name': 'watch', 'value_multiplier': 2.0},
                        4: {'name': 'earring', 'value_multiplier': 1.1},
                        5: {'name': 'precious_stone', 'value_multiplier': 3.0}
                    }
                }
            }
        }
        
        # Crea directory e salva
        Path(self.config_path).parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        # Carica la configurazione appena creata
        self.load_configuration()
    
    def set_active_scenario(self, scenario_name: str):
        """Imposta scenario attivo"""
        # Scenari predefiniti
        scenarios = {
            'jewelry_security': {
                'targets': ['people'],  # Solo people per ora, jewelry quando avremo il modello
                'description': 'Sicurezza gioielleria con detection persone'
            },
            'people_counting': {
                'targets': ['people'],
                'description': 'Conteggio presenze'
            },
            'general_security': {
                'targets': ['people'],
                'description': 'Sicurezza generale'
            }
        }
        
        scenario = scenarios.get(scenario_name)
        if not scenario:
            self.logger.error(f"Scenario '{scenario_name}' not found")
            return False
        
        self.active_scenario = scenario_name
        self.active_targets = scenario['targets']
        
        # Abilita solo i target del scenario
        for target_name, target in self.targets.items():
            target.enabled = target_name in self.active_targets
        
        # Carica modelli per target attivi
        self._load_active_models()
        
        self.logger.info(f"Active scenario: {scenario_name} with targets: {self.active_targets}")
        return True
    
    def _load_active_models(self):
        """Carica modelli per target attivi"""
        for target_name in self.active_targets:
            if target_name not in self.targets:
                continue
            
            target = self.targets[target_name]
            if not target.enabled:
                continue
            
            try:
                # Per 'people' usa YOLO standard
                if target_name == 'people':
                    self.models[target_name] = YOLO('yolo11n.pt')
                    self.logger.info(f"Model loaded for target '{target_name}': yolo11n.pt")
                else:
                    # Per altri target, prova il path specificato
                    model_path = target.model_path
                    if model_path and Path(model_path).exists():
                        self.models[target_name] = YOLO(model_path)
                        self.logger.info(f"Model loaded for target '{target_name}': {model_path}")
                    else:
                        self.logger.warning(f"Model not found for target '{target_name}': {model_path}")
                        
            except Exception as e:
                self.logger.error(f"Error loading model for '{target_name}': {e}")
    
    def detect_frame(self, frame: np.ndarray):
        """Detection principale su frame"""
        with self.detection_lock:
            results = {
                'timestamp': datetime.now().isoformat(),
                'scenario': self.active_scenario,
                'frame_shape': frame.shape,
                'detections_by_target': {},
                'alerts': [],
                'summary': {}
            }
            
            total_detections = 0
            high_priority_alerts = 0
            
            # Esegui detection per ogni target attivo
            for target_name in self.active_targets:
                if target_name not in self.models:
                    continue
                
                target = self.targets[target_name]
                model = self.models[target_name]
                
                try:
                    # Detection YOLO
                    detection_results = model(
                        frame,
                        conf=target.confidence_threshold,
                        verbose=False
                    )
                    
                    # Processa risultati
                    processed_detections = self._process_target_detections(
                        detection_results[0], target, target_name
                    )
                    
                    results['detections_by_target'][target_name] = processed_detections
                    total_detections += len(processed_detections)
                    
                    # Genera alert basati su regole
                    alerts = self._generate_alerts(processed_detections, target, target_name)
                    results['alerts'].extend(alerts)
                    high_priority_alerts += sum(1 for a in alerts if a.get('priority') == 'high')
                    
                except Exception as e:
                    self.logger.error(f"Detection error for target '{target_name}': {e}")
            
            # Summary
            results['summary'] = {
                'total_detections': total_detections,
                'targets_detected': len([t for t in results['detections_by_target'] if results['detections_by_target'][t]]),
                'high_priority_alerts': high_priority_alerts,
                'active_targets': len(self.active_targets)
            }
            
            # Aggiorna statistiche
            self._update_stats(results)
            
            return results
    
    def _process_target_detections(self, yolo_results, target: DetectionTarget, target_name: str):
        """Processa detection per target specifico"""
        detections = []
        
        if yolo_results.boxes is not None:
            for box in yolo_results.boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                bbox = box.xyxy[0].tolist()
                
                # Per people usa nomi COCO standard
                if target_name == 'people':
                    class_name = 'person' if class_id == 0 else f'object_{class_id}'
                else:
                    # Per altri target usa configurazione
                    class_info = target.classes.get(class_id, {'name': f'{target_name}_{class_id}'})
                    class_name = class_info.get('name', f'{target_name}_{class_id}')
                
                detection = {
                    'target': target_name,
                    'class_id': class_id,
                    'class_name': class_name,
                    'confidence': confidence,
                    'bbox': bbox,
                    'timestamp': datetime.now().isoformat()
                }
                
                # Calcoli specifici per target
                if target_name == 'jewelry':
                    detection['estimated_value'] = self._calculate_jewelry_value(target.classes.get(class_id, {}), confidence)
                
                detections.append(detection)
        
        return detections
    
    def _calculate_jewelry_value(self, class_info: dict, confidence: float) -> float:
        """Calcola valore stimato gioiello"""
        base_value = 100.0  # Euro
        multiplier = class_info.get('value_multiplier', 1.0)
        return round(base_value * multiplier * confidence, 2)
    
    def _generate_alerts(self, detections: list, target: DetectionTarget, target_name: str):
        """Genera alert basati su regole"""
        alerts = []
        
        for detection in detections:
            alert_conditions = []
            
            # Confidence alta
            if detection['confidence'] >= target.alert_threshold:
                alert_conditions.append('high_confidence')
            
            # Regole specifiche
            if target_name == 'people':
                alert_conditions.append('person_detected')
            
            # Crea alert se ci sono condizioni
            if alert_conditions:
                priority = 'high' if 'person_detected' in alert_conditions else 'medium'
                
                alert = {
                    'target': target_name,
                    'detection': detection,
                    'conditions': alert_conditions,
                    'priority': priority,
                    'timestamp': datetime.now().isoformat(),
                    'scenario': self.active_scenario
                }
                
                alerts.append(alert)
        
        return alerts
    
    def _update_stats(self, results: dict):
        """Aggiorna statistiche sistema"""
        timestamp = results['timestamp']
        
        # Stats per target
        for target_name, detections in results['detections_by_target'].items():
            if target_name not in self.detection_stats:
                self.detection_stats[target_name] = {
                    'total_detections': 0,
                    'last_detection': None,
                    'avg_confidence': 0.0
                }
            
            if detections:
                self.detection_stats[target_name]['total_detections'] += len(detections)
                self.detection_stats[target_name]['last_detection'] = timestamp
                
                # Media confidence
                confidences = [d['confidence'] for d in detections]
                self.detection_stats[target_name]['avg_confidence'] = np.mean(confidences)
        
        # Storico limitato
        self.detection_history.append({
            'timestamp': timestamp,
            'summary': results['summary'].copy()
        })
        
        if len(self.detection_history) > 100:
            self.detection_history = self.detection_history[-100:]
    
    def get_system_status(self):
        """Stato completo sistema"""
        return {
            'active_scenario': self.active_scenario,
            'active_targets': self.active_targets,
            'loaded_models': list(self.models.keys()),
            'available_targets': list(self.targets.keys()),
            'detection_stats': self.detection_stats.copy(),
            'models_ready': len(self.models) > 0
        }
    
    def _draw_multi_target_detections(self, frame: np.ndarray, results: dict) -> np.ndarray:
        """Disegna detection con colori diversi per target"""
        target_colors = {
            'people': (0, 255, 0),      # Verde
            'jewelry': (255, 215, 0),   # Oro
            'faces': (255, 0, 255),     # Magenta
            'bags': (255, 165, 0),      # Arancione
        }
        
        for target_name, detections in results['detections_by_target'].items():
            color = target_colors.get(target_name, (255, 255, 255))
            
            for detection in detections:
                bbox = detection['bbox']
                x1, y1, x2, y2 = map(int, bbox)
                
                # Spessore basato su confidence
                thickness = max(1, int(detection['confidence'] * 3))
                
                # Bounding box
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
                
                # Label
                label = f"{detection['class_name']} {detection['confidence']:.2f}"
                if 'estimated_value' in detection:
                    label += f" (€{detection['estimated_value']:.0f})"
                
                # Background label
                label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
                cv2.rectangle(frame, (x1, y1-25), (x1 + label_size[0], y1), color, -1)
                
                # Testo
                cv2.putText(frame, label, (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
        
        # Info scenario
        scenario_text = f"Scenario: {self.active_scenario}"
        cv2.putText(frame, scenario_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return frame
    
    def save_detection_with_targets(self, frame: np.ndarray, results: dict):
        """Salva detection con annotazioni multi-target"""
        if not results['detections_by_target']:
            return
        
        try:
            # Directory output
            output_dir = Path('captures/multi_target')
            output_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
            
            # Annota frame
            annotated_frame = self._draw_multi_target_detections(frame.copy(), results)
            
            # Salva immagine
            img_path = output_dir / f"detection_{timestamp}.jpg"
            cv2.imwrite(str(img_path), annotated_frame)
            
            # Salva metadata
            metadata = {
                'detection_results': results,
                'system_status': self.get_system_status(),
                'image_path': str(img_path)
            }
            
            json_path = output_dir / f"detection_{timestamp}.json"
            with open(json_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            self.logger.info(f"Multi-target detection saved: {img_path.name}")
            
        except Exception as e:
            self.logger.error(f"Error saving detection: {e}")


if __name__ == "__main__":
    print("🎯 Multi-Target Detection System - Test")
    
    # Test del sistema
    try:
        detection_system = MultiTargetDetectionSystem()
        print("✅ System initialized")
        print("📊 Status:", detection_system.get_system_status())
        
        # Test scenario
        success = detection_system.set_active_scenario('jewelry_security')
        print(f"🎭 Scenario set: {success}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
