#!/usr/bin/env python3
"""
Jewelry Vision Enhanced - Minimal Integration
Usa file enhanced esistenti del sistema
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import sistema base esistente
from jewelry_vision_web import *

# Import enhanced components esistenti
try:
    from multi_target_detection import MultiTargetDetector
    MULTI_TARGET_AVAILABLE = True
except ImportError:
    MULTI_TARGET_AVAILABLE = False

try:
    from scenario_configurator import ScenarioConfigurator  
    SCENARIO_CONFIGURATOR_AVAILABLE = True
except ImportError:
    SCENARIO_CONFIGURATOR_AVAILABLE = False

# Enhanced manager minimale
class EnhancedManager:
    def __init__(self):
        self.enhanced_mode = False
        self.multi_target = None
        self.scenario_config = None
        
    def toggle_enhanced(self):
        self.enhanced_mode = not self.enhanced_mode
        return self.enhanced_mode
        
    def get_status(self):
        return {
            'enhanced_mode': self.enhanced_mode,
            'multi_target_available': MULTI_TARGET_AVAILABLE,
            'scenario_configurator_available': SCENARIO_CONFIGURATOR_AVAILABLE
        }

# Istanza manager
enhanced_manager = EnhancedManager()

# Nuove route enhanced
@app.route('/enhanced_status')
def enhanced_status():
    return jsonify(enhanced_manager.get_status())

@app.route('/toggle_enhanced', methods=['POST'])
def toggle_enhanced():
    result = enhanced_manager.toggle_enhanced()
    return jsonify({
        'status': 'success',
        'enhanced_mode': result
    })

@app.route('/enhanced_panel')
def enhanced_panel():
    return render_template('enhanced_panel.html')

if __name__ == '__main__':
    print("=== JEWELRY VISION ENHANCED MINIMAL ===")
    print(f"Multi-target available: {MULTI_TARGET_AVAILABLE}")
    print(f"Scenario configurator available: {SCENARIO_CONFIGURATOR_AVAILABLE}")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
