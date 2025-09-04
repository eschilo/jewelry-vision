#!/usr/bin/env python3
"""
Jewelry Dataset Manager
Sistema di gestione, validazione e preparazione dataset per training
"""

import cv2
import os
import json
import shutil
import random
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict, Counter
import numpy as np
import argparse
from datetime import datetime

class JewelryDatasetManager:
    def __init__(self, dataset_dir: str = "~/jewelry_vision/dataset"):
        self.dataset_dir = Path(dataset_dir).expanduser()
        
        # Directory paths
        self.raw_images_dir = self.dataset_dir / "images/raw"
        self.processed_images_dir = self.dataset_dir / "images/processed"
        self.annotations_temp_dir = self.dataset_dir / "annotations/temp"
        self.annotations_yolo_dir = self.dataset_dir / "annotations/yolo"
        self.exports_dir = self.dataset_dir / "exports"
        
        # Categorie gioielli
        self.categories = {
            0: "anello", 1: "collana", 2: "orecchino", 3: "braccialetto",
            4: "pendente", 5: "spilla", 6: "gemma", 7: "orologio"
        }
        
        # Statistiche dataset
        self.dataset_stats = {}
        self.validation_errors = []
        
    def scan_dataset(self) -> Dict:
        """Scansiona e analizza il dataset completo"""
        print("🔍 Scanning dataset...")
        
        stats = {
            'total_images': 0,
            'annotated_images': 0,
            'total_bboxes': 0,
            'category_distribution': defaultdict(int),
            'image_sizes': [],
            'annotation_quality': {'valid': 0, 'invalid': 0},
            'files': {
                'raw_images': [],
                'annotations': [],
                'orphaned_images': [],
                'orphaned_annotations': []
            }
        }
        
        # Scansiona immagini raw
        if self.raw_images_dir.exists():
            for ext in ['*.jpg', '*.jpeg', '*.png']:
                stats['files']['raw_images'].extend(self.raw_images_dir.glob(ext))
        
        stats['total_images'] = len(stats['files']['raw_images'])
        
        # Scansiona annotazioni
        if self.annotations_temp_dir.exists():
            stats['files']['annotations'] = list(self.annotations_temp_dir.glob('*.json'))
        
        # Analizza annotazioni
        for ann_file in stats['files']['annotations']:
            try:
                with open(ann_file, 'r') as f:
                    metadata = json.load(f)
                
                # Verifica se ha annotazioni valide
                bboxes = metadata.get('bboxes', [])
                if not bboxes and metadata.get('bbox'):
                    # Formato singolo bbox
                    bboxes = [{'bbox': metadata['bbox'], 
                             'category_id': metadata.get('category_id', 0)}]
                
                if bboxes:
                    stats['annotated_images'] += 1
                    stats['total_bboxes'] += len(bboxes)
                    
                    # Conta categorie
                    for bbox_data in bboxes:
                        if isinstance(bbox_data, dict):
                            cat_id = bbox_data.get('category_id', 0)
                            category = self.categories.get(cat_id, 'unknown')
                            stats['category_distribution'][category] += 1
                
                # Dimensioni immagini
                img_size = metadata.get('image_size')
                if img_size:
                    stats['image_sizes'].append(tuple(img_size))
                
                stats['annotation_quality']['valid'] += 1
                
            except Exception as e:
                stats['annotation_quality']['invalid'] += 1
                self.validation_errors.append(f"Invalid annotation {ann_file}: {e}")
        
        # Trova file orfani
        annotated_stems = {f.stem for f in stats['files']['annotations']}
        image_stems = {f.stem for f in stats['files']['raw_images']}
        
        stats['files']['orphaned_images'] = [
            img for img in stats['files']['raw_images'] 
            if img.stem not in annotated_stems
        ]
        
        stats['files']['orphaned_annotations'] = [
            ann for ann in stats['files']['annotations'] 
            if ann.stem not in image_stems
        ]
        
        self.dataset_stats = stats
        return stats
    
    def validate_dataset(self) -> List[str]:
        """Valida integrità del dataset"""
        print("✅ Validating dataset...")
        
        errors = []
        
        # Verifica esistenza directory
        required_dirs = [
            self.raw_images_dir,
            self.annotations_temp_dir
        ]
        
        for dir_path in required_dirs:
            if not dir_path.exists():
                errors.append(f"Missing required directory: {dir_path}")
        
        # Verifica corrispondenza immagini-annotazioni
        if self.dataset_stats:
            orphaned_images = len(self.dataset_stats['files']['orphaned_images'])
            orphaned_annotations = len(self.dataset_stats['files']['orphaned_annotations'])
            
            if orphaned_images > 0:
                errors.append(f"{orphaned_images} images without annotations")
            
            if orphaned_annotations > 0:
                errors.append(f"{orphaned_annotations} annotations without images")
        
        # Verifica validità annotazioni
        for ann_file in self.annotations_temp_dir.glob('*.json'):
            try:
                with open(ann_file, 'r') as f:
                    metadata = json.load(f)
                
                # Verifica campi richiesti
                required_fields = ['filename', 'image_size']
                for field in required_fields:
                    if field not in metadata:
                        errors.append(f"Missing field '{field}' in {ann_file}")
                
                # Verifica bbox
                bboxes = metadata.get('bboxes', [])
                if metadata.get('bbox') and not bboxes:
                    bboxes = [{'bbox': metadata['bbox']}]
                
                for i, bbox_data in enumerate(bboxes):
                    if isinstance(bbox_data, dict) and 'bbox' in bbox_data:
                        bbox = bbox_data['bbox']
                        if len(bbox) != 4:
                            errors.append(f"Invalid bbox format in {ann_file} (bbox {i})")
                        
                        # Verifica coordinate
                        x1, y1, x2, y2 = bbox
                        if x1 >= x2 or y1 >= y2:
                            errors.append(f"Invalid bbox coordinates in {ann_file} (bbox {i})")
                
            except json.JSONDecodeError:
                errors.append(f"Invalid JSON in {ann_file}")
            except Exception as e:
                errors.append(f"Error validating {ann_file}: {e}")
        
        self.validation_errors.extend(errors)
        return errors
    
    def clean_dataset(self, remove_orphans: bool = False):
        """Pulisce il dataset rimuovendo file corrotti o duplicati"""
        print("🧹 Cleaning dataset...")
        
        cleaned_count = 0
        
        # Rimuovi annotazioni corrotte
        for ann_file in self.annotations_temp_dir.glob('*.json'):
            try:
                with open(ann_file, 'r') as f:
                    json.load(f)
            except:
                print(f"🗑️  Removing corrupted annotation: {ann_file}")
                ann_file.unlink()
                cleaned_count += 1
        
        # Rimuovi file orfani se richiesto
        if remove_orphans:
            if self.dataset_stats:
                for orphan_img in self.dataset_stats['files']['orphaned_images']:
                    print(f"🗑️  Removing orphaned image: {orphan_img}")
                    orphan_img.unlink()
                    cleaned_count += 1
                
                for orphan_ann in self.dataset_stats['files']['orphaned_annotations']:
                    print(f"🗑️  Removing orphaned annotation: {orphan_ann}")
                    orphan_ann.unlink()
                    cleaned_count += 1
        
        print(f"✅ Cleaned {cleaned_count} files")
        
        # Re-scan dopo pulizia
        self.scan_dataset()
    
    def create_train_val_split(self, train_ratio: float = 0.8, 
                              stratified: bool = True) -> Dict:
        """Crea split train/validation"""
        print(f"📊 Creating train/val split ({train_ratio:.1%} train)...")
        
        if not self.dataset_stats:
            self.scan_dataset()
        
        annotated_files = []
        
        # Raccogli file annotati con le loro categorie
        for ann_file in self.annotations_temp_dir.glob('*.json'):
            try:
                with open(ann_file, 'r') as f:
                    metadata = json.load(f)
                
                bboxes = metadata.get('bboxes', [])
                if not bboxes and metadata.get('bbox'):
                    bboxes = [{'bbox': metadata['bbox'], 
                             'category_id': metadata.get('category_id', 0)}]
                
                if bboxes:
                    # Prendi la categoria più frequente per questo file
                    categories = [bbox.get('category_id', 0) for bbox in bboxes]
                    main_category = Counter(categories).most_common(1)[0][0]
                    
                    annotated_files.append({
                        'stem': ann_file.stem,
                        'category': main_category
                    })
                    
            except:
                continue
        
        if not annotated_files:
            print("❌ No annotated files found!")
            return {}
        
        # Crea split
        if stratified:
            # Split stratificato per categoria
            train_files = []
            val_files = []
            
            # Raggruppa per categoria
            category_files = defaultdict(list)
            for file_info in annotated_files:
                category_files[file_info['category']].append(file_info['stem'])
            
            # Split per ogni categoria
            for category, files in category_files.items():
                random.shuffle(files)
                split_idx = int(len(files) * train_ratio)
                train_files.extend(files[:split_idx])
                val_files.extend(files[split_idx:])
                
        else:
            # Split casuale
            random.shuffle(annotated_files)
            split_idx = int(len(annotated_files) * train_ratio)
            train_files = [f['stem'] for f in annotated_files[:split_idx]]
            val_files = [f['stem'] for f in annotated_files[split_idx:]]
        
        split_info = {
            'train': train_files,
            'val': val_files,
            'train_count': len(train_files),
            'val_count': len(val_files),
            'total_count': len(annotated_files),
            'train_ratio': len(train_files) / len(annotated_files)
        }
        
        # Salva informazioni split
        split_file = self.dataset_dir / "train_val_split.json"
        with open(split_file, 'w') as f:
            json.dump(split_info, f, indent=2)
        
        print(f"✅ Split created: {len(train_files)} train, {len(val_files)} val")
        print(f"📁 Split info saved to: {split_file}")
        
        return split_info
    
    def export_yolo_dataset(self, split_info: Optional[Dict] = None) -> str:
        """Esporta dataset in formato YOLO pronto per training"""
        print("📦 Exporting YOLO dataset...")
        
        # Crea directory export
        export_name = f"yolo_dataset_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        export_path = self.exports_dir / export_name
        
        # Struttura directory YOLO
        dirs = ['images/train', 'images/val', 'labels/train', 'labels/val']
        for dir_name in dirs:
            (export_path / dir_name).mkdir(parents=True, exist_ok=True)
        
        # Carica split info
        if not split_info:
            split_file = self.dataset_dir / "train_val_split.json"
            if split_file.exists():
                with open(split_file, 'r') as f:
                    split_info = json.load(f)
            else:
                print("⚠️  No split info found, creating new split...")
                split_info = self.create_train_val_split()
        
        # Copia file per train e val
        for split_type in ['train', 'val']:
            file_stems = split_info.get(split_type, [])
            
            for stem in file_stems:
                # Copia immagine
                img_file = None
                for ext in ['.jpg', '.jpeg', '.png']:
                    potential_img = self.raw_images_dir / f"{stem}{ext}"
                    if potential_img.exists():
                        img_file = potential_img
                        break
                
                if img_file:
                    dest_img = export_path / f"images/{split_type}" / img_file.name
                    shutil.copy2(img_file, dest_img)
                
                # Converti e copia annotation
                ann_file = self.annotations_temp_dir / f"{stem}.json"
                if ann_file.exists():
                    self.convert_annotation_to_yolo(ann_file, 
                                                  export_path / f"labels/{split_type}" / f"{stem}.txt")
        
        # Crea file dataset.yaml
        dataset_yaml = f"""# Jewelry Dataset Configuration
path: {export_path.absolute()}
train: images/train
val: images/val

# Classes
nc: {len(self.categories)}
names: {list(self.categories.values())}

# Dataset info
created: {datetime.now().isoformat()}
total_images: {split_info.get('total_count', 0)}
train_images: {split_info.get('train_count', 0)}
val_images: {split_info.get('val_count', 0)}
"""
        
        with open(export_path / "dataset.yaml", 'w') as f:
            f.write(dataset_yaml)
        
        # Crea file classes.txt
        with open(export_path / "classes.txt", 'w') as f:
            for i in range(len(self.categories)):
                f.write(f"{self.categories[i]}\n")
        
        print(f"✅ YOLO dataset exported to: {export_path}")
        return str(export_path)
    
    def convert_annotation_to_yolo(self, json_path: Path, yolo_path: Path):
        """Converti annotazione JSON in formato YOLO"""
        try:
            with open(json_path, 'r') as f:
                metadata = json.load(f)
            
            img_h, img_w = metadata['image_size']
            bboxes = metadata.get('bboxes', [])
            
            # Compatibilità con formato singolo bbox
            if not bboxes and metadata.get('bbox'):
                bboxes = [{'bbox': metadata['bbox'], 
                         'category_id': metadata.get('category_id', 0)}]
            
            with open(yolo_path, 'w') as f:
                for bbox_data in bboxes:
                    if not isinstance(bbox_data, dict) or 'bbox' not in bbox_data:
                        continue
                    
                    x1, y1, x2, y2 = bbox_data['bbox']
                    category_id = bbox_data.get('category_id', 0)
                    
                    # Converti in formato YOLO normalizzato
                    center_x = (x1 + x2) / 2.0 / img_w
                    center_y = (y1 + y2) / 2.0 / img_h
                    width = (x2 - x1) / img_w
                    height = (y2 - y1) / img_h
                    
                    f.write(f"{category_id} {center_x:.6f} {center_y:.6f} {width:.6f} {height:.6f}\n")
                    
        except Exception as e:
            print(f"⚠️  Error converting {json_path}: {e}")
    
    def generate_dataset_report(self) -> str:
        """Genera report dettagliato del dataset"""
        if not self.dataset_stats:
            self.scan_dataset()
        
        stats = self.dataset_stats
        
        report = f"""
╔══════════════════════════════════════════════════════════════╗
║                    JEWELRY DATASET REPORT                   ║
╚══════════════════════════════════════════════════════════════╝

📊 DATASET OVERVIEW
├── Total Images: {stats['total_images']}
├── Annotated Images: {stats['annotated_images']} ({stats['annotated_images']/stats['total_images']*100:.1f}%)
├── Total Bounding Boxes: {stats['total_bboxes']}
├── Average Boxes per Image: {stats['total_bboxes']/max(stats['annotated_images'], 1):.1f}
└── Annotation Quality: {stats['annotation_quality']['valid']} valid, {stats['annotation_quality']['invalid']} invalid

📂 FILE DISTRIBUTION
├── Raw Images: {len(stats['files']['raw_images'])}
├── Annotations: {len(stats['files']['annotations'])}
├── Orphaned Images: {len(stats['files']['orphaned_images'])}
└── Orphaned Annotations: {len(stats['files']['orphaned_annotations'])}

🎯 CATEGORY DISTRIBUTION
"""
        
        # Aggiungi distribuzione categorie
        total_boxes = sum(stats['category_distribution'].values())
        for category, count in stats['category_distribution'].items():
            percentage = (count / total_boxes * 100) if total_boxes > 0 else 0
            bar_length = int(percentage / 2)  # Max 50 caratteri
            bar = "█" * bar_length + "░" * (50 - bar_length)
            report += f"├── {category:12}: {count:4d} ({percentage:5.1f}%) {bar}\n"
        
        # Aggiungi statistiche immagini
        if stats['image_sizes']:
            sizes = stats['image_sizes']
            heights = [s[0] for s in sizes]
            widths = [s[1] for s in sizes]
            
            report += f"""
📐 IMAGE DIMENSIONS
├── Images analyzed: {len(sizes)}
├── Height - Min: {min(heights)}, Max: {max(heights)}, Avg: {sum(heights)/len(heights):.0f}
└── Width  - Min: {min(widths)}, Max: {max(widths)}, Avg: {sum(widths)/len(widths):.0f}
"""
        
        # Aggiungi errori di validazione
        if self.validation_errors:
            report += f"""
⚠️  VALIDATION ERRORS ({len(self.validation_errors)})
"""
            for i, error in enumerate(self.validation_errors[:10]):  # Max 10 errori
                report += f"├── {error}\n"
            
            if len(self.validation_errors) > 10:
                report += f"└── ... and {len(self.validation_errors) - 10} more errors\n"
        
        # Raccomandazioni
        report += """
💡 RECOMMENDATIONS
"""
        
        if stats['annotated_images'] < stats['total_images'] * 0.8:
            report += "├── ⚠️  Consider annotating more images for better training\n"
        
        if len(stats['files']['orphaned_images']) > 0:
            report += "├── 🧹 Clean orphaned images to reduce storage\n"
        
        # Controlla bilanciamento classi
        if stats['category_distribution']:
            values = list(stats['category_distribution'].values())
            if max(values) > min(values) * 5:  # Sbilanciamento > 5:1
                report += "├── ⚖️  Dataset is unbalanced, consider collecting more data for underrepresented categories\n"
        
        if stats['total_bboxes'] < 1000:
            report += "├── 📈 Consider collecting more data (recommended: >1000 boxes per class)\n"
        
        report += f"""
╔══════════════════════════════════════════════════════════════╗
║ Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                           ║
╚══════════════════════════════════════════════════════════════╝
"""
        
        return report
    
    def backup_dataset(self) -> str:
        """Crea backup completo del dataset"""
        print("💾 Creating dataset backup...")
        
        backup_name = f"jewelry_dataset_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        backup_path = self.dataset_dir / "backups" / backup_name
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # Directory da includere nel backup
        dirs_to_backup = [
            "images/raw",
            "annotations/temp", 
            "annotations/yolo"
        ]
        
        backed_up_files = 0
        
        for dir_name in dirs_to_backup:
            source_dir = self.dataset_dir / dir_name
            dest_dir = backup_path / dir_name
            
            if source_dir.exists():
                dest_dir.mkdir(parents=True, exist_ok=True)
                
                # Copia tutti i file
                for file_path in source_dir.rglob('*'):
                    if file_path.is_file():
                        rel_path = file_path.relative_to(source_dir)
                        dest_file = dest_dir / rel_path
                        dest_file.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(file_path, dest_file)
                        backed_up_files += 1
        
        # Includi file di configurazione
        config_files = [
            "collection_stats.json",
            "train_val_split.json"
        ]
        
        for config_file in config_files:
            source_file = self.dataset_dir / config_file
            if source_file.exists():
                shutil.copy2(source_file, backup_path / config_file)
                backed_up_files += 1
        
        # Crea manifest del backup
        manifest = {
            'backup_created': datetime.now().isoformat(),
            'original_path': str(self.dataset_dir),
            'files_backed_up': backed_up_files,
            'dataset_stats': self.dataset_stats
        }
        
        with open(backup_path / "backup_manifest.json", 'w') as f:
            json.dump(manifest, f, indent=2)
        
        print(f"✅ Backup created: {backup_path}")
        print(f"📁 Files backed up: {backed_up_files}")
        
        return str(backup_path)

