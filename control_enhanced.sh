#!/bin/bash
# Controllo Enhanced System

case "$1" in
    start)
        echo "Avvio Enhanced System..."
        pkill -f jewelry_vision_web.py 2>/dev/null
        nohup python3 jewelry_vision_web_enhanced_minimal.py > enhanced.log 2>&1 &
        echo $! > enhanced.pid
        echo "Sistema enhanced avviato (PID: $(cat enhanced.pid))"
        ;;
    stop)
        if [ -f enhanced.pid ]; then
            kill $(cat enhanced.pid) 2>/dev/null
            rm -f enhanced.pid
            echo "Sistema enhanced fermato"
        else
            pkill -f jewelry_vision_web_enhanced_minimal.py
            echo "Sistema enhanced fermato (fallback)"
        fi
        ;;
    status)
        if [ -f enhanced.pid ] && ps -p $(cat enhanced.pid) > /dev/null; then
            echo "Sistema enhanced attivo (PID: $(cat enhanced.pid))"
        else
            echo "Sistema enhanced non attivo"
        fi
        ;;
    rollback)
        $0 stop
        python3 jewelry_vision_web.py &
        echo "Rollback al sistema base completato"
        ;;
    *)
        echo "Uso: $0 {start|stop|status|rollback}"
        ;;
esac
