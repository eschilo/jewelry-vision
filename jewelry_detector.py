#!/usr/bin/env python3
"""
Sistema di Rilevamento Gioielli - Versione 1.0
Jetson Orin Nano Super + YOLO11 + OpenCV

Funzionalità:
- Rilevamento oggetti in tempo reale
- Modalità calibrazione (stato di riferimento)  
- Modalità monitoraggio sicurezza
- Preprocessing anti-riflessi
- Interfaccia interattiva

Autori: Team Jewelry Vision
Data: Settembre 2024
"""

import cv2
import numpy as np
import time
from datetime import datetime
from ultralytics import YOLO
import json
import os

class JewelryVisionSystem:
    def __init__(self):
        print("🔍 Inizializzazione Sistema Jewelry Vision...")
        
        # Configurazione
        self.camera_id = 0
        self.confidence_threshold = 0.5
        self.reference_state = {}
        self.current_objects = []
        self.is_calibrated = False
        self.monitoring = False
        
        # Carica modello YOLO11
        print("📥 Caricamento YOLO11...")
        self.model = YOLO('yolo11n.pt')
        print("✅ Modello caricato")
        
        # Inizializza telecamera
        print("📷 Inizializzazione telecamera...")
        self.cap = cv2.VideoCapture(self.camera_id)
        if not self.cap.isOpened():
            raise Exception("❌ Errore apertura telecamera")
            
        # Imposta risoluzione ottimale
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        print("✅ Telecamera inizializzata")
        print("🎯 Sistema pronto!")
    
    def preprocess_frame(self, frame):
        """Preprocessa frame per ridurre riflessi e migliorare detection"""
        # Conversione in LAB per lavorare sulla luminanza
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Applica CLAHE per equalizzazione adattiva
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        l_enhanced = clahe.apply(l)
        
        # Riduce highlights estremi (anti-riflessi)
        l_enhanced = np.clip(l_enhanced, 0, 240)
        
        # Ricompone
        lab_enhanced = cv2.merge([l_enhanced, a, b])
        enhanced_frame = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)
        
        return enhanced_frame
    
    def detect_objects(self, frame):
        """Rileva oggetti nel frame usando YOLO11"""
        # Preprocessa per migliorare detection
        processed_frame = self.preprocess_frame(frame)
        
        # Inferenza YOLO
        results = self.model(processed_frame, conf=self.confidence_threshold, verbose=False)
        
        # Estrai detections
        detections = []
        if results and len(results) > 0 and results[0].boxes is not None:
            boxes = results[0].boxes
            for box in boxes:
                # Coordinate bbox
                x1, y1, x2, y2 = map(int, box.xyxy[0].cpu().numpy())
                confidence = float(box.conf[0].cpu().numpy())
                class_id = int(box.cls[0].cpu().numpy())
                class_name = self.model.names[class_id]
                
                detection = {
                    'bbox': [x1, y1, x2, y2],
                    'confidence': confidence,
                    'class_name': class_name,
                    'class_id': class_id,
                    'center': [(x1+x2)//2, (y1+y2)//2],
                    'area': (x2-x1) * (y2-y1)
                }
                detections.append(detection)
        
        return detections, processed_frame
    
    def draw_detections(self, frame, detections, title="Detection"):
        """Disegna bounding boxes e info sulle detection"""
        annotated_frame = frame.copy()
        
        # Titolo
        cv2.putText(annotated_frame, title, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        # Info generale
        info_text = f"Oggetti rilevati: {len(detections)}"
        cv2.putText(annotated_frame, info_text, (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Disegna ogni detection
        for i, det in enumerate(detections):
            x1, y1, x2, y2 = det['bbox']
            conf = det['confidence']
            class_name = det['class_name']
            
            # Bbox colorato
            color = (0, 255, 0)  # Verde per oggetti rilevati
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
            
            # Label con confidence
            label = f"{class_name}: {conf:.2f}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)[0]
            
            # Background per label
            cv2.rectangle(annotated_frame, (x1, y1-20), (x1 + label_size[0], y1), color, -1)
            cv2.putText(annotated_frame, label, (x1, y1-5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
            
            # Numero oggetto
            cv2.putText(annotated_frame, str(i+1), (x1+5, y1+20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
        
        return annotated_frame
    
    def calibrate_reference(self):
        """Calibra lo stato di riferimento (tutti gli oggetti presenti)"""
        print("\n🎯 MODALITÀ CALIBRAZIONE")
        print("Posizionate tutti i gioielli da monitorare e premete SPAZIO per calibrare")
        print("Premete ESC per annullare")
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                continue
                
            # Rileva oggetti
            detections, processed_frame = self.detect_objects(frame)
            
            # Disegna detection
            display_frame = self.draw_detections(frame, detections, "CALIBRAZIONE - SPAZIO per confermare")
            
            # Mostra
            cv2.imshow('Jewelry Calibration', display_frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord(' '):  # SPAZIO per calibrare
                if len(detections) > 0:
                    self.reference_state = {
                        'timestamp': datetime.now().isoformat(),
                        'total_objects': len(detections),
                        'objects': detections.copy(),
                        'categories': {}
                    }
                    
                    # Conta per categoria
                    for det in detections:
                        cat = det['class_name']
                        self.reference_state['categories'][cat] = self.reference_state['categories'].get(cat, 0) + 1
                    
                    self.is_calibrated = True
                    print(f"\n✅ CALIBRAZIONE COMPLETATA!")
                    print(f"📦 Oggetti di riferimento: {len(detections)}")
                    print("📋 Categorie rilevate:")
                    for cat, count in self.reference_state['categories'].items():
                        print(f"   - {cat}: {count}")
                    
                    # Salva stato di riferimento
                    self.save_reference_state()
                    break
                else:
                    print("⚠️ Nessun oggetto rilevato. Riposizionate i gioielli.")
                    
            elif key == 27:  # ESC per uscire
                print("❌ Calibrazione annullata")
                break
        
        cv2.destroyAllWindows()
    
    def save_reference_state(self):
        """Salva lo stato di riferimento su file"""
        os.makedirs('data/reference', exist_ok=True)
        with open('data/reference/reference_state.json', 'w') as f:
            json.dump(self.reference_state, f, indent=2)
        print("💾 Stato di riferimento salvato")
    
    def load_reference_state(self):
        """Carica stato di riferimento da file"""
        try:
            with open('data/reference/reference_state.json', 'r') as f:
                self.reference_state = json.load(f)
            self.is_calibrated = True
            print("📂 Stato di riferimento caricato")
            print(f"📦 Oggetti di riferimento: {self.reference_state['total_objects']}")
            return True
        except FileNotFoundError:
            print("⚠️ File stato di riferimento non trovato")
            return False
    
    def monitor_security(self):
        """Modalità monitoraggio sicurezza"""
        if not self.is_calibrated:
            print("❌ Sistema non calibrato! Esegui prima la calibrazione.")
            return
        
        print("\n👁️ MODALITÀ MONITORAGGIO SICUREZZA")
        print("Premete ESC per uscire")
        print(f"📦 Oggetti di riferimento: {self.reference_state['total_objects']}")
        
        alert_count = 0
        frame_count = 0
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                continue
            
            frame_count += 1
            
            # Rileva oggetti attuali
            detections, processed_frame = self.detect_objects(frame)
            current_count = len(detections)
            reference_count = self.reference_state['total_objects']
            
            # Analizza differenza
            missing_objects = reference_count - current_count
            
            # Determina stato
            if missing_objects > 0:
                status = "🚨 ALERT"
                status_color = (0, 0, 255)  # Rosso
                alert_count += 1
            elif missing_objects < 0:
                status = "⚠️ EXTRA"
                status_color = (0, 165, 255)  # Arancione
            else:
                status = "✅ OK"
                status_color = (0, 255, 0)  # Verde
                alert_count = 0
            
            # Disegna detection
            title = f"SECURITY - {status} | Rif: {reference_count} | Att: {current_count}"
            display_frame = self.draw_detections(frame, detections, title)
            
            # Info stato in alto
            status_text = f"Status: {status}"
            if missing_objects != 0:
                status_text += f" | Differenza: {abs(missing_objects)}"
            
            cv2.putText(display_frame, status_text, (10, 90), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
            
            # Timestamp
            timestamp = datetime.now().strftime("%H:%M:%S")
            cv2.putText(display_frame, f"Time: {timestamp}", (10, 120), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            # Alert persistente
            if alert_count > 5:  # Alert per 5 frame consecutivi
                cv2.rectangle(display_frame, (0, 0), (display_frame.shape[1], 50), (0, 0, 255), -1)
                cv2.putText(display_frame, "SECURITY ALERT!", (20, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                
                # Log alert
                if frame_count % 30 == 0:  # Log ogni secondo circa
                    print(f"🚨 ALERT: {missing_objects} oggetti mancanti alle {timestamp}")
            
            # Mostra
            cv2.imshow('Jewelry Security Monitor', display_frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC per uscire
                break
        
        cv2.destroyAllWindows()
    
    def live_detection(self):
        """Modalità detection live per test"""
        print("\n📹 MODALITÀ DETECTION LIVE")
        print("Premete ESC per uscire")
        
        fps_count = 0
        fps_time = time.time()
        
        while True:
            ret, frame = self.cap.read()
            if not ret:
                continue
            
            fps_count += 1
            
            # Detection
            detections, processed_frame = self.detect_objects(frame)
            
            # Disegna
            display_frame = self.draw_detections(frame, detections, "LIVE DETECTION")
            
            # FPS
            if time.time() - fps_time >= 1.0:
                fps = fps_count / (time.time() - fps_time)
                fps_count = 0
                fps_time = time.time()
                
            cv2.putText(display_frame, f"FPS: {fps:.1f}", (10, 150), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            
            cv2.imshow('Jewelry Live Detection', display_frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                break
        
        cv2.destroyAllWindows()
    
    def run_menu(self):
        """Menu principale interattivo"""
        while True:
            print("\n" + "="*60)
            print("🔍 SISTEMA JEWELRY VISION - MENU PRINCIPALE")
            print("="*60)
            print("1. 📹 Test Detection Live")
            print("2. 🎯 Calibrazione Sistema (definisci stato riferimento)")
            print("3. 👁️  Monitoraggio Sicurezza")
            print("4. 📂 Carica Calibrazione Esistente")
            print("5. 📊 Stato Sistema")
            print("0. 🚪 Esci")
            print("="*60)
            
            try:
                choice = input("Scegli opzione: ").strip()
                
                if choice == "1":
                    self.live_detection()
                    
                elif choice == "2":
                    self.calibrate_reference()
                    
                elif choice == "3":
                    self.monitor_security()
                    
                elif choice == "4":
                    self.load_reference_state()
                    
                elif choice == "5":
                    print(f"\n📊 STATO SISTEMA:")
                    print(f"🎯 Calibrato: {'✅ Sì' if self.is_calibrated else '❌ No'}")
                    if self.is_calibrated:
                        print(f"📦 Oggetti riferimento: {self.reference_state['total_objects']}")
                        print(f"📅 Data calibrazione: {self.reference_state['timestamp']}")
                        print("📋 Categorie:")
                        for cat, count in self.reference_state['categories'].items():
                            print(f"   - {cat}: {count}")
                    
                elif choice == "0":
                    print("👋 Arrivederci!")
                    break
                    
                else:
                    print("❌ Opzione non valida")
                    
            except KeyboardInterrupt:
                print("\n👋 Interruzione utente")
                break
    
    def cleanup(self):
        """Pulizia risorse"""
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        print("🧹 Risorse rilasciate")

def main():
    """Funzione principale"""
    print("=" * 80)
    print("🔍 SISTEMA DI VISIONE ARTIFICIALE PER GIOIELLI")
    print("   Jetson Orin Nano Super + YOLO11 + OpenCV")
    print("   Versione 1.0 - Sistema Base Funzionante")
    print("=" * 80)
    
    try:
        # Inizializza sistema
        system = JewelryVisionSystem()
        
        # Avvia menu
        system.run_menu()
        
    except Exception as e:
        print(f"❌ Errore: {e}")
    finally:
        try:
            system.cleanup()
        except:
            pass

if __name__ == "__main__":
    main()
