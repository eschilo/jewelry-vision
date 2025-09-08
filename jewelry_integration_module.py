#!/usr/bin/env python3
"""
🎯 JEWELRY DETECTION ENGINE
Sistema di detection specializzato per gioielli con tracking inventario e allarmi
Integrazione con il sistema Jewelry Vision esistente
"""

import cv2
import numpy as np
import torch
from ultralytics import YOLO
import json
import datetime
import logging
from typing import Dict, List, Tuple, Optional
import threading
import time
import os

class JewelryIntegrationModule:
    """
    Modulo di integrazione per il sistema Jewelry Vision esistente
    Estende le funzionalità di detection per gioielli specifici
    """
    
    def __init__(self, existing_model=None):
        """
        Inizializza il modulo di integrazione
        
        Args:
            existing_model: Modello YOLO esistente del sistema principale
        """
        self.existing_model = existing_model
        self.jewelry_model = None
        
        # Configurazione classi gioielli
        self.jewelry_classes = {
            # Classi COCO standard utili
            0: "person",
            24: "handbag", 
            26: "backpack",
            28: "suitcase",
            # Classi personalizzate gioielli (aggiunte)
            80: "ring",
            81: "necklace", 
            82: "bracelet",
            83: "earrings",
            84: "watch",
            85: "brooch",
            86: "chain",
            87: "pendant"
        }
        
        # Sistema inventario
        self.inventory = {}
        self.baseline_inventory = {}
        self.alerts = []
        self.tracking_active = False
        self.detection_history = []
        
        # Configurazioni
        self.config = {
            "confidence_threshold": 0.4,
            "jewelry_confidence": 0.3,  # Soglia più bassa per gioielli
            "tracking_tolerance": 50,
            "alert_timeout": 5.0,
            "save_detections": True,
            "log_enabled": True
        }
        
        # Setup logging
        self._setup_logging()
        
        # Inizializza modello jewelry se non esiste
        self._initialize_jewelry_model()
        
        self.logger.info("🎯 Jewelry Integration Module inizializzato")

    def _setup_logging(self):
        """Setup logging per il modulo"""
        self.logger = logging.getLogger('JewelryIntegration')
        self.logger.setLevel(logging.INFO)
        
        # Handler per file se non esiste
        if not self.logger.handlers:
            os.makedirs('logs', exist_ok=True)
            handler = logging.FileHandler('logs/jewelry_integration.log')
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def _initialize_jewelry_model(self):
        """Inizializza modello specifico per gioielli se necessario"""
        try:
            # Se abbiamo già un modello esistente, lo utilizziamo
            if self.existing_model:
                self.jewelry_model = self.existing_model
                self.logger.info("✅ Uso modello esistente per jewelry detection")
            else:
                # Carica modello YOLO11 standard
                self.jewelry_model = YOLO('yolo11n.pt')
                self.logger.info("✅ Modello YOLO11n caricato per jewelry detection")
                
        except Exception as e:
            self.logger.error(f"❌ Errore inizializzazione modello jewelry: {e}")

    def enhanced_detection(self, frame, original_detections=None):
        """
        Detection potenziata che integra detection standard + jewelry specifiche
        """
        try:
            # Esegui detection con modello
            results = self.jewelry_model(frame, 
                                       conf=self.config["confidence_threshold"],
                                       verbose=False)
            
            # Processa risultati
            jewelry_detections = []
            annotated_frame = frame.copy()
            
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        # Estrai informazioni
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        confidence = float(box.conf[0].cpu().numpy())
                        class_id = int(box.cls[0].cpu().numpy())
                        
                        # Determina se è una classe di interesse per gioielli
                        if self._is_jewelry_relevant(class_id, confidence):
                            class_name = self._get_class_name(class_id)
                            
                            # Crea detection object
                            detection = {
                                "id": f"{class_name}_{int((x1+x2)/2)}_{int((y1+y2)/2)}",
                                "class": class_name,
                                "class_id": class_id,
                                "confidence": confidence,
                                "bbox": [int(x1), int(y1), int(x2), int(y2)],
                                "center": [int((x1+x2)/2), int((y1+y2)/2)],
                                "area": int((x2-x1) * (y2-y1)),
                                "timestamp": datetime.datetime.now().isoformat(),
                                "is_jewelry": self._is_jewelry_class(class_id),
                                "security_relevant": self._is_security_relevant(class_id)
                            }
                            
                            jewelry_detections.append(detection)
                            
                            # Annota frame con stile jewelry-specific
                            annotated_frame = self._annotate_jewelry_detection(
                                annotated_frame, detection
                            )
            
            # Update inventory se tracking attivo
            if self.tracking_active:
                self._update_jewelry_inventory(jewelry_detections)
                self._check_jewelry_alerts()
            
            # Crea status report
            status = self._create_status_report(jewelry_detections)
            
            return annotated_frame, jewelry_detections, status
            
        except Exception as e:
            self.logger.error(f"Errore enhanced detection: {e}")
            return frame, [], {"error": str(e)}

    def _is_jewelry_relevant(self, class_id, confidence):
        """Determina se una detection è rilevante per jewelry monitoring"""
        # Gioielli: soglia di confidenza più bassa
        if self._is_jewelry_class(class_id):
            return confidence >= self.config["jewelry_confidence"]
        
        # Sicurezza (persone, borse): soglia standard
        if self._is_security_relevant(class_id):
            return confidence >= self.config["confidence_threshold"]
        
        return False

    def _is_jewelry_class(self, class_id):
        """Verifica se è una classe di gioiello"""
        jewelry_ids = [80, 81, 82, 83, 84, 85, 86, 87]  # ring, necklace, etc.
        return class_id in jewelry_ids

    def _is_security_relevant(self, class_id):
        """Verifica se è una classe rilevante per sicurezza"""
        security_ids = [0, 24, 26, 28]  # person, handbag, backpack, suitcase
        return class_id in security_ids

    def _get_class_name(self, class_id):
        """Ottiene nome classe da ID"""
        return self.jewelry_classes.get(class_id, f"unknown_{class_id}")

    def _annotate_jewelry_detection(self, frame, detection):
        """Annotazione specifica per jewelry detection"""
        x1, y1, x2, y2 = detection["bbox"]
        class_name = detection["class"]
        confidence = detection["confidence"]
        is_jewelry = detection["is_jewelry"]
        
        # Colori specifici per gioielli
        if is_jewelry:
            colors = {
                "ring": (255, 215, 0),       # Oro
                "necklace": (255, 20, 147),  # Rosa acceso
                "bracelet": (0, 255, 255),   # Ciano
                "earrings": (255, 105, 180), # Rosa chiaro
                "watch": (128, 0, 128),      # Viola
                "brooch": (255, 165, 0),     # Arancione
                "chain": (255, 255, 0),      # Giallo
                "pendant": (255, 192, 203),  # Rosa
            }
            color = colors.get(class_name, (0, 255, 0))
            thickness = 3  # Più spesso per gioielli
        else:
            # Colori per sicurezza
            colors = {
                "person": (0, 0, 255),    # Rosso - IMPORTANTE
                "handbag": (255, 140, 0), # Arancione scuro
                "backpack": (255, 69, 0), # Rosso-arancione
                "suitcase": (220, 20, 60) # Cremisi
            }
            color = colors.get(class_name, (128, 128, 128))
            thickness = 2
        
        # Disegna bounding box
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)
        
        # Label con icona per gioielli
        if is_jewelry:
            label = f"💎 {class_name}: {confidence:.2f}"
        else:
            label = f"🚨 {class_name}: {confidence:.2f}"
            
        # Background e testo label
        label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
        cv2.rectangle(frame, 
                     (x1, y1 - label_size[1] - 10), 
                     (x1 + label_size[0], y1), 
                     color, -1)
        
        cv2.putText(frame, label, (x1, y1 - 5), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Punto centrale con indicatore speciale per gioielli
        center_x, center_y = detection["center"]
        if is_jewelry:
            cv2.circle(frame, (center_x, center_y), 5, color, -1)
            cv2.circle(frame, (center_x, center_y), 8, color, 2)
        else:
            cv2.circle(frame, (center_x, center_y), 3, color, -1)
        
        return frame

    def _update_jewelry_inventory(self, detections):
        """Aggiorna inventario jewelry con tracking intelligente"""
        current_time = datetime.datetime.now().isoformat()
        new_inventory = {}
        
        # Processa detection attuali
        for detection in detections:
            if detection["is_jewelry"]:
                item_id = self._generate_item_id(detection)
                
                # Cerca corrispondenza con oggetti esistenti
                matched_item = self._find_matching_item(detection)
                
                if matched_item:
                    # Update oggetto esistente
                    new_inventory[matched_item["id"]] = {
                        **matched_item,
                        "last_seen": current_time,
                        "confidence": detection["confidence"],
                        "center": detection["center"],
                        "status": "present",
                        "detection_count": matched_item.get("detection_count", 0) + 1
                    }
                else:
                    # Nuovo oggetto
                    new_inventory[item_id] = {
                        **detection,
                        "first_seen": current_time,
                        "last_seen": current_time,
                        "status": "present",
                        "detection_count": 1,
                        "stable": False
                    }
        
        # Marca oggetti mancanti
        for item_id, item in self.inventory.items():
            if item_id not in new_inventory and item.get("is_jewelry", False):
                item["status"] = "missing"
                item["missing_since"] = current_time
                new_inventory[item_id] = item
        
        self.inventory = new_inventory

    def _find_matching_item(self, detection):
        """Trova oggetto corrispondente nell'inventario esistente"""
        for item in self.inventory.values():
            if (item.get("class") == detection["class"] and
                item.get("status") == "present" and
                self._calculate_distance(item["center"], detection["center"]) <= self.config["tracking_tolerance"]):
                return item
        return None

    def _calculate_distance(self, point1, point2):
        """Calcola distanza euclidea tra due punti"""
        return np.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

    def _generate_item_id(self, detection):
        """Genera ID univoco per item"""
        return f"{detection['class']}_{detection['center'][0]}_{detection['center'][1]}_{int(time.time())}"

    def _check_jewelry_alerts(self):
        """Sistema di allarmi intelligente per gioielli"""
        current_time = datetime.datetime.now()
        new_alerts = []
        
        # Controlla oggetti mancanti dal baseline
        missing_from_baseline = self._check_missing_from_baseline()
        new_alerts.extend(missing_from_baseline)
        
        # Controlla nuovi oggetti non autorizzati
        unauthorized_items = self._check_unauthorized_items()
        new_alerts.extend(unauthorized_items)
        
        # Controlla detection con bassa confidenza
        low_confidence_alerts = self._check_low_confidence()
        new_alerts.extend(low_confidence_alerts)
        
        # Controlla attività sospette (persone + manipolazione gioielli)
        suspicious_activity = self._check_suspicious_activity()
        new_alerts.extend(suspicious_activity)
        
        # Aggiungi nuovi allarmi
        self.alerts.extend(new_alerts)
        self.alerts = self.alerts[-50:]  # Mantieni ultimi 50
        
        # Log allarmi critici
        for alert in new_alerts:
            if alert["severity"] in ["HIGH", "CRITICAL"]:
                self.logger.warning(f"🚨 {alert['type']}: {alert['message']}")

    def _check_missing_from_baseline(self):
        """Controlla oggetti mancanti dal baseline"""
        alerts = []
        
        if not self.baseline_inventory:
            return alerts
            
        for baseline_id, baseline_item in self.baseline_inventory.items():
            if baseline_item.get("is_jewelry", False):
                found = any(
                    self._items_match(baseline_item, current_item)
                    for current_item in self.inventory.values()
                    if current_item.get("status") == "present"
                )
                
                if not found:
                    alerts.append({
                        "type": "MISSING_JEWELRY",
                        "message": f"Gioiello mancante: {baseline_item['class']}",
                        "item": baseline_item,
                        "timestamp": datetime.datetime.now().isoformat(),
                        "severity": "CRITICAL",
                        "action_required": True
                    })
        
        return alerts

    def _check_unauthorized_items(self):
        """Controlla nuovi oggetti non autorizzati"""
        alerts = []
        
        for item in self.inventory.values():
            if (item.get("is_jewelry", False) and 
                item.get("status") == "present" and
                item.get("detection_count", 0) > 3):  # Stabile
                
                # Verifica se è nel baseline
                found_in_baseline = any(
                    self._items_match(item, baseline_item)
                    for baseline_item in self.baseline_inventory.values()
                )
                
                if not found_in_baseline:
                    alerts.append({
                        "type": "NEW_JEWELRY",
                        "message": f"Nuovo gioiello rilevato: {item['class']}",
                        "item": item,
                        "timestamp": datetime.datetime.now().isoformat(),
                        "severity": "HIGH",
                        "action_required": True
                    })
        
        return alerts

    def _check_low_confidence(self):
        """Controlla detection con bassa confidenza"""
        alerts = []
        
        for item in self.inventory.values():
            if (item.get("is_jewelry", False) and
                item.get("confidence", 1.0) < 0.3 and
                item.get("status") == "present"):
                
                alerts.append({
                    "type": "LOW_CONFIDENCE_JEWELRY",
                    "message": f"Detection incerta: {item['class']} ({item['confidence']:.2f})",
                    "item": item,
                    "timestamp": datetime.datetime.now().isoformat(),
                    "severity": "MEDIUM",
                    "action_required": False
                })
        
        return alerts

    def _check_suspicious_activity(self):
        """Controlla attività sospette (persone + gioielli)"""
        alerts = []
        
        # Conta persone e gioielli presenti
        people_count = sum(1 for item in self.inventory.values() 
                          if item.get("class") == "person" and item.get("status") == "present")
        
        jewelry_count = sum(1 for item in self.inventory.values()
                           if item.get("is_jewelry", False) and item.get("status") == "present")
        
        # Allarme se persone presenti ma gioielli mancanti
        if people_count > 0 and jewelry_count < len(self.baseline_inventory) * 0.8:
            alerts.append({
                "type": "SUSPICIOUS_ACTIVITY",
                "message": f"Persone presenti ({people_count}) con gioielli ridotti ({jewelry_count})",
                "timestamp": datetime.datetime.now().isoformat(),
                "severity": "HIGH",
                "action_required": True,
                "details": {
                    "people_count": people_count,
                    "jewelry_present": jewelry_count,
                    "jewelry_expected": len(self.baseline_inventory)
                }
            })
        
        return alerts

    def _items_match(self, item1, item2, tolerance=None):
        """Verifica corrispondenza tra due oggetti"""
        if tolerance is None:
            tolerance = self.config["tracking_tolerance"]
            
        return (item1.get("class") == item2.get("class") and
                self._calculate_distance(item1.get("center", [0,0]), 
                                       item2.get("center", [0,0])) <= tolerance)

    def _create_status_report(self, detections):
        """Crea report status completo"""
        jewelry_items = [d for d in detections if d["is_jewelry"]]
        security_items = [d for d in detections if d["security_relevant"]]
        
        return {
            "timestamp": datetime.datetime.now().isoformat(),
            "total_detections": len(detections),
            "jewelry_detections": len(jewelry_items),
            "security_detections": len(security_items),
            "inventory_status": {
                "total_items": len(self.inventory),
                "present_jewelry": len([i for i in self.inventory.values() 
                                      if i.get("is_jewelry") and i.get("status") == "present"]),
                "missing_jewelry": len([i for i in self.inventory.values()
                                      if i.get("is_jewelry") and i.get("status") == "missing"]),
                "baseline_count": len(self.baseline_inventory)
            },
            "alerts": {
                "total": len(self.alerts),
                "critical": len([a for a in self.alerts if a.get("severity") == "CRITICAL"]),
                "high": len([a for a in self.alerts if a.get("severity") == "HIGH"]),
                "recent": self.alerts[-5:] if self.alerts else []
            },
            "tracking_active": self.tracking_active
        }

    # API Methods per integrazione Flask
    def start_jewelry_tracking(self):
        """Avvia tracking jewelry"""
        self.tracking_active = True
        self.logger.info("🎯 Jewelry tracking AVVIATO")
        return {"status": "success", "message": "Jewelry tracking avviato"}

    def stop_jewelry_tracking(self):
        """Ferma tracking jewelry"""
        self.tracking_active = False
        self.logger.info("⏹️ Jewelry tracking FERMATO")
        return {"status": "success", "message": "Jewelry tracking fermato"}

    def save_jewelry_baseline(self):
        """Salva baseline inventory corrente"""
        try:
            # Filtra solo oggetti jewelry presenti e stabili
            stable_jewelry = {
                item_id: item for item_id, item in self.inventory.items()
                if (item.get("is_jewelry", False) and 
                    item.get("status") == "present" and
                    item.get("detection_count", 0) >= 3)
            }
            
            os.makedirs('data/inventory', exist_ok=True)
            baseline_path = 'data/inventory/jewelry_baseline.json'
            
            with open(baseline_path, 'w') as f:
                json.dump(stable_jewelry, f, indent=2)
            
            self.baseline_inventory = stable_jewelry.copy()
            
            self.logger.info(f"💾 Jewelry baseline salvato: {len(stable_jewelry)} oggetti")
            return {
                "status": "success", 
                "message": f"Baseline salvato con {len(stable_jewelry)} gioielli",
                "baseline_count": len(stable_jewelry)
            }
            
        except Exception as e:
            self.logger.error(f"Errore salvataggio baseline: {e}")
            return {"status": "error", "message": str(e)}

    def load_jewelry_baseline(self):
        """Carica baseline inventory"""
        try:
            baseline_path = 'data/inventory/jewelry_baseline.json'
            if os.path.exists(baseline_path):
                with open(baseline_path, 'r') as f:
                    self.baseline_inventory = json.load(f)
                
                self.logger.info(f"📦 Jewelry baseline caricato: {len(self.baseline_inventory)} oggetti")
                return {
                    "status": "success",
                    "message": f"Baseline caricato con {len(self.baseline_inventory)} gioielli",
                    "baseline_count": len(self.baseline_inventory)
                }
            else:
                return {"status": "warning", "message": "Nessun baseline trovato"}
                
        except Exception as e:
            self.logger.error(f"Errore caricamento baseline: {e}")
            return {"status": "error", "message": str(e)}

    def get_jewelry_status(self):
        """Ottieni status completo jewelry system"""
        return self._create_status_report([])

    def clear_jewelry_alerts(self):
        """Pulisce allarmi jewelry"""
        self.alerts.clear()
        self.logger.info("🧹 Allarmi jewelry puliti")
        return {"status": "success", "message": "Allarmi puliti"}

    def export_jewelry_data(self):
        """Esporta dati jewelry per backup"""
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            export_path = f'data/exports/jewelry_export_{timestamp}.json'
            
            export_data = {
                "export_timestamp": datetime.datetime.now().isoformat(),
                "inventory": self.inventory,
                "baseline_inventory": self.baseline_inventory,
                "alerts": self.alerts,
                "config": self.config,
                "detection_history": self.detection_history[-100:]
            }
            
            os.makedirs(os.path.dirname(export_path), exist_ok=True)
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            self.logger.info(f"📤 Dati jewelry esportati: {export_path}")
            return {
                "status": "success",
                "message": "Dati esportati con successo",
                "export_path": export_path
            }
            
        except Exception as e:
            self.logger.error(f"Errore esportazione: {e}")
            return {"status": "error", "message": str(e)}
