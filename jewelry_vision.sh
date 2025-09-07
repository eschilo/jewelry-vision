#!/bin/bash
# 💎 JEWELRY VISION SYSTEM - Main Launcher
# Sistema completo di videosorveglianza intelligente per gioielli

set -e

# === CONFIGURAZIONE ===
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"
LOG_DIR="$PROJECT_DIR/logs"

# Colori
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m'

log_message() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    mkdir -p "$LOG_DIR"
    echo "[$timestamp] [$level] $message" >> "$LOG_DIR/jewelry_vision.log"
}

show_header() {
    clear
    echo -e "${PURPLE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║                    ${WHITE}💎 JEWELRY VISION SYSTEM${NC}                   ${PURPLE}║${NC}"
    echo -e "${PURPLE}║              ${CYAN}Sistema di Videosorveglianza Intelligente${NC}            ${PURPLE}║${NC}"
    echo -e "${PURPLE}╠════════════════════════════════════════════════════════════╣${NC}"
    echo -e "${PURPLE}║  ${YELLOW}🎯 Obiettivo:${NC} Protezione e monitoraggio gioielli h24        ${PURPLE}║${NC}"
    echo -e "${PURPLE}║  ${YELLOW}🚀 Platform:${NC} Jetson Orin Nano Super + YOLO11 + AI        ${PURPLE}║${NC}"
    echo -e "${PURPLE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${BLUE}📁 Project Directory:${NC} $PROJECT_DIR"
    echo -e "${BLUE}🕐 Current Time:${NC} $(date '+%Y-%m-%d %H:%M:%S')"
    echo -e "${BLUE}👤 User:${NC} $(whoami)@$(hostname)"
    echo ""
}

show_main_menu() {
    echo -e "${WHITE}╔══════════════════ MODULI PRINCIPALI ═══════════════════╗${NC}"
    echo -e "${WHITE}║                                                          ║${NC}"
    echo -e "${WHITE}║  ${RED}1${NC} - ${WHITE}VIDEOSORVEGLIANZA & ALLARMI${NC}                      ║${NC}"
    echo -e "${WHITE}║      Monitor continuo vetrina gioielli                  ║${NC}"
    echo -e "${WHITE}║      Rilevamento sottrazione/spostamento               ║${NC}"
    echo -e "${WHITE}║      Notifiche immediate multi-canale                  ║${NC}"
    echo -e "${WHITE}║      Human detection anti-falsi allarmi                ║${NC}"
    echo -e "${WHITE}║                                                          ║${NC}"
    echo -e "${WHITE}║  ${YELLOW}2${NC} - ${WHITE}TRAINING & LEARNING SYSTEM${NC}                     ║${NC}"
    echo -e "${WHITE}║      Addestramento continuo del modello                ║${NC}"
    echo -e "${WHITE}║      Riduzione automatica falsi allarmi                ║${NC}"
    echo -e "${WHITE}║      Performance analytics e ottimizzazione            ║${NC}"
    echo -e "${WHITE}║      Feedback loop intelligente                        ║${NC}"
    echo -e "${WHITE}║                                                          ║${NC}"
    echo -e "${WHITE}║  ${GREEN}3${NC} - ${WHITE}DATASET & VALIDATION${NC}                           ║${NC}"
    echo -e "${WHITE}║      Raccolta e organizzazione dati                    ║${NC}"
    echo -e "${WHITE}║      Annotazione intelligente batch                    ║${NC}"
    echo -e "${WHITE}║      Integrazione dataset esterni                      ║${NC}"
    echo -e "${WHITE}║      Etichette personalizzabili                        ║${NC}"
    echo -e "${WHITE}║                                                          ║${NC}"
    echo -e "${WHITE}║  ${BLUE}4${NC} - ${WHITE}SYSTEM CONFIGURATION${NC}                            ║${NC}"
    echo -e "${WHITE}║      Configurazione generale sistema                   ║${NC}"
    echo -e "${WHITE}║      Gestione hardware e performance                   ║${NC}"
    echo -e "${WHITE}║      Backup e manutenzione                             ║${NC}"
    echo -e "${WHITE}║                                                          ║${NC}"
    echo -e "${WHITE}║  ${PURPLE}5${NC} - ${WHITE}DASHBOARD & MONITORING${NC}                         ║${NC}"
    echo -e "${WHITE}║      Dashboard real-time completo                      ║${NC}"
    echo -e "${WHITE}║      Statistiche e analytics                           ║${NC}"
    echo -e "${WHITE}║      Report e export dati                              ║${NC}"
    echo -e "${WHITE}║                                                          ║${NC}"
    echo -e "${WHITE}║  ${RED}0${NC} - ${WHITE}ESCI DAL SISTEMA${NC}                               ║${NC}"
    echo -e "${WHITE}║                                                          ║${NC}"
    echo -e "${WHITE}╚══════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

show_status_bar() {
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}' || echo "N/A")
    local mem_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}' || echo "N/A")
    local gpu_temp=$(cat /sys/devices/virtual/thermal/thermal_zone0/temp 2>/dev/null | awk '{print $1/1000"°C"}' || echo "N/A")
    
    echo -e "${BLUE}💻 CPU: ${cpu_usage}% │ 🧠 RAM: ${mem_usage}% │ 🌡️  Temp: ${gpu_temp} │ 📡 Status: ${GREEN}Online${NC}"
    echo ""
}

