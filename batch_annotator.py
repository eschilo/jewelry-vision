#!/usr/bin/env python3
"""
Jewelry Batch Annotation Tool
Strumento per annotazione rapida batch di immagini gioielli
"""

import cv2
import os
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import argparse
from collections import defaultdict
import shutil

class JewelryBatchAnnotator:
    def __init__(self, dataset_dir: str = "~/jewelry_vision/dataset"):
        self.dataset_dir = Path(dataset_dir).expanduser()
        self.raw_images_dir = self.dataset_dir / "images/raw"
        self.annotations_dir = self.dataset_dir / "annotations/temp"
        
        # Categorie gioielli
        self.categories = {
            0: "anello", 1: "collana", 2: "orecchino", 3: "braccialetto",
            4: "pendente", 5: "spilla", 6: "gemma", 7: "orologio"
        }
        
        # UI State
        self.current_image_idx = 0
        self.images_list = []
        self.current_image = None
        self.current_filename = ""
        self.current_metadata = {}
        
        # Annotation state
        self.bboxes = []  # Lista di bbox correnti
        self.current_bbox = None
        self.drawing = False
        self.selected_category = 0
        
        # Stats
        self.session_stats = defaultdict(int)
        self.annotation_progress = {}
        
        self.load_images()
        
    def load_images(self):
        """Carica lista immagini da processare"""
        if not self.raw_images_dir.exists():
            print(f"❌ Directory immagini non trovata: {self.raw_images_dir}")
            return
            
        # Carica tutte le immagini
        extensions = ['*.jpg', '*.jpeg', '*.png']
        for ext in extensions:
            self.images_list.extend(self.raw_images_dir.glob(ext))
            
        self.images_list.sort()
        
        # Carica progresso esistente
        self.load_annotation_progress()
        
        print(f"📁 Trovate {len(self.images_list)} immagini")
        print(f"✅ Annotate: {len([x for x in self.annotation_progress.values() if x])}")
        print(f"⏳ Da annotare: {len([x for x in self.annotation_progress.values() if not x])}")
        
    def load_annotation_progress(self):
        """Carica progresso annotazioni esistente"""
        for img_path in self.images_list:
            json_path = self.annotations_dir / f"{img_path.stem}.json"
            
            if json_path.exists():
                try:
                    with open(json_path, 'r') as f:
                        metadata = json.load(f)
                    self.annotation_progress[img_path.name] = metadata.get('annotation_complete', False)
                except:
                    self.annotation_progress[img_path.name] = False
            else:
                self.annotation_progress[img_path.name] = False
                
    def load_current_image(self):
        """Carica immagine corrente"""
        if not self.images_list or self.current_image_idx >= len(self.images_list):
            return False
            
        img_path = self.images_list[self.current_image_idx]
        self.current_filename = img_path.name
        
        # Carica immagine
        self.current_image = cv2.imread(str(img_path))
        if self.current_image is None:
            print(f"❌ Errore caricamento: {img_path}")
            return False
            
        # Carica metadati esistenti
        json_path = self.annotations_dir / f"{img_path.stem}.json"
        
        if json_path.exists():
            with open(json_path, 'r') as f:
                self.current_metadata = json.load(f)
                
            # Carica bbox esistenti
            if 'bboxes' in self.current_metadata:
                self.bboxes = self.current_metadata['bboxes'].copy()
            elif 'bbox' in self.current_metadata and self.current_metadata['bbox']:
                # Converti bbox singolo in formato multi-bbox
                bbox = self.current_metadata['bbox']
                category_id = self.current_metadata.get('category_id', 0)
                self.bboxes = [{
                    'bbox': bbox,
                    'category_id': category_id,
                    'category': self.categories[category_id]
                }]
            else:
                self.bboxes = []
        else:
            # Crea metadati base
            self.current_metadata = {
                'filename': self.current_filename,
                'image_size': list(self.current_image.shape[:2]),
                'bboxes': [],
                'annotation_complete': False
            }
            self.bboxes = []
            
        return True
        
    def save_current_annotation(self):
        """Salva annotazione corrente"""
        if not self.current_image_idx < len(self.images_list):
            return
            
        img_path = self.images_list[self.current_image_idx]
        json_path = self.annotations_dir / f"{img_path.stem}.json"
        
        # Aggiorna metadati
        self.current_metadata.update({
            'filename': self.current_filename,
            'image_size': list(self.current_image.shape[:2]),
            'bboxes': self.bboxes,
            'annotation_complete': len(self.bboxes) > 0,
            'last_modified': str(Path.ctime(Path.now()))
        })
        
        # Salva JSON
        json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(json_path, 'w') as f:
            json.dump(self.current_metadata, f, indent=2)
            
        # Aggiorna progresso
        self.annotation_progress[self.current_filename] = len(self.bboxes) > 0
        
        # Aggiorna stats sessione
        self.session_stats['annotated'] += 1
        for bbox_data in self.bboxes:
            category = bbox_data['category']
            self.session_stats[f'category_{category}'] += 1
            
    def mouse_callback(self, event, x, y, flags, param):
        """Callback mouse per disegnare bbox"""
        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing = True
            self.current_bbox = {'start': (x, y), 'end': (x, y)}
            
        elif event == cv2.EVENT_MOUSEMOVE and self.drawing:
            self.current_bbox['end'] = (x, y)
            
        elif event == cv2.EVENT_LBUTTONUP and self.drawing:
            self.drawing = False
            
            if self.current_bbox:
                # Calcola bbox finale
                x1, y1 = self.current_bbox['start']
                x2, y2 = self.current_bbox['end']
                
                # Normalizza coordinate
                x1, x2 = min(x1, x2), max(x1, x2)
                y1, y2 = min(y1, y2), max(y1, y2)
                
                # Verifica dimensioni minime
                if abs(x2 - x1) > 10 and abs(y2 - y1) > 10:
                    bbox_data = {
                        'bbox': [x1, y1, x2, y2],
                        'category_id': self.selected_category,
                        'category': self.categories[self.selected_category]
                    }
                    self.bboxes.append(bbox_data)
                    print(f"➕ Aggiunto bbox: {self.categories[self.selected_category]}")
                    
                self.current_bbox = None
                
        elif event == cv2.EVENT_RBUTTONDOWN:
            # Click destro - rimuovi bbox vicino
            min_dist = float('inf')
            remove_idx = -1
            
            for i, bbox_data in enumerate(self.bboxes):
                x1, y1, x2, y2 = bbox_data['bbox']
                center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2
                dist = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
                
                if dist < min_dist and dist < 50:  # Raggio di 50 pixel
                    min_dist = dist
                    remove_idx = i
                    
            if remove_idx >= 0:
                removed = self.bboxes.pop(remove_idx)
                print(f"➖ Rimosso bbox: {removed['category']}")
                
    def draw_ui_overlay(self, image: np.ndarray) -> np.ndarray:
        """Disegna overlay UI"""
        overlay = image.copy()
        h, w = image.shape[:2]
        
        # Disegna bbox esistenti
        for i, bbox_data in enumerate(self.bboxes):
            x1, y1, x2, y2 = bbox_data['bbox']
            category = bbox_data['category']
            category_id = bbox_data['category_id']
            
            # Colore per categoria
            color = self.get_category_color(category_id)
            
            # Disegna rettangolo
            cv2.rectangle(overlay, (x1, y1), (x2, y2), color, 2)
            
            # Label
            label = f"{i+1}: {category}"
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
            cv2.rectangle(overlay, (x1, y1 - label_size[1] - 10), 
                         (x1 + label_size[0] + 5, y1), color, -1)
            cv2.putText(overlay, label, (x1 + 2, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Disegna bbox in creazione
        if self.drawing and self.current_bbox:
            x1, y1 = self.current_bbox['start']
            x2, y2 = self.current_bbox['end']
            color = self.get_category_color(self.selected_category)
            cv2.rectangle(overlay, (x1, y1), (x2, y2), color, 2)
            
        # Pannello informazioni
        self.draw_info_panel(overlay)
        
        return overlay
        
    def draw_info_panel(self, image: np.ndarray):
        """Disegna pannello informazioni"""
        h, w = image.shape[:2]
        
        # Background pannello
        panel_h = 150
        panel = np.zeros((panel_h, w, 3), dtype=np.uint8)
        panel[:] = (40, 40, 40)
        
        # Info immagine corrente
        progress = f"{self.current_image_idx + 1}/{len(self.images_list)}"
        cv2.putText(panel, f"Immagine: {self.current_filename} ({progress})", 
                   (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Categoria selezionata
        current_cat = self.categories[self.selected_category]
        color = self.get_category_color(self.selected_category)
        cv2.putText(panel, f"Categoria: {current_cat}", (10, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        # Numero bbox correnti
        cv2.putText(panel, f"Bbox: {len(self.bboxes)}", (10, 75), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        # Status annotazione
        is_annotated = self.annotation_progress.get(self.current_filename, False)
        status = "✅ ANNOTATA" if is_annotated else "⏳ DA ANNOTARE"
        status_color = (0, 255, 0) if is_annotated else (0, 255, 255)
        cv2.putText(panel, status, (10, 100), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, status_color, 2)
        
        # Comandi
        commands = "SPACE=Next | BACKSPACE=Prev | S=Save | 1-8=Category | C=Clear | Q=Quit"
        cv2.putText(panel, commands, (10, 125), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
        
        # Statistiche laterali
        stats_x = w - 200
        cv2.putText(panel, "STATS SESSIONE:", (stats_x, 25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
        
        annotated = len([x for x in self.annotation_progress.values() if x])
        total = len(self.annotation_progress)
        cv2.putText(panel, f"Annotate: {annotated}/{total}", (stats_x, 45), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        if total > 0:
            progress_pct = (annotated / total) * 100
            cv2.putText(panel, f"Progresso: {progress_pct:.1f}%", (stats_x, 65), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Sovrapponi pannello
        image[:panel_h] = panel
        
    def get_category_color(self, category_id: int) -> Tuple[int, int, int]:
        """Restituisce colore per categoria"""
        colors = [
            (0, 255, 255),    # anello - giallo
            (255, 0, 255),    # collana - magenta
            (0, 255, 0),      # orecchino - verde
            (255, 0, 0),      # braccialetto - rosso
            (0, 128, 255),    # pendente - arancione
            (255, 255, 0),    # spilla - ciano
            (128, 0, 255),    # gemma - viola
            (255, 128, 0),    # orologio - blu chiaro
        ]
        return colors[category_id % len(colors)]
        
    def next_image(self):
        """Passa alla prossima immagine"""
        if self.current_image_idx < len(self.images_list) - 1:
            self.save_current_annotation()
            self.current_image_idx += 1
            self.load_current_image()
            return True
        return False
        
    def prev_image(self):
        """Torna all'immagine precedente"""
        if self.current_image_idx > 0:
            self.save_current_annotation()
            self.current_image_idx -= 1
            self.load_current_image()
            return True
        return False
        
    def clear_annotations(self):
        """Cancella tutte le annotazioni correnti"""
        self.bboxes = []
        print("🗑️  Annotazioni cancellate")
        
    def jump_to_next_unannotated(self):
        """Salta alla prossima immagine non annotata"""
        start_idx = self.current_image_idx
        
        for i in range(start_idx + 1, len(self.images_list)):
            img_name = self.images_list[i].name
            if not self.annotation_progress.get(img_name, False):
                self.save_current_annotation()
                self.current_image_idx = i
                self.load_current_image()
                print(f"⏭️  Saltato a immagine non annotata: {img_name}")
                return True
                
        # Se non trovate, ricomincia dall'inizio
        for i in range(0, start_idx):
            img_name = self.images_list[i].name
            if not self.annotation_progress.get(img_name, False):
                self.save_current_annotation()
                self.current_image_idx = i
                self.load_current_image()
                print(f"🔄 Ricominciato dall'inizio: {img_name}")
                return True
                
        print("✅ Tutte le immagini sono state annotate!")
        return False
        
    def export_annotations(self):
        """Esporta tutte le annotazioni in formato YOLO"""
        print("🔄 Esportazione annotazioni in formato YOLO...")
        
        yolo_dir = self.dataset_dir / "annotations/yolo"
        yolo_dir.mkdir(parents=True, exist_ok=True)
        
        exported_count = 0
        
        for img_path in self.images_list:
            json_path = self.annotations_dir / f"{img_path.stem}.json"
            
            if not json_path.exists():
                continue
                
            with open(json_path, 'r') as f:
                metadata = json.load(f)
                
            if not metadata.get('bboxes'):
                continue
                
            # Crea file annotazione YOLO
            yolo_file = yolo_dir / f"{img_path.stem}.txt"
            
            with open(yolo_file, 'w') as f:
                img_h, img_w = metadata['image_size']
                
                for bbox_data in metadata['bboxes']:
                    x1, y1, x2, y2 = bbox_data['bbox']
                    category_id = bbox_data['category_id']
                    
                    # Converti in formato YOLO (normalizzato)
                    center_x = (x1 + x2) / 2.0 / img_w
                    center_y = (y1 + y2) / 2.0 / img_h
                    width = (x2 - x1) / img_w
                    height = (y2 - y1) / img_h
                    
                    f.write(f"{category_id} {center_x:.6f} {center_y:.6f} {width:.6f} {height:.6f}\n")
                    
            exported_count += 1
            
        # Genera file classes.txt
        classes_file = yolo_dir / "classes.txt"
        with open(classes_file, 'w') as f:
            for i in range(len(self.categories)):
                f.write(f"{self.categories[i]}\n")
                
        print(f"✅ Esportate {exported_count} annotazioni YOLO")
        print(f"📁 Directory: {yolo_dir}")
        
    def print_statistics(self):
        """Stampa statistiche dettagliate"""
        print("\n" + "="*60)
        print("📊 JEWELRY ANNOTATION STATISTICS")
        print("="*60)
        
        total_images = len(self.images_list)
        annotated = len([x for x in self.annotation_progress.values() if x])
        
        print(f"Immagini totali: {total_images}")
        print(f"Immagini annotate: {annotated}")
        print(f"Immagini rimanenti: {total_images - annotated}")
        
        if total_images > 0:
            progress = (annotated / total_images) * 100
            print(f"Progresso: {progress:.1f}%")
            
        # Conta bbox per categoria
        category_counts = defaultdict(int)
        total_bboxes = 0
        
        for img_path in self.images_list:
            json_path = self.annotations_dir / f"{img_path.stem}.json"
            if json_path.exists():
                with open(json_path, 'r') as f:
                    metadata = json.load(f)
                    
                for bbox_data in metadata.get('bboxes', []):
                    category = bbox_data['category']
                    category_counts[category] += 1
                    total_bboxes += 1
                    
        print(f"\nBounding boxes totali: {total_bboxes}")
        print("\nDistribuzione per categoria:")
        for cat_name in self.categories.values():
            count = category_counts[cat_name]
            pct = (count / total_bboxes * 100) if total_bboxes > 0 else 0
            print(f"  {cat_name:12}: {count:4d} ({pct:5.1f}%)")
            
        print("="*60)
        
    def run_annotation_interface(self):
        """Avvia interfaccia di annotazione"""
        print("🎨 Starting Jewelry Batch Annotation Interface")
        print("📖 Controls:")
        print("  Left Click & Drag  - Draw bounding box")
        print("  Right Click        - Remove nearest bbox")
        print("  SPACE              - Next image")
        print("  BACKSPACE          - Previous image")
        print("  N                  - Jump to next unannotated")
        print("  S                  - Save current annotations")
        print("  C                  - Clear all current annotations")
        print("  1-8                - Select category")
        print("  E                  - Export all annotations")
        print("  T                  - Show statistics")
        print("  Q                  - Quit")
        
        if not self.images_list:
            print("❌ Nessuna immagine trovata!")
            return
            
        if not self.load_current_image():
            print("❌ Errore caricamento prima immagine!")
            return
            
        window_name = "Jewelry Batch Annotator"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, 1200, 800)
        cv2.setMouseCallback(window_name, self.mouse_callback)
        
        try:
            while True:
                if self.current_image is None:
                    break
                    
                # Disegna interfaccia
                display_image = self.draw_ui_overlay(self.current_image.copy())
                cv2.imshow(window_name, display_image)
                
                # Handle input
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q'):
                    self.save_current_annotation()
                    break
                elif key == ord(' '):  # Next image
                    if not self.next_image():
                        print("📍 Ultima immagine raggiunta")
                elif key == 8:  # Backspace - Previous image
                    if not self.prev_image():
                        print("📍 Prima immagine raggiunta")
                elif key == ord('n'):  # Next unannotated
                    self.jump_to_next_unannotated()
                elif key == ord('s'):  # Save
                    self.save_current_annotation()
                    print("💾 Annotazioni salvate")
                elif key == ord('c'):  # Clear
                    self.clear_annotations()
                elif key == ord('e'):  # Export
                    self.save_current_annotation()
                    self.export_annotations()
                elif key == ord('t'):  # Statistics
                    self.print_statistics()
                elif key >= ord('1') and key <= ord('8'):  # Category selection
                    new_category = key - ord('1')
                    if new_category in self.categories:
                        self.selected_category = new_category
                        print(f"📂 Categoria selezionata: {self.categories[new_category]}")
                        
        except KeyboardInterrupt:
            print("\n⏹️  Annotation stopped by user")
            
        finally:
            self.save_current_annotation()
            cv2.destroyAllWindows()
            self.print_statistics()
            print(f"\n💾 Annotazioni salvate in: {self.annotations_dir}")

def main():
    parser = argparse.ArgumentParser(description="Jewelry Batch Annotation Tool")
    parser.add_argument('--dataset-dir', type=str, default='~/jewelry_vision/dataset',
                       help='Dataset directory (default: ~/jewelry_vision/dataset)')
    parser.add_argument('--start-idx', type=int, default=0,
                       help='Start from image index (default: 0)')
    
    args = parser.parse_args()
    
    annotator = JewelryBatchAnnotator(args.dataset_dir)
    
    if args.start_idx > 0 and args.start_idx < len(annotator.images_list):
        annotator.current_image_idx = args.start_idx
        annotator.load_current_image()
        
    annotator.run_annotation_interface()

if __name__ == "__main__":
    main()