def main():
    parser = argparse.ArgumentParser(description="Jewelry Dataset Manager")
    parser.add_argument('--dataset-dir', type=str, default='~/jewelry_vision/dataset',
                       help='Dataset directory (default: ~/jewelry_vision/dataset)')
    parser.add_argument('--action', type=str, choices=[
        'scan', 'validate', 'clean', 'split', 'export', 'report', 'backup', 'all'
    ], default='report', help='Action to perform (default: report)')
    parser.add_argument('--train-ratio', type=float, default=0.8,
                       help='Training set ratio for split (default: 0.8)')
    parser.add_argument('--remove-orphans', action='store_true',
                       help='Remove orphaned files during cleaning')
    parser.add_argument('--stratified', action='store_true', default=True,
                       help='Use stratified split by category')
    
    args = parser.parse_args()
    
    manager = JewelryDatasetManager(args.dataset_dir)
    
    if args.action == 'scan' or args.action == 'all':
        manager.scan_dataset()
        print("✅ Dataset scan completed")
    
    if args.action == 'validate' or args.action == 'all':
        errors = manager.validate_dataset()
        if errors:
            print(f"❌ Found {len(errors)} validation errors:")
            for error in errors:
                print(f"  - {error}")
        else:
            print("✅ Dataset validation passed")
    
    if args.action == 'clean' or args.action == 'all':
        manager.clean_dataset(args.remove_orphans)
    
    if args.action == 'split' or args.action == 'all':
        split_info = manager.create_train_val_split(args.train_ratio, args.stratified)
        print(f"✅ Train/val split created")
    
    if args.action == 'export' or args.action == 'all':
        export_path = manager.export_yolo_dataset()
        print(f"✅ YOLO dataset exported to: {export_path}")
    
    if args.action == 'backup' or args.action == 'all':
        backup_path = manager.backup_dataset()
        print(f"✅ Backup created at: {backup_path}")
    
    if args.action == 'report' or args.action == 'all':
        if not manager.dataset_stats:
            manager.scan_dataset()
            manager.validate_dataset()
        
        report = manager.generate_dataset_report()
        print(report)
        
        # Salva report su file
        report_file = manager.dataset_dir / f"dataset_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        print(f"\n📄 Report saved to: {report_file}")

if __name__ == "__main__":
    main()
