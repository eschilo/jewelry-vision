"""
Enhanced Jewelry Vision Web - Sistema completo integrato
Versione enhanced del sistema originale con multi-target detection
"""

from flask import Flask, render_template, Response, jsonify, request, send_from_directory
import cv2
import numpy as np
import json
import logging
import threading
import time
from datetime import datetime
from pathlib import Path
import os

# Enhanced System Imports
try:
    from multi_target_detection import MultiTargetDetectionSystem
    from scenario_configurator import ScenarioConfigurator
    ENHANCED_AVAILABLE = True
    print("✅ Enhanced system disponibile")
except ImportError as e:
    ENHANCED_AVAILABLE = False
    print(f"⚠️ Enhanced system non disponibile: {e}")

# Verifica dipendenze base
try:
    import cv2
    print(f"✅ OpenCV disponibile - versione: {cv2.__version__}")
except ImportError:
    print("❌ OpenCV non disponibile")

try:
    from ultralytics import YOLO
    print("✅ YOLO11 disponibile")
except ImportError:
    print("❌ YOLO11 non disponibile")

try:
    import numpy as np
    print(f"✅ Numpy disponibile - versione: {np.__version__}")
except ImportError:
    print("❌ Numpy non disponibile")

class JewelryVisionWeb:
    """
    Sistema principale Jewelry Vision con funzionalità enhanced
    """
    
    def __init__(self):
        print("🔍 Inizializzazione JewelryVisionWeb...")
        
        # Configurazione camera e streaming
        self.camera_index = 0
        self.frame_width = 640
        self.frame_height = 480
        self.fps = 30
        self.detection_interval = 3
        self.jpeg_quality = 85
        
        # Stato sistema
        self.streaming_active = False
        self.monitoring_active = False
        self.camera = None
        
        # Configurazione detection
        self.confidence_threshold = 0.5
        self.model = None
        
        # Stats
        self.detection_count = 0
        self.last_detection_time = None
        
        # Setup logging
        self.setup_logging()
        
        # Inizializza modello base
        self.initialize_base_model()
        
        # Enhanced System Setup
        self.setup_enhanced_system()
        
        print("✅ JewelryVisionWeb inizializzato")
    
    def setup_logging(self):
        """Setup logging system"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('JewelryVisionWeb')
        
        # File handler
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / f"jewelry_vision_{datetime.now().strftime('%Y%m%d')}.log"
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        self.logger.addHandler(file_handler)
    
    def initialize_base_model(self):
        """Inizializza modello YOLO base"""
        try:
            self.model = YOLO('yolo11n.pt')
            self.logger.info("✅ Modello YOLO base caricato")
        except Exception as e:
            self.logger.error(f"❌ Errore caricamento modello base: {e}")
            self.model = None
    
    def setup_enhanced_system(self):
        """Setup sistema enhanced"""
        if ENHANCED_AVAILABLE:
            try:
                self.detection_system = MultiTargetDetectionSystem()
                self.scenario_configurator = ScenarioConfigurator(self.detection_system)
                self.detection_system.set_active_scenario('jewelry_security')
                self.enhanced_enabled = True
                self.logger.info("✅ Enhanced system attivato")
                print("✅ Enhanced system attivato")
            except Exception as e:
                self.logger.error(f"⚠️ Enhanced system errore: {e}")
                print(f"⚠️ Enhanced system errore: {e}")
                self.enhanced_enabled = False
        else:
            self.enhanced_enabled = False
            self.logger.warning("⚠️ Enhanced system non disponibile")
    
    def start_streaming(self):
        """Avvia streaming camera"""
        try:
            if not self.streaming_active:
                self.camera = cv2.VideoCapture(self.camera_index)
                
                if not self.camera.isOpened():
                    self.logger.error("❌ Impossibile aprire camera")
                    return False
                
                # Configurazione camera
                self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
                self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
                self.camera.set(cv2.CAP_PROP_FPS, self.fps)
                self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                
                self.streaming_active = True
                self.logger.info("📹 Streaming avviato")
                print("📹 Streaming avviato")
                return True
        except Exception as e:
            self.logger.error(f"❌ Errore avvio streaming: {e}")
            return False
    
    def stop_streaming(self):
        """Ferma streaming"""
        self.streaming_active = False
        self.monitoring_active = False
        
        if self.camera:
            self.camera.release()
            self.camera = None
        
        self.logger.info("📹 Streaming fermato")
        print("📹 Streaming fermato")
    
    def generate_frames(self):
        """Generator per streaming video"""
        frame_count = 0
        
        while self.streaming_active:
            if not self.camera:
                break
                
            success, frame = self.camera.read()
            if not success:
                self.logger.warning("⚠️ Errore lettura frame")
                break
            
            frame_count += 1
            
            # Detection ogni N frame per performance
            if self.monitoring_active and frame_count % self.detection_interval == 0:
                frame = self.process_frame_with_detection(frame)
            
            # Encoding per streaming
            try:
                ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality])
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                          b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            except Exception as e:
                self.logger.error(f"Errore encoding frame: {e}")
                break
        
        # Cleanup
        if self.camera:
            self.camera.release()
            self.camera = None
    
    def process_frame_with_detection(self, frame):
        """Processa frame con detection (enhanced + fallback)"""
        try:
            # Prova prima enhanced detection
            if self.enhanced_enabled and hasattr(self, 'detection_system'):
                frame = self.apply_enhanced_detection(frame)
            else:
                # Fallback detection base
                frame = self.apply_base_detection(frame)
            
            return frame
            
        except Exception as e:
            self.logger.error(f"Errore detection: {e}")
            return frame
    
    def apply_enhanced_detection(self, frame):
        """Applica enhanced detection"""
        try:
            results = self.detection_system.detect_frame(frame)
            if results and results.get('detections_by_target'):
                frame = self.detection_system._draw_multi_target_detections(frame, results)
                
                # Update stats
                total_detections = results.get('summary', {}).get('total_detections', 0)
                if total_detections > 0:
                    self.detection_count += total_detections
                    self.last_detection_time = datetime.now()
                
                # Salva detection importanti
                if len(results.get('alerts', [])) > 0:
                    self.detection_system.save_detection_with_targets(frame, results)
            
            return frame
        except Exception as e:
            self.logger.error(f"Errore enhanced detection: {e}")
            return self.apply_base_detection(frame)
    
    def apply_base_detection(self, frame):
        """Detection base con YOLO standard (fallback)"""
        try:
            if self.model is None:
                return frame
            
            # Detection YOLO
            results = self.model(frame, conf=self.confidence_threshold, verbose=False)
            
            # Disegna detection
            for result in results:
                if result.boxes is not None:
                    for box in result.boxes:
                        # Coordinate bounding box
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                        
                        # Confidence e classe
                        confidence = float(box.conf[0])
                        class_id = int(box.cls[0])
                        class_name = self.model.names[class_id]
                        
                        # Disegna bounding box
                        color = (0, 255, 0)  # Verde
                        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                        
                        # Label
                        label = f"{class_name} {confidence:.2f}"
                        label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
                        cv2.rectangle(frame, (x1, y1-25), (x1 + label_size[0], y1), color, -1)
                        cv2.putText(frame, label, (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                        
                        # Update stats
                        self.detection_count += 1
                        self.last_detection_time = datetime.now()
            
            return frame
            
        except Exception as e:
            self.logger.error(f"Errore base detection: {e}")
            return frame
    
    def capture_frame(self):
        """Cattura frame corrente"""
        if not self.camera:
            return False
        
        success, frame = self.camera.read()
        if success:
            # Directory captures
            captures_dir = Path("captures")
            captures_dir.mkdir(exist_ok=True)
            
            # Nome file con timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"capture_{timestamp}.jpg"
            filepath = captures_dir / filename
            
            # Salva frame
            cv2.imwrite(str(filepath), frame)
            self.logger.info(f"📸 Frame salvato: {filename}")
            return True
        
        return False
    
    def get_monitoring_status(self):
        """Status monitoring corrente"""
        status = {
            'streaming_active': self.streaming_active,
            'monitoring_active': self.monitoring_active,
            'camera_connected': self.camera is not None,
            'detection_count': self.detection_count,
            'last_detection': self.last_detection_time.isoformat() if self.last_detection_time else None,
            'enhanced_enabled': getattr(self, 'enhanced_enabled', False),
            'model_loaded': self.model is not None
        }
        
        # Aggiungi info enhanced se disponibile
        if self.enhanced_enabled and hasattr(self, 'detection_system'):
            enhanced_status = self.detection_system.get_system_status()
            status.update({
                'active_scenario': enhanced_status.get('active_scenario'),
                'active_targets': enhanced_status.get('active_targets', []),
                'enhanced_stats': enhanced_status.get('detection_stats', {})
            })
        
        return status


# Creazione app Flask
app = Flask(__name__)
app.secret_key = 'jewelry_vision_enhanced_secret_key'

# Inizializzazione sistema
jewelry_system = JewelryVisionWeb()

# ============= ROUTE PRINCIPALI =============

@app.route('/')
def main_menu():
    """Menu principale"""
    return render_template('main_menu.html')

@app.route('/surveillance')
def surveillance():
    """Pagina surveillance"""
    return render_template('surveillance.html')

@app.route('/monitoring')
def monitoring():
    """Pagina monitoring"""
    return render_template('monitoring.html')

@app.route('/scenario_manager')
def scenario_manager():
    """Interfaccia scenario manager (NUOVA)"""
    return render_template('scenario_manager.html')

# ============= STREAMING =============

@app.route('/video_feed')
def video_feed():
    """Stream video principale"""
    return Response(
        jewelry_system.generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@app.route('/detection_feed')
def detection_feed():
    """Stream con detection (alias per compatibilità)"""
    return video_feed()

# ============= API CONTROLLO STREAMING =============

@app.route('/api/start_streaming', methods=['POST'])
def start_streaming():
    """Avvia streaming"""
    success = jewelry_system.start_streaming()
    return jsonify({
        'success': success,
        'message': 'Streaming avviato' if success else 'Errore avvio streaming'
    })

@app.route('/api/stop_streaming', methods=['POST'])
def stop_streaming():
    """Ferma streaming"""
    jewelry_system.stop_streaming()
    return jsonify({'success': True, 'message': 'Streaming fermato'})

@app.route('/api/start_monitoring', methods=['POST'])
def start_monitoring():
    """Avvia monitoring"""
    jewelry_system.monitoring_active = True
    return jsonify({'success': True, 'message': 'Monitoring avviato'})

@app.route('/api/stop_monitoring', methods=['POST'])
def stop_monitoring():
    """Ferma monitoring"""
    jewelry_system.monitoring_active = False
    return jsonify({'success': True, 'message': 'Monitoring fermato'})

@app.route('/api/capture_frame', methods=['POST'])
def capture_frame():
    """Cattura frame"""
    success = jewelry_system.capture_frame()
    return jsonify({
        'success': success,
        'message': 'Frame catturato' if success else 'Errore cattura frame'
    })

@app.route('/api/monitoring_status')
def monitoring_status():
    """Status monitoring"""
    status = jewelry_system.get_monitoring_status()
    return jsonify(status)

# ============= API ENHANCED =============

@app.route('/api/system/status')
def get_system_status():
    """Status sistema enhanced"""
    try:
        if hasattr(jewelry_system, 'detection_system') and jewelry_system.enhanced_enabled:
            status = jewelry_system.detection_system.get_system_status()
            status.update({
                'streaming_active': jewelry_system.streaming_active,
                'monitoring_active': jewelry_system.monitoring_active,
                'enhanced_enabled': jewelry_system.enhanced_enabled,
                'camera_connected': jewelry_system.camera is not None,
                'detection_count': jewelry_system.detection_count,
                'timestamp': datetime.now().isoformat()
            })
            return jsonify({'success': True, 'status': status})
        else:
            # Fallback status
            return jsonify({
                'success': True, 
                'status': jewelry_system.get_monitoring_status()
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/scenarios/list')
def list_scenarios():
    """Lista scenari disponibili"""
    try:
        if hasattr(jewelry_system, 'scenario_configurator') and jewelry_system.enhanced_enabled:
            predefined = jewelry_system.scenario_configurator.get_scenario_templates()
            custom_scenarios = jewelry_system.scenario_configurator.load_custom_scenarios()
            active_scenario = jewelry_system.detection_system.active_scenario
            
            return jsonify({
                'success': True,
                'predefined_scenarios': predefined,
                'custom_scenarios': custom_scenarios,
                'active_scenario': active_scenario
            })
        else:
            # Fallback scenari base
            return jsonify({
                'success': True,
                'predefined_scenarios': {
                    'basic_security': {
                        'name': 'Sicurezza Base',
                        'description': 'Detection persone con YOLO standard',
                        'targets': ['people']
                    }
                },
                'custom_scenarios': {},
                'active_scenario': 'basic_security'
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/scenarios/activate/<scenario_name>', methods=['POST'])
def activate_scenario(scenario_name):
    """Attiva scenario"""
    try:
        if hasattr(jewelry_system, 'detection_system') and jewelry_system.enhanced_enabled:
            success = jewelry_system.detection_system.set_active_scenario(scenario_name)
            return jsonify({
                'success': success,
                'scenario': scenario_name,
                'active_targets': jewelry_system.detection_system.active_targets if success else [],
                'message': f'Scenario "{scenario_name}" {"attivato" if success else "non trovato"}'
            })
        else:
            return jsonify({
                'success': False, 
                'error': 'Enhanced system non attivo - usando detection base'
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/scenarios/create', methods=['POST'])
def create_custom_scenario():
    """Crea scenario personalizzato"""
    try:
        if hasattr(jewelry_system, 'scenario_configurator') and jewelry_system.enhanced_enabled:
            config = request.get_json()
            result = jewelry_system.scenario_configurator.create_custom_scenario(config)
            return jsonify(result)
        else:
            return jsonify({
                'success': False,
                'error': 'Enhanced system richiesto per scenari personalizzati'
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/databases/info')
def get_databases_info():
    """Informazioni database disponibili"""
    try:
        if hasattr(jewelry_system, 'scenario_configurator') and jewelry_system.enhanced_enabled:
            info = jewelry_system.scenario_configurator.get_database_info()
            return jsonify({'success': True, 'databases': info})
        else:
            # Info base
            return jsonify({
                'success': True,
                'databases': {
                    'yolo_standard': {
                        'name': 'YOLO Standard',
                        'description': 'Modello YOLO11 base per detection generali',
                        'cost': 'Gratuito',
                        'pros': ['Veloce', 'Affidabile', 'Pronto all\'uso'],
                        'cons': ['Solo classi COCO standard']
                    }
                }
            })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ============= STATIC FILES =============

@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve file statici"""
    return send_from_directory('static', filename)

# ============= ERROR HANDLERS =============

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint non trovato'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Errore interno server'}), 500

# ============= MAIN =============

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🎯 JEWELRY VISION WEB - ENHANCED SYSTEM")
    print("="*60)
    print("📡 Server in ascolto su: http://localhost:5000")
    print("🏠 Menu principale: http://localhost:5000")
    print("📹 Surveillance: http://localhost:5000/surveillance")
    print("🎯 Detection: http://localhost:5000/monitoring")
    
    if jewelry_system.enhanced_enabled:
        print("💎 Scenario Manager: http://localhost:5000/scenario_manager")
        print("🔧 Sistema Enhanced: ATTIVO")
    else:
        print("⚠️ Sistema Enhanced: NON DISPONIBILE (usando fallback)")
    
    print("="*60)
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n⏹️ Server fermato")
        jewelry_system.stop_streaming()
    except Exception as e:
        print(f"\n❌ Errore server: {e}")
        jewelry_system.stop_streaming()

