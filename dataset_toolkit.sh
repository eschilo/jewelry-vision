#!/bin/bash

# Jewelry Dataset Toolkit Launcher
# Script unificato per gestione completa dataset gioielli

set -e

# Configurazione
DATASET_DIR="$HOME/jewelry_vision/dataset"
SCRIPT_DIR="$HOME/jewelry_vision"

# Colori per output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Funzioni utility
print_header() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║              JEWELRY DATASET TOOLKIT v1.0                   ║"
    echo "║          Sistema completo per gestione dataset              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_section() {
    echo -e "${BLUE}📍 $1${NC}"
    echo "────────────────────────────────────────────────"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_dependencies() {
    print_section "Checking Dependencies"
    
    # Verifica Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 not found!"
        exit 1
    fi
    print_success "Python3 found: $(python3 --version)"
    
    # Verifica pip packages
    required_packages=("cv2" "numpy" "pathlib")
    for package in "${required_packages[@]}"; do
        if ! python3 -c "import $package" 2>/dev/null; then
            print_warning "Package $package not found, installing..."
            pip3 install opencv-python numpy
        else
            print_success "Package $package: OK"
        fi
    done
}

setup_directories() {
    print_section "Setting up Dataset Directory Structure"
    
    mkdir -p "$DATASET_DIR"/{images/{raw,processed},annotations/{temp,yolo,coco},exports,backups}
    
    print_success "Directory structure created at $DATASET_DIR"
    
    # Crea directory script se non esiste
    mkdir -p "$SCRIPT_DIR"
    print_success "Script directory ready at $SCRIPT_DIR"
}

create_scripts() {
    print_section "Installing Dataset Tools"
    
    # File già creati nei precedenti artifact
    tools=("dataset_collector.py" "batch_annotator.py" "dataset_manager.py")
    
    for tool in "${tools[@]}"; do
        if [ -f "$SCRIPT_DIR/$tool" ]; then
            print_success "$tool: Already installed"
        else
            print_warning "$tool: Not found - please copy the scripts to $SCRIPT_DIR"
        fi
    done
}

show_menu() {
    echo -e "${CYAN}"
    echo "🛠️  DATASET TOOLKIT MENU"
    echo "═══════════════════════════"
    echo -e "${NC}"
    echo "1) 📸 Dataset Collection    - Raccolta interattiva immagini"
    echo "2) ✏️  Batch Annotation     - Annotazione rapida batch"
    echo "3) 📊 Dataset Manager       - Gestione e validazione"
    echo "4) 📈 Dataset Report        - Report dettagliato"
    echo "5) 🔄 Export YOLO Dataset   - Esportazione per training"
    echo "6) 💾 Backup Dataset        - Backup completo"
    echo "7) 🧹 Clean Dataset         - Pulizia file corrotti"
    echo "8) 📂 Open Dataset Folder   - Apri cartella dataset"
    echo "9) 🔧 System Status         - Verifica sistema"
    echo "0) ❌ Exit"
    echo ""
    echo -e "Dataset directory: ${YELLOW}$DATASET_DIR${NC}"
    echo ""
}

run_dataset_collection() {
    print_section "Starting Dataset Collection Interface"
    
    if [ ! -f "$SCRIPT_DIR/dataset_collector.py" ]; then
        print_error "dataset_collector.py not found in $SCRIPT_DIR"
        return 1
    fi
    
    echo "Camera options:"
    echo "0) Default camera (USB/integrated)"
    echo "1) External USB camera"
    echo "2) IP camera (requires URL modification in script)"
    
    read -p "Select camera (0-2): " camera_choice
    
    case $camera_choice in
        0|1) 
            python3 "$SCRIPT_DIR/dataset_collector.py" --camera "$camera_choice" --dataset-dir "$DATASET_DIR"
            ;;
        2)
            print_warning "For IP camera, modify the script to use your camera URL"
            python3 "$SCRIPT_DIR/dataset_collector.py" --camera 0 --dataset-dir "$DATASET_DIR"
            ;;
        *)
            print_error "Invalid camera selection"
            ;;
    esac
}

run_batch_annotator() {
    print_section "Starting Batch Annotation Interface"
    
    if [ ! -f "$SCRIPT_DIR/batch_annotator.py" ]; then
        print_error "batch_annotator.py not found in $SCRIPT_DIR"
        return 1
    fi
    
    # Verifica se ci sono immagini da annotare
    if [ ! -d "$DATASET_DIR/images/raw" ] || [ -z "$(ls -A $DATASET_DIR/images/raw)" ]; then
        print_warning "No raw images found. Please collect some images first."
        return 1
    fi
    
    python3 "$SCRIPT_DIR/batch_annotator.py" --dataset-dir "$DATASET_DIR"
}

run_dataset_manager() {
    print_section "Dataset Manager Options"
    
    if [ ! -f "$SCRIPT_DIR/dataset_manager.py" ]; then
        print_error "dataset_manager.py not found in $SCRIPT_DIR"
        return 1
    fi
    
    echo "Available actions:"
    echo "1) Scan dataset"
    echo "2) Validate dataset"
    echo "3) Clean dataset"
    echo "4) Create train/val split"
    echo "5) Export YOLO dataset"
    echo "6) Full analysis (all actions)"
    
    read -p "Select action (1-6): " action_choice
    
    case $action_choice in
        1) python3 "$SCRIPT_DIR/dataset_manager.py" --action scan --dataset-dir "$DATASET_DIR" ;;
        2) python3 "$SCRIPT_DIR/dataset_manager.py" --action validate --dataset-dir "$DATASET_DIR" ;;
        3) python3 "$SCRIPT_DIR/dataset_manager.py" --action clean --dataset-dir "$DATASET_DIR" --remove-orphans ;;
        4) python3 "$SCRIPT_DIR/dataset_manager.py" --action split --dataset-dir "$DATASET_DIR" ;;
        5) python3 "$SCRIPT_DIR/dataset_manager.py" --action export --dataset-dir "$DATASET_DIR" ;;
        6) python3 "$SCRIPT_DIR/dataset_manager.py" --action all --dataset-dir "$DATASET_DIR" ;;
        *) print_error "Invalid action selection" ;;
    esac
}