check_system_status() {
    echo -e "${CYAN}🔍 Controllo stato sistema...${NC}"
    
    local errors=0
    
    if ! ls /dev/video* >/dev/null 2>&1; then
        echo -e "${RED}❌ Nessuna camera rilevata${NC}"
        ((errors++))
    else
        echo -e "${GREEN}✅ Camera disponibile${NC}"
    fi
    
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python3 non trovato${NC}"
        ((errors++))
    else
        echo -e "${GREEN}✅ Python3 disponibile${NC}"
    fi
    
    if [ ! -f "$PROJECT_DIR/yolo11n.pt" ]; then
        echo -e "${YELLOW}⚠️  Modello YOLO11 non trovato${NC}"
    else
        echo -e "${GREEN}✅ Modello YOLO11 presente${NC}"
    fi
    
    local available_space=$(df -h "$PROJECT_DIR" | tail -1 | awk '{print $4}')
    echo -e "${BLUE}💾 Spazio disponibile: $available_space${NC}"
    
    if [ "$errors" -eq 0 ]; then
        echo -e "\n${GREEN}🎯 Sistema pronto per l'utilizzo!${NC}"
    else
        echo -e "\n${YELLOW}⚠️  Alcuni componenti richiedono attenzione${NC}"
    fi
    
    echo ""
}

# Funzioni semplificate per test
launch_surveillance_module() {
    echo -e "\n${WHITE}🚨 MODULO VIDEOSORVEGLIANZA${NC}"
    echo -e "${WHITE}════════════════════════════${NC}"
    echo -e "${YELLOW}Avvio jewelry_detector.py...${NC}"
    
    if [ -f "$PROJECT_DIR/jewelry_detector.py" ]; then
        python3 "$PROJECT_DIR/jewelry_detector.py" || echo -e "${RED}Errore esecuzione${NC}"
    else
        echo -e "${RED}File jewelry_detector.py non trovato${NC}"
    fi
    
    read -p "Premi INVIO per tornare al menu..."
}

launch_training_module() {
    echo -e "\n${WHITE}🧠 MODULO TRAINING${NC}"
    echo -e "${WHITE}═══════════════════${NC}"
    echo -e "${YELLOW}Modulo training in sviluppo...${NC}"
    read -p "Premi INVIO per tornare al menu..."
}

launch_dataset_module() {
    echo -e "\n${WHITE}📊 MODULO DATASET${NC}"
    echo -e "${WHITE}══════════════════${NC}"
    
    if [ -f "$PROJECT_DIR/dataset_toolkit.sh" ]; then
        bash "$PROJECT_DIR/dataset_toolkit.sh"
    else
        echo -e "${YELLOW}Dataset toolkit non trovato${NC}"
    fi
    
    read -p "Premi INVIO per tornare al menu..."
}

launch_configuration_module() {
    echo -e "\n${WHITE}⚙️  CONFIGURAZIONE${NC}"
    echo -e "${WHITE}═══════════════════${NC}"
    echo -e "${YELLOW}Modulo configurazione in sviluppo...${NC}"
    read -p "Premi INVIO per tornare al menu..."
}

launch_dashboard_module() {
    echo -e "\n${WHITE}📊 DASHBOARD${NC}"
    echo -e "${WHITE}═════════════${NC}"
    echo -e "${YELLOW}Modulo dashboard in sviluppo...${NC}"
    read -p "Premi INVIO per tornare al menu..."
}

main_menu() {
    while true; do
        show_header
        show_status_bar
        check_system_status
        show_main_menu
        
        read -p "$(echo -e ${WHITE}Seleziona modulo [1-5] o 0 per uscire:${NC} )" choice
        
        case "$choice" in
            1) launch_surveillance_module ;;
            2) launch_training_module ;;
            3) launch_dataset_module ;;
            4) launch_configuration_module ;;
            5) launch_dashboard_module ;;
            0|exit|quit|q)
                echo -e "\n${GREEN}👋 Arrivederci! Jewelry Vision System terminato.${NC}"
                exit 0
                ;;
            *)
                echo -e "\n${RED}❌ Opzione non valida: '$choice'${NC}"
                read -p "Premi INVIO per continuare..."
                ;;
        esac
    done
}

initialize_system() {
    mkdir -p "$LOG_DIR" "$PROJECT_DIR/config" "$PROJECT_DIR/backups"
    log_message "INFO" "Sistema avviato da $(whoami)"
}

main() {
    initialize_system
    main_menu
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
