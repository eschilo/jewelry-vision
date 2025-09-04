#!/usr/bin/env python3
"""
Jewelry Dataset Collection System
Sistema completo per raccolta e annotazione dataset gioielli
"""

import cv2
import os
import json
import time
import numpy as np
from datetime import datetime
from pathlib import Path
import threading
import queue
from typing import Dict, List, Tuple, Optional
import argparse

class JewelryDatasetCollector:
    def __init__(self, base_dir: str = "~/jewelry_vision/dataset"):
        self.base_dir = Path(base_dir).expanduser()
        self.setup_directories()
        
        # Categorie gioielli supportate
        self.categories = {
            0: "anello",
            1: "collana", 
            2: "orecchino",
            3: "braccialetto",
            4: "pendente",
            5: "spilla",
            6: "gemma",
            7: "orologio"
        }
        
        # Configurazione raccolta
        self.auto_capture = False
        self.capture_interval = 2.0  # secondi
        self.min_detection_confidence = 0.3
        self.current_category = 0
        
        # Stats
        self.stats = {cat: 0 for cat in self.categories.values()}
        self.session_captures = 0
        
        # UI state
        self.annotation_mode = False
        self.selected_bbox = None
        self.temp_bbox = None
        self.drawing = False
        
        self.load_existing_stats()
        
    def setup_directories(self):
        """Crea struttura directory dataset"""
        dirs = [
            "images/raw",
            "images/processed", 
            "annotations/yolo",
            "annotations/coco",
            "annotations/temp",
            "exports",
            "backups"
        ]
        
        for dir_path in dirs:
            full_path = self.base_dir / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            
        print(f"📁 Dataset directory: {self.base_dir}")
        
    def load_existing_stats(self):
        """Carica statistiche esistenti"""
        stats_file = self.base_dir / "collection_stats.json"
        if stats_file.exists():
            with open(stats_file, 'r') as f:
                data = json.load(f)
                self.stats.update(data.get('category_counts', {}))
                
    def save_stats(self):
        """Salva statistiche correnti"""
        stats_data = {
            'last_updated': datetime.now().isoformat(),
            'category_counts': self.stats,
            'total_images': sum(self.stats.values()),
            'session_captures': self.session_captures
        }
        
        with open(self.base_dir / "collection_stats.json", 'w') as f:
            json.dump(stats_data, f, indent=2)
            
    def generate_filename(self, category: str) -> str:
        """Genera nome file unico"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        count = self.stats[category] + 1
        return f"{category}_{count:04d}_{timestamp}"
        
    def save_image_with_metadata(self, image: np.ndarray, category: str, 
                                bbox: Optional[List] = None) -> str:
        """Salva immagine con metadati"""
        filename = self.generate_filename(category)
        
        # Salva immagine
        img_path = self.base_dir / "images/raw" / f"{filename}.jpg"
        cv2.imwrite(str(img_path), image)
        
        # Salva metadati
        metadata = {
            'filename': f"{filename}.jpg",
            'category': category,
            'category_id': [k for k, v in self.categories.items() if v == category][0],
            'timestamp': datetime.now().isoformat(),
            'image_size': list(image.shape[:2]),
            'bbox': bbox if bbox else [],
            'annotation_complete': bbox is not None
        }
        
        meta_path = self.base_dir / "annotations/temp" / f"{filename}.json"
        with open(meta_path, 'w') as f:
            json.dump(metadata, f, indent=2)
            
        # Aggiorna stats
        self.stats[category] += 1
        self.session_captures += 1
        self.save_stats()
        
        return filename
        
    def auto_capture_frame(self, frame: np.ndarray, detections: List) -> bool:
        """Cattura automatica se rileva oggetti"""
        if not self.auto_capture or len(detections) == 0:
            return False
            
        # Filtra detection per confidenza
        valid_detections = [d for d in detections if d['confidence'] > self.min_detection_confidence]
        
        if valid_detections:
            category = self.categories[self.current_category]
            
            # Prendi il bbox della detection migliore
            best_detection = max(valid_detections, key=lambda x: x['confidence'])
            bbox = [
                int(best_detection['x1']), int(best_detection['y1']),
                int(best_detection['x2']), int(best_detection['y2'])
            ]
            
            filename = self.save_image_with_metadata(frame, category, bbox)
            print(f"🤖 Auto-captured: {filename} ({category})")
            return True
            
        return False
        
    def manual_capture_frame(self, frame: np.ndarray) -> str:
        """Cattura manuale"""
        category = self.categories[self.current_category]
        bbox = None
        
        # Se c'è una selezione bbox, usala
        if self.selected_bbox:
            bbox = self.selected_bbox
            
        filename = self.save_image_with_metadata(frame, category, bbox)
        print(f"📸 Manual capture: {filename} ({category})")
        return filename
        
    def mouse_callback(self, event, x, y, flags, param):
        """Callback per selezione bbox con mouse"""
        if not self.annotation_mode:
            return
            
        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing = True
            self.temp_bbox = [x, y, x, y]
            
        elif event == cv2.EVENT_MOUSEMOVE and self.drawing:
            self.temp_bbox[2] = x
            self.temp_bbox[3] = y
            
        elif event == cv2.EVENT_LBUTTONUP:
            self.drawing = False
            if self.temp_bbox:
                # Normalizza bbox
                x1, y1, x2, y2 = self.temp_bbox
                self.selected_bbox = [min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)]
                self.temp_bbox = None
                
    def draw_ui_overlay(self, frame: np.ndarray) -> np.ndarray:
        """Disegna overlay UI"""
        overlay = frame.copy()
        h, w = frame.shape[:2]
        
        # Pannello informazioni
        info_panel = np.zeros((120, w, 3), dtype=np.uint8)
        
        # Categoria corrente
        category = self.categories[self.current_category]
        cv2.putText(info_panel, f"Categoria: {category.upper()}", (10, 25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        
        # Modalità
        mode = "AUTO" if self.auto_capture else "MANUAL"
        mode_color = (0, 255, 0) if self.auto_capture else (255, 255, 255)
        cv2.putText(info_panel, f"Modo: {mode}", (10, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, mode_color, 2)
        
        # Annotation mode
        if self.annotation_mode:
            cv2.putText(info_panel, "ANNOTATION MODE", (10, 75), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
        
        # Stats sessione
        cv2.putText(info_panel, f"Sessione: {self.session_captures}", (300, 25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Stats categoria corrente
        current_count = self.stats[category]
        cv2.putText(info_panel, f"{category}: {current_count}", (300, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Comandi
        cv2.putText(info_panel, "SPACE=Cattura | A=Auto | B=Annotation | 1-8=Categoria | Q=Quit", 
                   (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
        
        # Combina frame e pannello
        combined = np.vstack([info_panel, overlay])
        
        # Disegna bbox selezionato
        if self.selected_bbox:
            x1, y1, x2, y2 = self.selected_bbox
            cv2.rectangle(combined, (x1, y1+120), (x2, y2+120), (0, 255, 0), 2)
            cv2.putText(combined, category, (x1, y1+115), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Disegna bbox temporaneo
        if self.temp_bbox and self.drawing:
            x1, y1, x2, y2 = self.temp_bbox
            cv2.rectangle(combined, (x1, y1+120), (x2, y2+120), (255, 255, 0), 2)
            
        return combined
        
    def print_stats_summary(self):
        """Stampa riassunto statistiche"""
        print("\n" + "="*50)
        print("📊 DATASET COLLECTION STATS")
        print("="*50)
        
        total = sum(self.stats.values())
        print(f"Totale immagini: {total}")
        print(f"Sessione corrente: {self.session_captures}")
        print("\nPer categoria:")
        
        for cat_id, cat_name in self.categories.items():
            count = self.stats[cat_name]
            percentage = (count / total * 100) if total > 0 else 0
            print(f"  {cat_name:12}: {count:4d} ({percentage:5.1f}%)")
            
        print("="*50)
        
    def export_yolo_annotations(self):
        """Esporta annotazioni in formato YOLO"""
        print("\n🔄 Exporting YOLO annotations...")
        
        temp_dir = self.base_dir / "annotations/temp"
        yolo_dir = self.base_dir / "annotations/yolo"
        
        exported = 0
        
        for json_file in temp_dir.glob("*.json"):
            with open(json_file, 'r') as f:
                metadata = json.load(f)
                
            if not metadata.get('annotation_complete') or not metadata.get('bbox'):
                continue
                
            # Converti bbox in formato YOLO
            img_h, img_w = metadata['image_size']
            x1, y1, x2, y2 = metadata['bbox']
            
            # Normalizza coordinate
            center_x = (x1 + x2) / 2.0 / img_w
            center_y = (y1 + y2) / 2.0 / img_h
            width = (x2 - x1) / img_w
            height = (y2 - y1) / img_h
            
            # Salva annotazione YOLO
            yolo_file = yolo_dir / f"{json_file.stem}.txt"
            with open(yolo_file, 'w') as f:
                class_id = metadata['category_id']
                f.write(f"{class_id} {center_x:.6f} {center_y:.6f} {width:.6f} {height:.6f}\n")
                
            exported += 1
            
        print(f"✅ Exported {exported} YOLO annotations")
        
        # Genera classes.txt
        classes_file = yolo_dir / "classes.txt"
        with open(classes_file, 'w') as f:
            for i in range(len(self.categories)):
                f.write(f"{self.categories[i]}\n")
                
        print(f"📝 Generated {classes_file}")
        
    def run_collection_interface(self, camera_id: int = 0):
        """Avvia interfaccia di raccolta"""
        print("🎥 Starting Jewelry Dataset Collection Interface")
        print("📖 Controls:")
        print("  SPACE    - Capture image")
        print("  A        - Toggle auto-capture")
        print("  B        - Toggle annotation mode")
        print("  1-8      - Select category")
        print("  S        - Show stats")
        print("  E        - Export annotations")
        print("  R        - Reset selection")
        print("  Q        - Quit")
        
        cap = cv2.VideoCapture(camera_id)
        if not cap.isOpened():
            print(f"❌ Cannot open camera {camera_id}")
            return
            
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        window_name = "Jewelry Dataset Collector"
        cv2.namedWindow(window_name)
        cv2.setMouseCallback(window_name, self.mouse_callback)
        
        last_auto_capture = time.time()
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                    
                # Auto capture check
                if (self.auto_capture and 
                    time.time() - last_auto_capture > self.capture_interval):
                    # Simula detection (in produzione userai YOLO)
                    detections = []  # Placeholder
                    if self.auto_capture_frame(frame, detections):
                        last_auto_capture = time.time()
                
                # Disegna UI
                display_frame = self.draw_ui_overlay(frame)
                cv2.imshow(window_name, display_frame)
                
                # Handle input
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q'):
                    break
                elif key == ord(' '):  # Spacebar - capture
                    self.manual_capture_frame(frame)
                elif key == ord('a'):  # Toggle auto
                    self.auto_capture = not self.auto_capture
                    print(f"🤖 Auto-capture: {self.auto_capture}")
                elif key == ord('b'):  # Toggle annotation
                    self.annotation_mode = not self.annotation_mode
                    print(f"✏️  Annotation mode: {self.annotation_mode}")
                elif key == ord('r'):  # Reset selection
                    self.selected_bbox = None
                    print("🔄 Selection reset")
                elif key == ord('s'):  # Show stats
                    self.print_stats_summary()
                elif key == ord('e'):  # Export
                    self.export_yolo_annotations()
                elif key >= ord('1') and key <= ord('8'):  # Categories
                    new_category = key - ord('1')
                    if new_category in self.categories:
                        self.current_category = new_category
                        self.selected_bbox = None  # Reset selection
                        print(f"📂 Category: {self.categories[new_category]}")
                        
        except KeyboardInterrupt:
            print("\n⏹️  Collection stopped by user")
            
        finally:
            cap.release()
            cv2.destroyAllWindows()
            self.print_stats_summary()
            print(f"\n💾 Data saved to: {self.base_dir}")

def main():
    parser = argparse.ArgumentParser(description="Jewelry Dataset Collection System")
    parser.add_argument('--camera', type=int, default=0, help='Camera ID (default: 0)')
    parser.add_argument('--dataset-dir', type=str, default='~/jewelry_vision/dataset', 
                       help='Dataset directory (default: ~/jewelry_vision/dataset)')
    
    args = parser.parse_args()
    
    collector = JewelryDatasetCollector(args.dataset_dir)
    collector.run_collection_interface(args.camera)

if __name__ == "__main__":
    main()
