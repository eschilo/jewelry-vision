#!/bin/bash
# Enhanced Backup Integration - Compatibile con sistema esistente

cd ~/jewelry_vision

echo "=== JEWELRY VISION ENHANCED BACKUP INTEGRATION ==="
echo "Data: $(date)"
echo "=================================================="

# File enhanced da includere nel backup
ENHANCED_FILES=(
    "jewelry_vision_web_enhanced_minimal.py"
    "control_enhanced.sh"
    "enhanced.log"
    "enhanced_config.json"
    "templates/enhanced_panel.html"
)

# 1. Pre-backup: Commit Git se necessario
if [ -d ".git" ] && [ -n "$(git status --porcelain)" ]; then
    echo "Commit modifiche Git prima del backup..."
    git add .
    git commit -m "Auto-commit before enhanced backup - $(date)"
fi

# 2. Esegui backup sistema principale
echo "Esecuzione backup sistema principale..."
~/backup_jewelry_vision.sh

# 3. Crea directory enhanced nel backup
BACKUP_ROOT="$HOME/jewelry_vision_backups"
LATEST_BACKUP=$(ls -td "$BACKUP_ROOT"/external_transfer/jewelry_vision_deploy_* 2>/dev/null | head -1)

if [ -n "$LATEST_BACKUP" ] && [ -d "$LATEST_BACKUP" ]; then
    echo "Integrazione file enhanced nel backup: $LATEST_BACKUP"
    
    # Aggiungi file enhanced
    for file in "${ENHANCED_FILES[@]}"; do
        if [ -f "$file" ]; then
            cp "$file" "$LATEST_BACKUP/" 2>/dev/null
            echo "  ✓ $file"
        fi
    done
    
    # Crea manifest enhanced
    cat > "$LATEST_BACKUP/ENHANCED_MANIFEST.txt" << EOF
JEWELRY VISION ENHANCED - DEPLOYMENT MANIFEST
============================================
Data: $(date)
Versione: Step 1 - Framework Integration

FILE ENHANCED INCLUSI:
- jewelry_vision_web_enhanced_minimal.py  = Sistema enhanced principale
- control_enhanced.sh                     = Script controllo enhanced
- templates/enhanced_panel.html           = Interfaccia enhanced
- enhanced_config.json                    = Configurazione (se presente)

INSTALLAZIONE SU PRODUZIONE:
1. Estrai pacchetto deployment normale
2. Copia file enhanced nella directory jewelry_vision/
3. Rendi eseguibile: chmod +x control_enhanced.sh
4. Avvia enhanced: ./control_enhanced.sh start
5. Accedi a: http://localhost:5000/enhanced_panel

ROLLBACK A SISTEMA BASE:
./control_enhanced.sh rollback

PRIVACY MODE:
Il sistema enhanced rispetta la privacy mode esistente.
Nessuna connessione internet richiesta per funzionamento.
EOF
    
    echo "✅ Enhanced integration completata"
else
    echo "⚠️  Backup principale non trovato, creazione standalone..."
    
    # Crea backup enhanced standalone
    ENHANCED_BACKUP="$BACKUP_ROOT/enhanced_backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$ENHANCED_BACKUP"
    
    for file in "${ENHANCED_FILES[@]}"; do
        if [ -f "$file" ]; then
            cp "$file" "$ENHANCED_BACKUP/"
        fi
    done
    
    echo "✅ Enhanced backup standalone: $ENHANCED_BACKUP"
fi

echo "=================================================="
echo "✅ ENHANCED BACKUP INTEGRATION COMPLETATA"
echo "=================================================="
