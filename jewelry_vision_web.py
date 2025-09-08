#!/usr/bin/env python3
"""
Jewelry Vision System - Web Interface FINAL COMPLETE
Sistema completo di videosorveglianza intelligente per gioielli
Jetson Orin Nano Super - Settembre 2025
FEATURES:
- Menu principale con diamante e 5 sezioni
- Streaming video dedicato 
- Detection & Monitoring separato
- Gestione camera ottimizzata
- Interfaccia modulare
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for, Response
import subprocess
import os
import sys
import json
import time
import cv2
from pathlib import Path
from datetime import datetime
import threading
import psutil
import signal
import numpy as np

# Gestione import OpenCV
try:
    import cv2
    CV2_AVAILABLE = True
    print(f"✅ OpenCV disponibile - versione: {cv2.__version__}")
except ImportError:
    CV2_AVAILABLE = False
    print("❌ OpenCV non disponibile")

# Gestione import YOLO
try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
    print(f"✅ YOLO11 disponibile")
except ImportError:
    YOLO_AVAILABLE = False
    print("❌ YOLO11 non disponibile")

# Gestione import Numpy
try:
    import numpy as np
    print(f"✅ Numpy disponibile - versione: {np.__version__}")
except ImportError:
    print("❌ Numpy non disponibile")

class JewelryVisionWeb:
    def __init__(self):
        print("🔍 Inizializzazione JewelryVisionWeb...")
        
        # Stati sistema
        self.streaming_active = False
        self.monitoring_active = False
        self.recording_active = False
        self.detection_enabled = True
        self.alerts_enabled = True
        
        # Camera e streaming
        self.cap = None
        self.stream_thread = None
        self.current_frame = None
        self.frame_lock = threading.Lock()
        
        # YOLO Detection
        self.yolo_model = None
        if YOLO_AVAILABLE:
            try:
                self.yolo_model = YOLO('yolo11n.pt')
                print("✅ Modello YOLO11 caricato")
            except Exception as e:
                print(f"❌ Errore caricamento YOLO: {e}")
        
        # Statistiche sistema
        self.system_stats = {
            'uptime': 0,
            'frames_processed': 0,
            'detections_today': 0,
            'alerts_today': 0,
            'avg_fps': 0
        }
        
        # Avvia monitoraggio sistema
        self.start_system_monitoring()
        print("🎯 JewelryVisionWeb FINALE inizializzato")
    
    def start_system_monitoring(self):
        """Avvia monitoraggio sistema in background"""
        def monitor():
            start_time = time.time()
            while True:
                try:
                    # CPU e memoria
                    cpu_percent = psutil.cpu_percent()
                    memory_percent = psutil.virtual_memory().percent
                    
                    # Uptime
                    self.system_stats['uptime'] = int(time.time() - start_time)
                    
                    # Log ogni 5 minuti
                    if self.system_stats['uptime'] % 300 == 0:
                        print(f"📊 Sistema - CPU: {cpu_percent}%, RAM: {memory_percent}%")
                    
                    time.sleep(30)
                except Exception as e:
                    print(f"Errore monitoring: {e}")
                    break
        
        monitor_thread = threading.Thread(target=monitor, daemon=True)
        monitor_thread.start()
        print("📊 Monitoraggio sistema avviato")
    
    def stream_loop(self):
        """Loop principale streaming"""
        print("📹 Avvio stream loop...")
        fps_counter = 0
        fps_start = time.time()
        
        while self.streaming_active:
            try:
                if self.cap is None or not self.cap.isOpened():
                    print("❌ Camera non disponibile nel loop")
                    break
                
                ret, frame = self.cap.read()
                if not ret:
                    print("❌ Impossibile leggere frame")
                    time.sleep(0.1)
                    continue
                
                # Aggiorna frame corrente
                with self.frame_lock:
                    self.current_frame = frame.copy()
                
                # Calcolo FPS
                fps_counter += 1
                if fps_counter >= 30:
                    elapsed = time.time() - fps_start
                    self.system_stats['avg_fps'] = round(fps_counter / elapsed, 1)
                    fps_counter = 0
                    fps_start = time.time()
                
                self.system_stats['frames_processed'] += 1
                time.sleep(1/30)  # 30 FPS
                
            except Exception as e:
                print(f"❌ Errore stream loop: {e}")
                time.sleep(1)
                break
        
        print("🛑 Stream loop terminato")
    
    def start_streaming(self):
        """Avvia streaming video"""
        print("🚀 START STREAMING...")
        
        if not CV2_AVAILABLE:
            return False, "❌ OpenCV non disponibile"
        
        if self.streaming_active:
            return True, "✅ Streaming già attivo"
        
        try:
            # Ferma monitoring se attivo
            if self.monitoring_active:
                print("🔄 Fermando monitoring per avviare streaming...")
                self.stop_monitoring()
                time.sleep(1)
            
            # Rilascia camera esistente
            if hasattr(self, 'cap') and self.cap is not None:
                self.cap.release()
                time.sleep(0.5)
            
            # Crea nuova connessione camera (forza V4L2)
            self.cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
            if not self.cap.isOpened():
                return False, "❌ Impossibile aprire camera"
            
            # Configura camera
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # Avvia thread streaming
            self.streaming_active = True
            if hasattr(self, 'stream_thread') and self.stream_thread and self.stream_thread.is_alive():
                self.stream_thread.join(timeout=1)
            
            self.stream_thread = threading.Thread(target=self.stream_loop, daemon=True)
            self.stream_thread.start()
            
            print("✅ Streaming avviato")
            return True, "📹 Streaming avviato con successo!"
            
        except Exception as e:
            print(f"❌ Errore avvio streaming: {e}")
            return False, f"Errore: {str(e)}"

    def stop_streaming(self):
        """Ferma streaming"""
        print("🛑 STOP STREAMING...")
        
        self.streaming_active = False
        
        # Attendi stop thread
        if hasattr(self, 'stream_thread') and self.stream_thread and self.stream_thread.is_alive():
            self.stream_thread.join(timeout=2)
        
        # Cleanup
        if hasattr(self, 'cap') and self.cap is not None:
            try:
                self.cap.release()
            except:
                pass
            self.cap = None
        
        print("✅ Streaming fermato")
        return True, "⏹️ Streaming fermato!"

    def start_monitoring(self):
        """Avvia monitoring con detection YOLO reale"""
        print("🎯 START MONITORING...")
        
        if self.monitoring_active:
            return True, "✅ Monitoring già attivo"
        
        if not YOLO_AVAILABLE:
            return False, "❌ YOLO non disponibile"
        
        try:
            # Ferma streaming se attivo
            if self.streaming_active:
                print("🔄 Fermando streaming per avviare monitoring...")
                self.stop_streaming()
                time.sleep(2)
            
            # Inizializza camera per detection
            self.cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
            if not self.cap.isOpened():
                return False, "❌ Impossibile aprire camera per monitoring"
            
            # Configura camera
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # Risoluzione più bassa per detection
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 10)  # FPS più bassi per detection
            
            # Avvia monitoring
            self.monitoring_active = True
            self.detection_thread = threading.Thread(target=self._detection_loop, daemon=True)
            self.detection_thread.start()
            
            print("✅ Monitoring con detection YOLO avviato")
            return True, "🎯 Monitoring con AI detection attivato!"
            
        except Exception as e:
            print(f"❌ Errore avvio monitoring: {e}")
            return False, f"Errore: {str(e)}"

    def stop_monitoring(self):
        """Ferma monitoring"""
        print("🛑 STOP MONITORING...")
        
        self.monitoring_active = False
        
        # Attendi stop detection thread
        if hasattr(self, 'detection_thread') and self.detection_thread and self.detection_thread.is_alive():
            self.detection_thread.join(timeout=2)
        
        # Rilascia camera
        if hasattr(self, 'cap') and self.cap is not None:
            try:
                self.cap.release()
            except:
                pass
            self.cap = None
        
        print("✅ Monitoring fermato")
        return True, "⏹️ Monitoring fermato!"
    
    def _detection_loop(self):
        """Loop detection con YOLO"""
        print("🎯 Avvio detection loop...")
        
        while self.monitoring_active:
            try:
                if self.cap is None or not self.cap.isOpened():
                    print("❌ Camera non disponibile per detection")
                    break
                
                ret, frame = self.cap.read()
                if not ret:
                    time.sleep(0.1)
                    continue
                
                # Detection YOLO
                if self.yolo_model:
                    results = self.yolo_model(frame)
                    
                    # Processa risultati
                    for result in results:
                        boxes = result.boxes
                        if boxes is not None and len(boxes) > 0:
                            for box in boxes:
                                # Estrai info detection
                                conf = box.conf[0].item()
                                cls = int(box.cls[0].item())
                                class_name = self.yolo_model.names[cls]
                                
                                if conf > 0.5:  # Soglia confidenza
                                    print(f"🎯 Detection: {class_name} ({conf:.2f})")
                                    self.system_stats['detections_today'] += 1
                                    
                                    # Trigger allarme per persone
                                    if class_name == 'person' and conf > 0.7:
                                        self._trigger_alert(class_name, conf, frame)
                
                time.sleep(0.5)  # Detection ogni 500ms
                
            except Exception as e:
                print(f"❌ Errore detection loop: {e}")
                time.sleep(1)
        
        print("🛑 Detection loop terminato")
    
    def _trigger_alert(self, object_type, confidence, frame):
        """Trigger allarme detection"""
        if not self.alerts_enabled:
            return
        
        current_time = time.time()
        if hasattr(self, '_last_alert_time'):
            if current_time - self._last_alert_time < 10:  # Cooldown 10 secondi
                return
        
        self._last_alert_time = current_time
        self.system_stats['alerts_today'] += 1
        
        # Salva frame allarme
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        alert_frame_path = Path("captures") / f"alert_{object_type}_{timestamp}.jpg"
        cv2.imwrite(str(alert_frame_path), frame)
        
        print(f"🚨 ALLARME: {object_type} rilevato ({confidence:.2f}) - Frame salvato")
        
        # Beep allarme
        os.system('echo -e "\a"')
    
    def get_current_frame(self):
        """Ottiene frame corrente per streaming web"""
        with self.frame_lock:
            if self.current_frame is not None:
                return self.current_frame.copy()
        return None
    
    def capture_frame(self):
        """Cattura frame corrente"""
        frame = self.get_current_frame()
        if frame is None:
            return False, "❌ Nessun frame disponibile"
        
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"jewelry_capture_{timestamp}.jpg"
            filepath = Path("captures") / filename
            
            cv2.imwrite(str(filepath), frame)
            return True, f"📸 Frame salvato: {filename}"
        except Exception as e:
            return False, f"❌ Errore salvataggio: {str(e)}"
    
    def toggle_detection(self):
        """Toggle sistema detection"""
        self.detection_enabled = not self.detection_enabled
        status = "abilitato" if self.detection_enabled else "disabilitato"
        return True, f"🎯 Detection {status}"
    
    def toggle_alerts(self):
        """Toggle sistema allarmi"""
        self.alerts_enabled = not self.alerts_enabled
        status = "abilitato" if self.alerts_enabled else "disabilitato"
        return True, f"🔔 Allarmi {status}"
    
    def test_alarm(self):
        """Test allarme"""
        if self.alerts_enabled:
            # Beep sistema
            os.system('echo -e "\a"')
            self.system_stats['alerts_today'] += 1
            return True, "🔊 Test allarme eseguito con successo!"
        else:
            return False, "⚠️ Sistema allarmi disabilitato"
    
    def start_recording(self):
        """Avvia registrazione video"""
        if not self.recording_active:
            self.recording_active = True
            return True, "🔴 Registrazione video avviata!"
        else:
            return False, "⚠️ Registrazione già attiva"
    
    def stop_recording(self):
        """Ferma registrazione video"""
        if self.recording_active:
            self.recording_active = False
            return True, "⏹️ Registrazione video fermata!"
        else:
            return False, "⚠️ Registrazione non attiva"
    
    def get_status(self):
        """Ottiene status completo sistema"""
        return {
            'streaming_active': self.streaming_active,
            'monitoring_active': self.monitoring_active,
            'recording_active': self.recording_active,
            'detection_enabled': self.detection_enabled,
            'alerts_enabled': self.alerts_enabled,
            'system_stats': self.system_stats,
            'opencv_available': CV2_AVAILABLE,
            'yolo_available': YOLO_AVAILABLE,
            'uptime': f"{self.system_stats['uptime']//3600}h {(self.system_stats['uptime']%3600)//60}m"
        }
    
    def release_camera(self):
        """Rilascia tutte le risorse camera"""
        self.streaming_active = False
        self.monitoring_active = False
        
        if hasattr(self, 'stream_thread') and self.stream_thread and self.stream_thread.is_alive():
            self.stream_thread.join(timeout=2)
        
        if hasattr(self, 'cap') and self.cap is not None:
            self.cap.release()
            self.cap = None
        
        print("🔧 Tutte le risorse camera rilasciate")

# Istanza globale
jewelry_vision = JewelryVisionWeb()

# Flask App
app = Flask(__name__)

def generate_frames():
    """Genera frame per video streaming"""
    while True:
        frame = jewelry_vision.get_current_frame()
        if frame is not None:
            try:
                # Aggiungi overlay info
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cv2.putText(frame, f"Jewelry Vision - {timestamp}", (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Encoding
                ret, buffer = cv2.imencode('.jpg', frame)
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            except Exception as e:
                print(f"Errore encoding frame: {e}")
        
        time.sleep(1/30)  # 30 FPS

# ===== ROUTES FLASK =====

# Route principale
@app.route('/')
def main_menu():
    """Menu principale con diamante"""
    return render_template('main_menu.html')

# Routes sezioni
@app.route('/dataset')
def dataset():
    return render_template('dataset.html')

@app.route('/training')  
def training():
    return render_template('training.html')

@app.route('/surveillance')
def surveillance():
    """Pagina dedicata solo al video streaming"""
    return render_template('surveillance.html')

@app.route('/monitoring')
def monitoring():
    """Pagina dedicata solo al detection/monitoring"""
    return render_template('monitoring.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')

# Route compatibilità
@app.route('/index')
def index():
    """Vecchia interfaccia per compatibilità"""
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    """Stream video per interfaccia web"""
    if not jewelry_vision.streaming_active:
        return "Streaming non attivo", 404
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

# ===== API ROUTES =====

@app.route('/api/status')
def api_status():
    return jsonify(jewelry_vision.get_status())

@app.route('/api/start_streaming', methods=['POST'])
def api_start_streaming():
    success, message = jewelry_vision.start_streaming()
    return jsonify({'success': success, 'message': message})

@app.route('/api/stop_streaming', methods=['POST'])
def api_stop_streaming():
    success, message = jewelry_vision.stop_streaming()
    return jsonify({'success': success, 'message': message})

@app.route('/api/start_monitoring', methods=['POST'])
def api_start_monitoring():
    success, message = jewelry_vision.start_monitoring()
    return jsonify({'success': success, 'message': message})

@app.route('/api/stop_monitoring', methods=['POST'])
def api_stop_monitoring():
    success, message = jewelry_vision.stop_monitoring()
    return jsonify({'success': success, 'message': message})

@app.route('/api/capture_frame', methods=['POST'])
def api_capture_frame():
    success, message = jewelry_vision.capture_frame()
    return jsonify({'success': success, 'message': message})

@app.route('/api/toggle_detection', methods=['POST'])
def api_toggle_detection():
    success, message = jewelry_vision.toggle_detection()
    return jsonify({'success': success, 'message': message})

@app.route('/api/toggle_alerts', methods=['POST'])
def api_toggle_alerts():
    success, message = jewelry_vision.toggle_alerts()
    return jsonify({'success': success, 'message': message})

@app.route('/api/test_alarm', methods=['POST'])
def api_test_alarm():
    success, message = jewelry_vision.test_alarm()
    return jsonify({'success': success, 'message': message})

@app.route('/api/start_recording', methods=['POST'])
def api_start_recording():
    success, message = jewelry_vision.start_recording()
    return jsonify({'success': success, 'message': message})

@app.route('/api/stop_recording', methods=['POST'])
def api_stop_recording():
    success, message = jewelry_vision.stop_recording()
    return jsonify({'success': success, 'message': message})

def cleanup_on_exit():
    """Cleanup quando il server si chiude"""
    print("🧹 Cleanup risorse...")
    jewelry_vision.release_camera()

def signal_handler(sig, frame):
    """Handler per shutdown graceful"""
    print('\n🛑 Shutdown richiesto...')
    cleanup_on_exit()
    sys.exit(0)

@app.route('/scenario_manager')
def scenario_manager():
    """Interfaccia scenario manager"""
    return render_template('scenario_manager.html')
# AGGIUNGI QUESTO ENDPOINT PRIMA DEL if __name__ == '__main__':
@app.route('/detection_feed')
def detection_feed():
    """Feed video con detection YOLO - OTTIMIZZATO PER JETSON L4T"""
    
    def generate_frames():
        print("🎯 Avvio detection feed per Jetson...")
        
        while jewelry_vision.monitoring_active:
            try:
                # Verifica che la camera sia disponibile
                if jewelry_vision.cap is None:
                    print("❌ Camera non disponibile per detection feed")
                    break
                    
                success, frame = jewelry_vision.cap.read()
                if not success:
                    print("❌ Impossibile leggere frame dalla camera")
                    time.sleep(0.1)
                    continue
                
                # Copia il frame originale per le modifiche
                detection_frame = frame.copy()
                
                # RIDIMENSIONA per migliorare performance su Jetson
                height, width = detection_frame.shape[:2]
                if width > 640:
                    scale = 640.0 / width
                    new_width = 640
                    new_height = int(height * scale)
                    detection_frame = cv2.resize(detection_frame, (new_width, new_height))
                
                # Applica detection YOLO se disponibile
                try:
                    if hasattr(jewelry_vision, 'yolo_model') and jewelry_vision.yolo_model is not None:
                        # Esegui detection
                        results = jewelry_vision.yolo_model(detection_frame, conf=0.5, verbose=False)
                        
                        # Disegna i risultati
                        for r in results:
                            boxes = r.boxes
                            if boxes is not None:
                                for box in boxes:
                                    # Estrai coordinate
                                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                                    conf = box.conf[0].cpu().numpy()
                                    cls = int(box.cls[0].cpu().numpy())
                                    class_name = jewelry_vision.yolo_model.names[cls]
                                    
                                    # Scegli colore in base alla classe
                                    if class_name == 'person':
                                        color = (0, 255, 0)  # Verde per persone
                                    else:
                                        color = (0, 0, 255)  # Rosso per altri oggetti
                                    
                                    # Disegna bounding box più spesso per Jetson
                                    cv2.rectangle(detection_frame, (x1, y1), (x2, y2), color, 3)
                                    
                                    # Aggiungi etichetta con background
                                    label = f'{class_name}: {conf:.2f}'
                                    label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
                                    cv2.rectangle(detection_frame, (x1, y1-label_size[1]-15), 
                                                (x1+label_size[0]+10, y1), color, -1)
                                    cv2.putText(detection_frame, label, (x1+5, y1-5),
                                              cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    else:
                        # Se non c'è il modello YOLO, mostra solo la camera
                        cv2.putText(detection_frame, "MONITORING - Caricamento modello...", 
                                  (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 165, 0), 2)
                        
                except Exception as e:
                    print(f"Errore durante detection: {e}")
                    # Continua comunque con il frame normale
                
                # Aggiungi overlay informativi con font più grandi per Jetson
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                cv2.putText(detection_frame, f"JETSON DETECTION - {timestamp}", 
                          (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                
                # Aggiungi indicatore stato
                status_text = "MONITORING ATTIVO" if jewelry_vision.monitoring_active else "MONITORING INATTIVO"
                status_color = (0, 255, 0) if jewelry_vision.monitoring_active else (0, 0, 255)
                cv2.putText(detection_frame, status_text, 
                          (10, detection_frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.8, status_color, 2)
                
                # ENCODING OTTIMIZZATO PER JETSON
                # Usa qualità più alta e parametri specifici per L4T
                encode_param = [
                    int(cv2.IMWRITE_JPEG_QUALITY), 90,  # Qualità alta
                    int(cv2.IMWRITE_JPEG_OPTIMIZE), 1,   # Ottimizzazione
                    int(cv2.IMWRITE_JPEG_PROGRESSIVE), 1  # Progressive JPEG
                ]
                
                result, buffer = cv2.imencode('.jpg', detection_frame, encode_param)
                
                if result:
                    frame_bytes = buffer.tobytes()
                    
                    # HEADERS SPECIFICI PER JETSON/L4T
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n'
                           b'Content-Length: ' + str(len(frame_bytes)).encode() + b'\r\n'
                           b'Cache-Control: no-cache\r\n'
                           b'Connection: keep-alive\r\n'
                           b'\r\n' + frame_bytes + b'\r\n')
                else:
                    print("❌ Errore encoding frame")
                    continue
                
                # Pausa ottimizzata per Jetson (15 FPS per ridurre carico)
                time.sleep(0.066)
                
            except Exception as e:
                print(f"❌ Errore nel loop detection feed: {e}")
                time.sleep(0.1)
                continue
        
        print("🛑 Detection feed terminato")
    
    print("📡 Richiesta detection feed ricevuta (Jetson Mode)")
    
    # RESPONSE HEADERS OTTIMIZZATI PER JETSON
    response = Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame',
        headers={
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*'
        }
    )
    
    return response
@app.route('/api/monitoring_status')
def api_monitoring_status():
    """Stato dettagliato del sistema di monitoring"""
    return jsonify({
        'monitoring_active': jewelry_vision.monitoring_active,
        'detection_enabled': jewelry_vision.detection_enabled,
        'model_loaded': hasattr(jewelry_vision, 'yolo_model') and jewelry_vision.yolo_model is not None,
        'camera_available': jewelry_vision.cap is not None,
        'stats': jewelry_vision.system_stats,
        'timestamp': time.time()
    })

if __name__ == '__main__':
    # Registra handler per cleanup
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        print("🚀 Avvio Jewelry Vision Web Server...")
        print("📱 Menu principale: http://localhost:5000")
        print("📹 Video streaming: http://localhost:5000/surveillance")  
        print("🎯 Detection monitoring: http://localhost:5000/monitoring")
        
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,
            threaded=True,
            use_reloader=False
        )
    except KeyboardInterrupt:
        print("\n🛑 Server fermato da utente")
    finally:
        cleanup_on_exit()