show_system_status() {
    print_section "System Status Check"
    
    echo "💻 SYSTEM INFO"
    echo "OS: $(uname -s)"
    echo "Architecture: $(uname -m)"
    echo "Python: $(python3 --version)"
    
    if command -v nvidia-smi &> /dev/null; then
        echo "GPU: $(nvidia-smi --query-gpu=name --format=csv,noheader,nounits | head -1)"
        echo "CUDA: $(nvidia-smi --query-gpu=driver_version --format=csv,noheader,nounits | head -1)"
    else
        echo "GPU: No NVIDIA GPU detected"
    fi
    
    echo ""
    echo "📁 DATASET STATUS"
    
    if [ -d "$DATASET_DIR" ]; then
        raw_images=$(find "$DATASET_DIR/images/raw" -type f \( -name "*.jpg" -o -name "*.png" -o -name "*.jpeg" \) 2>/dev/null | wc -l)
        annotations=$(find "$DATASET_DIR/annotations/temp" -name "*.json" 2>/dev/null | wc -l)
        
        echo "Raw images: $raw_images"
        echo "Annotations: $annotations"
        echo "Dataset size: $(du -sh $DATASET_DIR 2>/dev/null | cut -f1)"
        
        # Verifica completezza
        if [ $raw_images -gt 0 ] && [ $annotations -gt 0 ]; then
            print_success "Dataset ready for training preparation"
        elif [ $raw_images -gt 0 ]; then
            print_warning "Images found but no annotations"
        else
            print_warning "No dataset found - start with data collection"
        fi
    else
        print_warning "Dataset directory not found"
    fi
    
    echo ""
    echo "🛠️  TOOLS STATUS"
    
    tools=("dataset_collector.py" "batch_annotator.py" "dataset_manager.py")
    for tool in "${tools[@]}"; do
        if [ -f "$SCRIPT_DIR/$tool" ]; then
            print_success "$tool: Installed"
        else
            print_error "$tool: Missing"
        fi
    done
}

create_desktop_shortcuts() {
    print_section "Creating Desktop Shortcuts"
    
    if [ ! -d "$HOME/Desktop" ]; then
        mkdir -p "$HOME/Desktop"
    fi
    
    # Shortcut per dataset collection
    cat > "$HOME/Desktop/jewelry_dataset_collection.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Jewelry Dataset Collection
Comment=Collect jewelry images for dataset
Exec=gnome-terminal -- bash -c 'cd $SCRIPT_DIR && ./dataset_toolkit.sh; read -p "Press Enter to close..."'
Icon=camera-photo
Terminal=false
Categories=Development;
EOF
    
    chmod +x "$HOME/Desktop/jewelry_dataset_collection.desktop"
    print_success "Desktop shortcut created"
}

# Script principale
main() {
    print_header
    
    # Setup iniziale
    check_dependencies
    setup_directories
    create_scripts
    
    # Menu principale
    while true; do
        echo ""
        show_menu
        read -p "Seleziona opzione (0-9): " choice
        
        case $choice in
            1)
                run_dataset_collection
                ;;
            2)
                run_batch_annotator
                ;;
            3)
                run_dataset_manager
                ;;
            4)
                if [ -f "$SCRIPT_DIR/dataset_manager.py" ]; then
                    python3 "$SCRIPT_DIR/dataset_manager.py" --action report --dataset-dir "$DATASET_DIR"
                else
                    print_error "dataset_manager.py not found"
                fi
                ;;
            5)
                if [ -f "$SCRIPT_DIR/dataset_manager.py" ]; then
                    python3 "$SCRIPT_DIR/dataset_manager.py" --action export --dataset-dir "$DATASET_DIR"
                else
                    print_error "dataset_manager.py not found"
                fi
                ;;
            6)
                if [ -f "$SCRIPT_DIR/dataset_manager.py" ]; then
                    python3 "$SCRIPT_DIR/dataset_manager.py" --action backup --dataset-dir "$DATASET_DIR"
                else
                    print_error "dataset_manager.py not found"
                fi
                ;;
            7)
                if [ -f "$SCRIPT_DIR/dataset_manager.py" ]; then
                    python3 "$SCRIPT_DIR/dataset_manager.py" --action clean --dataset-dir "$DATASET_DIR" --remove-orphans
                else
                    print_error "dataset_manager.py not found"
                fi
                ;;
            8)
                if command -v nautilus &> /dev/null; then
                    nautilus "$DATASET_DIR" &
                elif command -v thunar &> /dev/null; then
                    thunar "$DATASET_DIR" &
                else
                    echo "Dataset directory: $DATASET_DIR"
                fi
                print_success "Opening dataset folder..."
                ;;
            9)
                show_system_status
                ;;
            0)
                print_success "Goodbye!"
                exit 0
                ;;
            *)
                print_error "Opzione non valida. Riprova."
                ;;
        esac
        continue  # Torna al menu dopo ogni opzione
        
        echo ""
        read -p "Premi Enter per continuare..."
    done
}

# Avvia script
main "$@"
