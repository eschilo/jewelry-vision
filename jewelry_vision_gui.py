#!/usr/bin/env python3
"""
Jewelry Vision System - Main GUI Interface
Sistema completo di videosorveglianza intelligente per gioielli
Jetson Orin Nano Super - Settembre 2025
"""

import tkinter as tk
from tkinter import ttk, messagebox, PhotoImage
import subprocess
import os
import sys
from pathlib import Path
import threading
import time
from datetime import datetime

class JewelryVisionGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("💎 Jewelry Vision System")
        self.root.geometry("800x600")
        self.root.configure(bg='#1a1a2e')
        
        # Colori tema
        self.colors = {
            'bg_primary': '#1a1a2e',
            'bg_secondary': '#16213e', 
            'accent': '#0f3460',
            'gold': '#ffd700',
            'white': '#ffffff',
            'gray': '#cccccc',
            'success': '#4CAF50',
            'warning': '#FF9800',
            'error': '#f44336'
        }
        
        self.setup_styles()
        self.create_main_interface()
        
        # Sistema di monitoraggio
        self.monitoring_active = False
        self.detector_process = None
        
    def setup_styles(self):
        """Configura gli stili per l'interfaccia"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Stile per i bottoni principali
        style.configure('Main.TButton',
                       font=('Segoe UI', 12, 'bold'),
                       foreground=self.colors['white'],
                       background=self.colors['accent'],
                       borderwidth=0,
                       focuscolor='none')
        
        style.map('Main.TButton',
                 background=[('active', self.colors['gold']),
                           ('pressed', self.colors['gold'])])
        
        # Stile per i frame
        style.configure('Main.TFrame',
                       background=self.colors['bg_primary'])
        
        style.configure('Card.TFrame',
                       background=self.colors['bg_secondary'],
                       relief='raised',
                       borderwidth=1)
    
    def create_main_interface(self):
        """Crea l'interfaccia principale con icona centrale"""
        # Frame principale
        main_frame = ttk.Frame(self.root, style='Main.TFrame')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Header con titolo e status
        self.create_header(main_frame)
        
        # Area centrale con icona principale
        self.create_center_area(main_frame)
        
        # Status bar in basso
        self.create_status_bar(main_frame)
        
        # Menu nascosto (inizialmente)
        self.menu_frame = None
        self.menu_visible = False
    
    def create_header(self, parent):
        """Crea l'header con titolo e informazioni"""
        header_frame = ttk.Frame(parent, style='Card.TFrame')
        header_frame.pack(fill='x', pady=(0, 20))
        
        # Titolo principale
        title_label = tk.Label(header_frame,
                              text="💎 JEWELRY VISION SYSTEM",
                              font=('Segoe UI', 24, 'bold'),
                              fg=self.colors['gold'],
                              bg=self.colors['bg_secondary'])
        title_label.pack(pady=15)
        
        # Sottotitolo
        subtitle_label = tk.Label(header_frame,
                                 text="Sistema Intelligente di Videosorveglianza per Gioiellerie",
                                 font=('Segoe UI', 12),
                                 fg=self.colors['gray'],
                                 bg=self.colors['bg_secondary'])
        subtitle_label.pack(pady=(0, 10))
        
        # Status indicators
        status_frame = tk.Frame(header_frame, bg=self.colors['bg_secondary'])
        status_frame.pack(fill='x', padx=20, pady=(0, 15))
        
        self.create_status_indicator(status_frame, "🎯 YOLO11", "READY", self.colors['success'])
        self.create_status_indicator(status_frame, "📷 CAMERA", "READY", self.colors['success'])
        self.create_status_indicator(status_frame, "🔔 ALERTS", "STANDBY", self.colors['warning'])
    
    def create_status_indicator(self, parent, label, status, color):
        """Crea un indicatore di status"""
        indicator_frame = tk.Frame(parent, bg=self.colors['bg_secondary'])
        indicator_frame.pack(side='left', fill='x', expand=True, padx=10)
        
        tk.Label(indicator_frame, text=label, 
                font=('Segoe UI', 10, 'bold'),
                fg=self.colors['white'],
                bg=self.colors['bg_secondary']).pack()
        
        tk.Label(indicator_frame, text=status,
                font=('Segoe UI', 9),
                fg=color,
                bg=self.colors['bg_secondary']).pack()
    
    def create_center_area(self, parent):
        """Crea l'area centrale con l'icona principale cliccabile"""
        center_frame = ttk.Frame(parent, style='Main.TFrame')
        center_frame.pack(fill='both', expand=True)
        
        # Container per l'icona principale
        icon_container = tk.Frame(center_frame, bg=self.colors['bg_primary'])
        icon_container.pack(expand=True)
        
        # Icona principale cliccabile (grande diamante)
        self.main_icon = tk.Button(icon_container,
                                  text="💎",
                                  font=('Segoe UI', 120),
                                  bg=self.colors['bg_primary'],
                                  fg=self.colors['gold'],
                                  bd=0,
                                  activebackground=self.colors['bg_primary'],
                                  activeforeground=self.colors['white'],
                                  cursor='hand2',
                                  command=self.toggle_main_menu)
        self.main_icon.pack(pady=20)
        
        # Testo sotto l'icona
        instruction_label = tk.Label(icon_container,
                                   text="Clicca per aprire il Menu Principale",
                                   font=('Segoe UI', 14, 'italic'),
                                   fg=self.colors['gray'],
                                   bg=self.colors['bg_primary'])
        instruction_label.pack(pady=10)
        
        # Quick actions (sempre visibili)
        self.create_quick_actions(center_frame)
    
    def create_quick_actions(self, parent):
        """Crea i pulsanti di azione rapida"""
        quick_frame = tk.Frame(parent, bg=self.colors['bg_primary'])
        quick_frame.pack(fill='x', pady=20)
        
        quick_title = tk.Label(quick_frame,
                              text="⚡ AZIONI RAPIDE",
                              font=('Segoe UI', 14, 'bold'),
                              fg=self.colors['white'],
                              bg=self.colors['bg_primary'])
        quick_title.pack(pady=(0, 15))
        
        buttons_frame = tk.Frame(quick_frame, bg=self.colors['bg_primary'])
        buttons_frame.pack()
        
        # Pulsanti rapidi
        quick_buttons = [
            ("🚨 START MONITORING", self.start_monitoring, self.colors['success']),
            ("⏹️ STOP MONITORING", self.stop_monitoring, self.colors['error']),
            ("📊 VIEW DASHBOARD", self.open_dashboard, self.colors['accent']),
        ]
        
        for text, command, color in quick_buttons:
            btn = tk.Button(buttons_frame,
                           text=text,
                           font=('Segoe UI', 10, 'bold'),
                           fg=self.colors['white'],
                           bg=color,
                           bd=0,
                           padx=20,
                           pady=10,
                           cursor='hand2',
                           command=command)
            btn.pack(side='left', padx=10)
    
    def toggle_main_menu(self):
        """Mostra/nasconde il menu principale"""
        if self.menu_visible:
            self.hide_main_menu()
        else:
            self.show_main_menu()
    
    def show_main_menu(self):
        """Mostra il menu principale"""
        if self.menu_frame:
            self.menu_frame.destroy()
        
        # Crea il menu
        self.menu_frame = tk.Toplevel(self.root)
        self.menu_frame.title("💎 Menu Principale - Jewelry Vision")
        self.menu_frame.geometry("600x500")
        self.menu_frame.configure(bg=self.colors['bg_secondary'])
        self.menu_frame.resizable(False, False)
        
        # Posiziona il menu al centro dello schermo principale
        self.menu_frame.transient(self.root)
        self.menu_frame.grab_set()
        
        # Header del menu
        header = tk.Label(self.menu_frame,
                         text="💎 JEWELRY VISION SYSTEM",
                         font=('Segoe UI', 18, 'bold'),
                         fg=self.colors['gold'],
                         bg=self.colors['bg_secondary'])
        header.pack(pady=20)
        
        # Menu items
        self.create_menu_items(self.menu_frame)
        
        self.menu_visible = True
        
        # Chiudi menu quando si clicca X
        self.menu_frame.protocol("WM_DELETE_WINDOW", self.hide_main_menu)
    
    def create_menu_items(self, parent):
        """Crea gli elementi del menu principale"""
        menu_items = [
            {
                'icon': '🚨',
                'title': 'VIDEOSORVEGLIANZA & ALLARMI',
                'desc': 'Detection continuo, human detection, notifiche',
                'command': self.open_surveillance_module
            },
            {
                'icon': '🧠',
                'title': 'TRAINING & LEARNING', 
                'desc': 'Riduzione falsi allarmi, feedback loop',
                'command': self.open_training_module
            },
            {
                'icon': '📊',
                'title': 'DATASET & VALIDATION',
                'desc': 'Raccolta dati, annotazione, validazione',
                'command': self.open_dataset_module
            },
            {
                'icon': '⚙️',
                'title': 'CONFIGURAZIONE SISTEMA',
                'desc': 'Impostazioni, calibrazione, backup',
                'command': self.open_settings_module
            },
            {
                'icon': '📈',
                'title': 'DASHBOARD & REPORT',
                'desc': 'Statistiche, report, monitoraggio prestazioni',
                'command': self.open_dashboard_module
            }
        ]
        
        for item in menu_items:
            self.create_menu_button(parent, item)
    
    def create_menu_button(self, parent, item):
        """Crea un pulsante del menu"""
        button_frame = tk.Frame(parent, bg=self.colors['accent'], relief='raised', bd=1)
        button_frame.pack(fill='x', padx=20, pady=5)
        
        # Rende il frame cliccabile
        button_frame.bind("<Button-1>", lambda e, cmd=item['command']: cmd())
        button_frame.bind("<Enter>", lambda e, f=button_frame: f.configure(bg=self.colors['gold']))
        button_frame.bind("<Leave>", lambda e, f=button_frame: f.configure(bg=self.colors['accent']))
        
        # Layout interno
        content_frame = tk.Frame(button_frame, bg=self.colors['accent'])
        content_frame.pack(fill='both', expand=True, padx=15, pady=10)
        content_frame.bind("<Button-1>", lambda e, cmd=item['command']: cmd())
        
        # Icona
        icon_label = tk.Label(content_frame,
                             text=item['icon'],
                             font=('Segoe UI', 24),
                             bg=self.colors['accent'],
                             fg=self.colors['white'])
        icon_label.pack(side='left', padx=(0, 15))
        icon_label.bind("<Button-1>", lambda e, cmd=item['command']: cmd())
        
        # Testo
        text_frame = tk.Frame(content_frame, bg=self.colors['accent'])
        text_frame.pack(side='left', fill='both', expand=True)
        text_frame.bind("<Button-1>", lambda e, cmd=item['command']: cmd())
        
        title_label = tk.Label(text_frame,
                              text=item['title'],
                              font=('Segoe UI', 12, 'bold'),
                              fg=self.colors['white'],
                              bg=self.colors['accent'],
                              anchor='w')
        title_label.pack(fill='x')
        title_label.bind("<Button-1>", lambda e, cmd=item['command']: cmd())
        
        desc_label = tk.Label(text_frame,
                             text=item['desc'],
                             font=('Segoe UI', 9),
                             fg=self.colors['gray'],
                             bg=self.colors['accent'],
                             anchor='w')
        desc_label.pack(fill='x')
        desc_label.bind("<Button-1>", lambda e, cmd=item['command']: cmd())
    
    def hide_main_menu(self):
        """Nasconde il menu principale"""
        if self.menu_frame:
            self.menu_frame.destroy()
            self.menu_frame = None
        self.menu_visible = False
    
    def create_status_bar(self, parent):
        """Crea la barra di stato in basso"""
        status_frame = ttk.Frame(parent, style='Card.TFrame')
        status_frame.pack(fill='x', side='bottom')
        
        # Info di sistema
        system_info = tk.Label(status_frame,
                              text=f"🚀 Jetson Orin Nano Super | 📅 {datetime.now().strftime('%d/%m/%Y %H:%M')} | 🔗 GitHub: jewelry-vision",
                              font=('Segoe UI', 9),
                              fg=self.colors['gray'],
                              bg=self.colors['bg_secondary'])
        system_info.pack(pady=5)
    
    # === METODI MODULI ===
    
    def open_surveillance_module(self):
        """Apre il modulo videosorveglianza"""
        self.hide_main_menu()
        messagebox.showinfo("Modulo Videosorveglianza", 
                           "🚨 Apertura modulo Videosorveglianza & Allarmi...")
        # TODO: Implementare interfaccia modulo sorveglianza
    
    def open_training_module(self):
        """Apre il modulo training"""
        self.hide_main_menu()
        messagebox.showinfo("Modulo Training", 
                           "🧠 Apertura modulo Training & Learning...")
        # TODO: Implementare interfaccia modulo training
    
    def open_dataset_module(self):
        """Apre il modulo dataset"""
        self.hide_main_menu()
        messagebox.showinfo("Modulo Dataset", 
                           "📊 Apertura modulo Dataset & Validation...")
        # TODO: Implementare interfaccia modulo dataset
    
    def open_settings_module(self):
        """Apre il modulo configurazioni"""
        self.hide_main_menu()
        messagebox.showinfo("Configurazione", 
                           "⚙️ Apertura modulo Configurazione Sistema...")
        # TODO: Implementare interfaccia configurazioni
    
    def open_dashboard_module(self):
        """Apre il modulo dashboard"""
        self.hide_main_menu()
        messagebox.showinfo("Dashboard", 
                           "📈 Apertura Dashboard & Report...")
        # TODO: Implementare interfaccia dashboard
    
    # === AZIONI RAPIDE ===
    
    def start_monitoring(self):
        """Avvia il monitoraggio"""
        if not self.monitoring_active:
            try:
                # Avvia jewelry_detector.py in background
                self.detector_process = subprocess.Popen([
                    sys.executable, 'jewelry_detector.py'
                ], cwd=Path.home() / 'jewelry_vision')
                
                self.monitoring_active = True
                messagebox.showinfo("Monitoraggio Avviato", 
                                  "🚨 Sistema di monitoraggio attivo!")
                
            except Exception as e:
                messagebox.showerror("Errore", f"Impossibile avviare monitoraggio: {e}")
        else:
            messagebox.showwarning("Attenzione", "Il monitoraggio è già attivo!")
    
    def stop_monitoring(self):
        """Ferma il monitoraggio"""
        if self.monitoring_active and self.detector_process:
            self.detector_process.terminate()
            self.detector_process = None
            self.monitoring_active = False
            messagebox.showinfo("Monitoraggio Fermato", 
                               "⏹️ Sistema di monitoraggio disattivato!")
        else:
            messagebox.showwarning("Attenzione", "Nessun monitoraggio attivo!")
    
    def open_dashboard(self):
        """Apre dashboard rapida"""
        messagebox.showinfo("Dashboard", "📊 Apertura dashboard rapida...")
        # TODO: Implementare dashboard rapida
    
    def run(self):
        """Avvia l'applicazione"""
        # Centra la finestra
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - self.root.winfo_width()) // 2
        y = (self.root.winfo_screenheight() - self.root.winfo_height()) // 2
        self.root.geometry(f"+{x}+{y}")
        
        # Gestione chiusura applicazione
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Avvia loop principale
        self.root.mainloop()
    
    def on_closing(self):
        """Gestisce la chiusura dell'applicazione"""
        if self.monitoring_active:
            if messagebox.askokcancel("Chiusura", 
                                    "Il monitoraggio è attivo. Vuoi fermarlo e chiudere?"):
                self.stop_monitoring()
                self.root.destroy()
        else:
            self.root.destroy()

if __name__ == "__main__":
    # Verifica che siamo nella directory corretta
    jewelry_vision_dir = Path.home() / 'jewelry_vision'
    if jewelry_vision_dir.exists():
        os.chdir(jewelry_vision_dir)
    
    # Avvia l'applicazione
    app = JewelryVisionGUI()
    app.run()
