# 💎 Jewelry Vision - Sistema di Videosorveglianza Intelligente

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com)
[![YOLO](https://img.shields.io/badge/YOLO-v11-red.svg)](https://ultralytics.com)
[![Jetson](https://img.shields.io/badge/NVIDIA-Jetson%20Orin%20Nano-76B900.svg)](https://developer.nvidia.com/jetson)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> Sistema di videosorveglianza intelligente progettato specificamente per gioiellerie, basato su NVIDIA Jetson Orin Nano con detection AI in tempo reale.

## 🌟 **Caratteristiche Principali**

### 🎯 **Detection & Monitoring**
- **YOLO11** per detection oggetti in tempo reale
- **Smart Camera Switch** tra streaming e monitoring
- **Bounding box** colorati per diverse classi di oggetti
- **Salvataggio automatico** dei frame con detection
- **Log system** completo con timestamp

### 📹 **Video Streaming**
- **Streaming HD** ottimizzato per Jetson Orin Nano
- **Controlli intuitivi** (play/pause/capture/fullscreen)
- **Interfaccia responsive** per desktop e mobile
- **MJPEG streaming** ottimizzato per L4T

### 🎨 **Interfaccia Utente**
- **Menu diamante** interattivo e moderno
- **Dashboard modulare** con 5 sezioni operative
- **Design responsive** con tema scuro professionale
- **Controlli touch-friendly** per tablet

### ⚡ **Ottimizzazioni Jetson**
- **Hardware acceleration** per CUDA/GPU
- **Memory management** ottimizzato
- **Frame rate adattivo** per performance
- **Multi-threading** per operations parallele

## 🏗️ **Architettura Sistema**

```
jewelry_vision/
├── 🐍 jewelry_vision_web.py     # Server Flask principale
├── 📁 templates/                # Interfacce web
│   ├── 🏠 main_menu.html       # Menu diamante principale
│   ├── 📹 surveillance.html    # Streaming video
│   ├── 🎯 monitoring.html      # Detection & monitoring
│   ├── 📊 dataset.html         # Gestione dataset (TODO)
│   ├── 🏋️ training.html        # Training modelli (TODO)
│   └── ⚙️ settings.html        # Configurazioni (TODO)
├── 🤖 models/                  # Modelli YOLO
├── 📸 captures/                # Frame salvati
├── 📝 logs/                    # Log sistema
├── 🎬 recordings/              # Registrazioni video
└── ⚙️ config/                  # File configurazione
```

## 🚀 **Quick Start**

### Prerequisiti
- **NVIDIA Jetson Orin Nano 8GB** con JetPack 5.0+
- **Python 3.8+** 
- **Camera USB/CSI** compatibile V4L2
- **Connessione Internet** per download modelli

### Installazione Rapida

```bash
# 1. Clona il repository
git clone https://github.com/tuousername/jewelry-vision.git
cd jewelry-vision

# 2. Installa dipendenze
pip install -r requirements.txt

# 3. Avvia il sistema
python jewelry_vision_web.py

# 4. Apri nel browser
# http://localhost:5000
```

## 📦 **Installazione Completa**

### 1. Setup Ambiente Jetson

```bash
# Aggiorna sistema
sudo apt update && sudo apt upgrade -y

# Installa dipendenze sistema
sudo apt install python3-pip python3-venv git curl -y

# Crea ambiente virtuale
python3 -m venv jewelry_vision_env
source jewelry_vision_env/bin/activate
```

### 2. Installa Dipendenze Python

```bash
# Installa PyTorch per Jetson
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Installa Ultralytics YOLO
pip install ultralytics

# Installa Flask e dipendenze web
pip install flask opencv-python requests

# Verifica installazione
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

### 3. Configurazione Camera

```bash
# Verifica camera disponibili
ls /dev/video*

# Test camera (sostituisci X con il numero corretto)
v4l2-ctl --device=/dev/videoX --all
```

### 4. Avvio Sistema

```bash
# Avvia server
python jewelry_vision_web.py

# Output atteso:
# 🎯 JewelryVisionWeb FINALE inizializzato
# 📡 Server in ascolto su: http://localhost:5000
# 🎯 Detection monitoring: http://localhost:5000/monitoring
```

## 🎮 **Utilizzo**

### Menu Principale
1. Accedi a `http://localhost:5000`
2. Clicca sul **diamante centrale** per navigare
3. Scegli tra le **5 sezioni operative**

### Video Streaming
1. Vai su **"Surveillance"**
2. Clicca **"Avvia Streaming"** 
3. Usa i controlli per gestire il video
4. **Cattura frame** quando necessario

### Detection & Monitoring  
1. Vai su **"Detection & Monitoring"**
2. Clicca **"Avvia Monitoring"**
3. Osserva le **detection in tempo reale**
4. Controlla **log e statistiche** nel pannello laterale

### Keyboard Shortcuts
- `Ctrl + S` - Avvia monitoring
- `Ctrl + Q` - Ferma monitoring  
- `Ctrl + C` - Cattura frame
- `Ctrl + F` - Modalità fullscreen

## 🔧 **Configurazione**

### Impostazioni Camera

Modifica `jewelry_vision_web.py`:

```python
# Configurazione camera
camera_index = 0  # Cambia se usi camera diversa
frame_width = 640
frame_height = 480
fps = 30
```

### Soglie Detection

Nel monitoring, regola:
- **Confidenza**: 0.1 - 1.0 (default: 0.5)
- **Classi**: person, bag, backpack, handbag, etc.

### Performance Tuning

Per ottimizzare su Jetson:

```python
# In jewelry_vision_web.py
JETSON_OPTIMIZATIONS = {
    'frame_width': 640,      # Risoluzione bilanciata
    'frame_height': 480,
    'fps': 30,               # Frame rate target
    'detection_interval': 3,  # Detection ogni N frame
    'jpeg_quality': 85,      # Compressione streaming
    'buffer_size': 1         # Buffer camera
}
```

## 📊 **Monitoraggio Sistema**

### Log Files
- `logs/jewelry_vision.log` - Log generale sistema
- `logs/detection_*.json` - Log detection con metadata
- `captures/detection_*.jpg` - Frame salvati con detection

### API Endpoints

```http
GET  /                          # Menu principale
GET  /surveillance             # Streaming video
GET  /monitoring               # Detection & monitoring
GET  /video_feed               # Stream MJPEG surveillance
GET  /detection_feed           # Stream MJPEG con detection

POST /api/start_streaming      # Avvia streaming
POST /api/stop_streaming       # Ferma streaming
POST /api/start_monitoring     # Avvia monitoring  
POST /api/stop_monitoring      # Ferma monitoring
POST /api/capture_frame        # Cattura frame
GET  /api/monitoring_status    # Stato sistema
```

## 🧪 **Testing**

### Test Basic Functionality

```bash
# Test server
curl http://localhost:5000

# Test streaming endpoint
curl -I http://localhost:5000/video_feed

# Test detection endpoint  
curl -I http://localhost:5000/detection_feed

# Test API
curl -X POST http://localhost:5000/api/start_monitoring
```

### Test Performance

```bash
# Monitor CPU/GPU usage
sudo tegrastats

# Monitor memoria
free -h

# Monitor temperatura
cat /sys/class/thermal/thermal_zone*/temp
```

## 🔮 **Roadmap**

### ✅ **Completato**
- [x] Menu principale con navigazione diamante
- [x] Video streaming ottimizzato per Jetson
- [x] Detection & monitoring con YOLO11
- [x] Sistema di log e statistiche
- [x] Smart camera switching
- [x] Interfacce responsive

### 🚧 **In Sviluppo**
- [ ] **Dataset Management** - Gestione dataset per training
- [ ] **Model Training** - Training modelli personalizzati  
- [ ] **System Settings** - Configurazioni avanzate
- [ ] **Multi-camera Support** - Supporto telecamere multiple
- [ ] **Cloud Integration** - Backup e notifiche cloud

### 💡 **Pianificato**
- [ ] **Mobile App** - App companion per controllo remoto
- [ ] **Analytics Dashboard** - Analytics avanzati e report
- [ ] **Alert System** - Sistema notifiche intelligenti
- [ ] **Database Integration** - Storage detection in DB
- [ ] **Docker Support** - Containerizzazione sistema

## 🛠️ **Troubleshooting**

### Camera Non Rilevata

```bash
# Verifica dispositivi video
ls -la /dev/video*

# Test camera manuale
ffplay /dev/video0

# Permessi camera
sudo usermod -a -G video $USER
```

### Performance Issues

```bash
# Incrementa memoria GPU
sudo systemctl edit nvargus-daemon
# Aggiungi: Environment="GST_PLUGIN_PATH=/usr/lib/aarch64-linux-gnu/gstreamer-1.0"

# Ottimizza frequenza GPU
sudo /usr/bin/jetson_clocks
```

### YOLO Model Issues

```bash
# Re-download modello
rm -rf models/yolo11n.pt
python -c "from ultralytics import YOLO; YOLO('yolo11n.pt')"

# Verifica CUDA
python -c "import torch; print(torch.cuda.is_available())"
```

## 📚 **Documentazione Avanzata**

- [**Guida Installazione Dettagliata**](docs/INSTALL.md)
- [**Architettura Sistema**](docs/ARCHITECTURE.md) 
- [**API Reference**](docs/API.md)
- [**Guida Sviluppatore**](docs/DEVELOPMENT.md)

## 🤝 **Contribuire**

1. **Fork** il repository
2. **Crea** un branch per la feature (`git checkout -b feature/amazing-feature`)
3. **Commit** le modifiche (`git commit -m 'Add amazing feature'`)
4. **Push** al branch (`git push origin feature/amazing-feature`)
5. **Apri** una Pull Request

## 📄 **Licenza**

Questo progetto è rilasciato sotto licenza **MIT**. Vedi il file [LICENSE](LICENSE) per i dettagli.

## 🙏 **Riconoscimenti**

- **NVIDIA** per la piattaforma Jetson Orin Nano
- **Ultralytics** per il framework YOLO11
- **Flask** team per il framework web
- **OpenCV** community per le librerie computer vision

## 📞 **Supporto**

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/tuousername/jewelry-vision/issues)
- 💡 **Feature Requests**: [GitHub Discussions](https://github.com/tuousername/jewelry-vision/discussions)
- 📧 **Email**: tuo.email@example.com

---

<p align="center">
  <b>Fatto con ❤️ per la sicurezza delle gioiellerie</b><br>
  <sub>Powered by NVIDIA Jetson Orin Nano 💚</sub>
</p>
