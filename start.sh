#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$SCRIPT_DIR/.venv/bin/python3"
APP="$SCRIPT_DIR/qt_gui_refactored.py"
OLLAMA_PID_FILE="/tmp/thoughtmachine_ollama.pid"

# --- Farben ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

stop() {
    echo -e "${YELLOW}Stoppe ThoughtMachine...${NC}"

    # App beenden falls als Hintergrundprozess
    if [ -f "/tmp/thoughtmachine_app.pid" ]; then
        kill "$(cat /tmp/thoughtmachine_app.pid)" 2>/dev/null
        rm -f /tmp/thoughtmachine_app.pid
        echo -e "${GREEN}App gestoppt.${NC}"
    fi

    # Ollama nur stoppen wenn wir es gestartet haben
    if [ -f "$OLLAMA_PID_FILE" ]; then
        echo -e "${YELLOW}Stoppe Ollama (wurde von diesem Script gestartet)...${NC}"
        kill "$(cat $OLLAMA_PID_FILE)" 2>/dev/null
        rm -f "$OLLAMA_PID_FILE"
        echo -e "${GREEN}Ollama gestoppt.${NC}"
    else
        echo -e "${YELLOW}Ollama läuft weiter (wurde nicht von diesem Script gestartet).${NC}"
    fi
    exit 0
}

# stop-Argument
if [ "$1" == "stop" ]; then
    stop
fi

echo -e "${GREEN}=== ThoughtMachine Starter ===${NC}"

# --- Ollama Check ---
if curl -s http://localhost:11434 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Ollama läuft bereits.${NC}"
else
    echo -e "${YELLOW}Ollama nicht gefunden, starte...${NC}"
    ollama serve > /tmp/ollama.log 2>&1 &
    echo $! > "$OLLAMA_PID_FILE"

    # Warten bis Ollama bereit ist (max 15s)
    for i in $(seq 1 15); do
        sleep 1
        if curl -s http://localhost:11434 > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Ollama gestartet.${NC}"
            break
        fi
        if [ "$i" -eq 15 ]; then
            echo -e "${RED}✗ Ollama konnte nicht gestartet werden. Abbruch.${NC}"
            rm -f "$OLLAMA_PID_FILE"
            exit 1
        fi
    done
fi

# --- App starten ---
echo -e "${GREEN}Starte ThoughtMachine (phi3:mini)...${NC}"
echo -e "${YELLOW}Zum Beenden: ./start.sh stop${NC}"

cd "$SCRIPT_DIR"
"$VENV" "$APP"
