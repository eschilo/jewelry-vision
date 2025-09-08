"""
Scenario Configurator - Sistema di configurazione dinamica
Permette di creare e gestire scenari personalizzati
"""

import json
from pathlib import Path
from typing import Dict, List, Any
import logging
from datetime import datetime

class ScenarioConfigurator:
    """
    Configuratore avanzato per scenari di detection
    """
    
    def __init__(self, detection_system):
        self.detection_system = detection_system
        self.logger = logging.getLogger('ScenarioConfigurator')
        
        # Template di scenari pre-configurati
        self.scenario_templates = {
            'jewelry_security': {
                'name': 'Sicurezza Gioielleria',
                'description': 'Monitoraggio completo per gioiellerie con detection persone',
                'targets': ['people'],
                'rules': {
                    'alert_on_person_entry': True,
                    'exclude_staff_hours': '09:00-18:00',
                    'high_confidence_threshold': 0.7
                },
                'database_preferences': {
                    'people': 'ultralytics'
                }
            },
            'people_counting': {
                'name': 'Conteggio Presenze',
                'description': 'Conta il numero di persone presenti nell\'area',
                'targets': ['people'],
                'rules': {
                    'count_entries_exits': True,
                    'max_occupancy': 50,
                    'ignore_staff': False
                },
                'database_preferences': {
                    'people': 'ultralytics'
                }
            },
            'general_security': {
                'name': 'Sicurezza Generale',
                'description': 'Monitoraggio sicurezza generale con detection persone',
                'targets': ['people'],
                'rules': {
                    'immediate_alert': True,
                    'track_movement': True,
                    'after_hours_alert': True
                },
                'database_preferences': {
                    'people': 'ultralytics'
                }
            },
            'advanced_jewelry': {
                'name': 'Gioielleria Avanzata',
                'description': 'Sicurezza gioielleria con detection persone + gioielli (richiede modello custom)',
                'targets': ['people', 'jewelry'],
                'rules': {
                    'alert_on_person_entry': True,
                    'alert_on_jewelry_movement': True,
                    'high_value_threshold': 0.8
                },
                'database_preferences': {
                    'people': 'ultralytics',
                    'jewelry': 'local'
                }
            }
        }
        
        # Database disponibili con caratteristiche
        self.available_databases = {
            'ultralytics': {
                'name': 'Ultralytics Hub',
                'description': 'Modelli pre-addestrati gratuiti (YOLO standard)',
                'supported_targets': ['people', 'vehicles', 'general_objects'],
                'pros': ['Gratuito', 'Veloce', 'Affidabile', 'Pronto all\'uso'],
                'cons': ['Limitato a classi COCO', 'Non personalizzabile'],
                'requires_internet': True,
                'cost': 'Gratuito'
            },
            'local': {
                'name': 'Database Locale',
                'description': 'Modelli custom addestrati localmente',
                'supported_targets': ['jewelry', 'custom_objects', 'faces'],
                'pros': ['Massima personalizzazione', 'Privacy totale', 'Veloce'],
                'cons': ['Richiede training', 'Maintenance manuale'],
                'requires_internet': False,
                'cost': 'Gratuito (dopo training)'
            },
            'roboflow': {
                'name': 'Roboflow Universe',
                'description': 'Database comunitario con modelli specializzati',
                'supported_targets': ['custom', 'specialized'],
                'pros': ['Ampia varietà', 'Modelli specializzati', 'Community'],
                'cons': ['Qualità variabile', 'Alcuni a pagamento'],
                'requires_internet': True,
                'cost': 'Freemium'
            }
        }
        
    def get_scenario_templates(self) -> Dict[str, Any]:
        """Restituisce template scenari disponibili"""
        return self.scenario_templates
    
    def get_database_info(self) -> Dict[str, Any]:
        """Informazioni sui database disponibili"""
        return self.available_databases
    
    def create_custom_scenario(self, config: Dict) -> Dict[str, Any]:
        """Crea scenario personalizzato"""
        try:
            # Validazione configurazione
            validation_result = self._validate_scenario_config(config)
            if not validation_result['valid']:
                return {'success': False, 'errors': validation_result['errors']}
            
            # Crea scenario
            scenario_name = config['name'].lower().replace(' ', '_')
            
            scenario_data = {
                'description': config.get('description', f'Scenario personalizzato: {config["name"]}'),
                'targets': config['targets'],
                'rules': config['rules'],
                'database_preferences': config.get('database_preferences', {})
            }
            
            # Salva configurazione
            self._save_custom_scenario(scenario_name, scenario_data)
            
            # Aggiungi ai template disponibili
            self.scenario_templates[scenario_name] = {
                'name': config['name'],
                'description': scenario_data['description'],
                'targets': scenario_data['targets'],
                'rules': scenario_data['rules'],
                'database_preferences': scenario_data['database_preferences']
            }
            
            return {
                'success': True,
                'scenario_name': scenario_name,
                'message': f'Scenario "{config["name"]}" creato con successo'
            }
            
        except Exception as e:
            self.logger.error(f"Error creating custom scenario: {e}")
            return {'success': False, 'error': str(e)}
    
    def _validate_scenario_config(self, config: Dict) -> Dict[str, Any]:
        """Valida configurazione scenario"""
        errors = []
        
        # Campi obbligatori
        required_fields = ['name', 'targets', 'rules']
        for field in required_fields:
            if field not in config:
                errors.append(f"Campo obbligatorio mancante: {field}")
        
        # Validazione targets
        if 'targets' in config:
            if not isinstance(config['targets'], list) or not config['targets']:
                errors.append("Targets deve essere una lista non vuota")
            
            # Verifica targets supportati
            supported_targets = ['people', 'jewelry', 'faces', 'bags', 'weapons', 'vehicles']
            
            for target in config['targets']:
                if target not in supported_targets:
                    errors.append(f"Target '{target}' non supportato. Supportati: {supported_targets}")
        
        # Validazione regole
        if 'rules' in config:
            if not isinstance(config['rules'], dict):
                errors.append("Rules deve essere un dizionario")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def _save_custom_scenario(self, scenario_name: str, scenario_data: Dict):
        """Salva scenario personalizzato"""
        scenarios_dir = Path('config/custom_scenarios')
        scenarios_dir.mkdir(parents=True, exist_ok=True)
        
        scenario_file = scenarios_dir / f'{scenario_name}.json'
        with open(scenario_file, 'w') as f:
            json.dump(scenario_data, f, indent=2)
    
    def load_custom_scenarios(self) -> Dict[str, Any]:
        """Carica scenari personalizzati salvati"""
        custom_scenarios = {}
        scenarios_dir = Path('config/custom_scenarios')
        
        if scenarios_dir.exists():
            for scenario_file in scenarios_dir.glob('*.json'):
                try:
                    with open(scenario_file, 'r') as f:
                        scenario_data = json.load(f)
                        scenario_name = scenario_file.stem
                        custom_scenarios[scenario_name] = scenario_data
                except Exception as e:
                    self.logger.error(f"Error loading custom scenario {scenario_file}: {e}")
        
        return custom_scenarios
    
    def get_target_configuration_options(self) -> Dict[str, Any]:
        """Opzioni di configurazione per ogni target"""
        return {
            'people': {
                'description': 'Rilevamento persone',
                'configurable_options': [
                    'confidence_threshold', 'tracking_enabled', 'face_blur'
                ],
                'alert_rules': [
                    'immediate_alert', 'counting', 'loitering_detection',
                    'rapid_movement', 'crowding_alert', 'after_hours_alert'
                ],
                'model_info': {
                    'available': True,
                    'source': 'Ultralytics YOLO11n',
                    'classes': 'COCO (80 classi)',
                    'accuracy': 'Alta'
                }
            },
            'jewelry': {
                'description': 'Rilevamento gioielli e oggetti di valore',
                'configurable_options': [
                    'value_estimation', 'material_detection', 'size_estimation'
                ],
                'alert_rules': [
                    'high_value_alert', 'movement_detection', 'removal_alert',
                    'inventory_tracking'
                ],
                'model_info': {
                    'available': False,
                    'source': 'Modello custom (da addestrare)',
                    'classes': 'Ring, Necklace, Bracelet, Watch, Earring, Precious Stone',
                    'accuracy': 'Dipende dal training'
                }
            },
            'faces': {
                'description': 'Riconoscimento facciale',
                'configurable_options': [
                    'recognition_database', 'emotion_detection', 'age_estimation'
                ],
                'alert_rules': [
                    'unknown_face_alert', 'blacklist_match', 'vip_recognition',
                    'access_control'
                ],
                'model_info': {
                    'available': False,
                    'source': 'Modello specializzato (da configurare)',
                    'classes': 'Face detection + recognition',
                    'accuracy': 'Molto alta'
                }
            }
        }
    
    def generate_scenario_recommendations(self, requirements: Dict) -> Dict[str, Any]:
        """Genera raccomandazioni scenario basate su requisiti"""
        try:
            location_type = requirements.get('location', 'general')
            security_level = requirements.get('security_level', 'medium')
            budget = requirements.get('budget', 'medium')
            
            recommendations = []
            
            # Raccomandazioni basate su location
            if location_type == 'jewelry_store':
                if budget == 'low':
                    recommendations.append({
                        'scenario': 'jewelry_security',
                        'confidence': 0.9,
                        'reason': 'Perfetto per gioiellerie con budget limitato - usa solo detection persone'
                    })
                else:
                    recommendations.append({
                        'scenario': 'advanced_jewelry',
                        'confidence': 0.95,
                        'reason': 'Massima sicurezza per gioiellerie - richiede training modello jewelry'
                    })
            
            elif location_type == 'office':
                recommendations.append({
                    'scenario': 'people_counting',
                    'confidence': 0.8,
                    'reason': 'Ideale per uffici - monitora presenze e accessi'
                })
            
            else:  # general
                recommendations.append({
                    'scenario': 'general_security',
                    'confidence': 0.7,
                    'reason': 'Configurazione versatile per uso generale'
                })
            
            return {
                'success': True,
                'recommendations': recommendations,
                'explanation': self._explain_recommendations(requirements)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _explain_recommendations(self, requirements: Dict) -> str:
        """Spiega le raccomandazioni fatte"""
        location = requirements.get('location', 'generale')
        budget = requirements.get('budget', 'medio')
        
        explanation = f"Basato su: Location {location}, Budget {budget}. "
        explanation += "Le raccomandazioni privilegiano soluzioni pronte all'uso con YOLO standard per massima affidabilità."
        
        return explanation
    
    def get_scenario_status(self, scenario_name: str) -> Dict[str, Any]:
        """Stato di un scenario specifico"""
        scenario = self.scenario_templates.get(scenario_name)
        if not scenario:
            return {'exists': False}
        
        # Verifica disponibilità modelli per i target
        models_available = {}
        for target in scenario['targets']:
            if target == 'people':
                models_available[target] = True  # YOLO standard sempre disponibile
            elif target == 'jewelry':
                # Verifica se esiste modello jewelry custom
                jewelry_model_path = Path('models/custom/jewelry_yolo11.pt')
                models_available[target] = jewelry_model_path.exists()
            else:
                models_available[target] = False  # Altri target non ancora implementati
        
        return {
            'exists': True,
            'name': scenario['name'],
            'description': scenario['description'],
            'targets': scenario['targets'],
            'models_available': models_available,
            'ready_to_use': all(models_available.values()),
            'missing_models': [t for t, available in models_available.items() if not available]
        }


class ScenarioWizard:
    """
    Wizard per creare scenari step-by-step
    """
    
    def __init__(self, configurator: ScenarioConfigurator):
        self.configurator = configurator
        self.wizard_steps = [
            'basic_info',
            'location_type', 
            'security_concerns',
            'target_selection',
            'review_and_create'
        ]
        
    def get_wizard_step(self, step_name: str, previous_answers: Dict = None) -> Dict[str, Any]:
        """Restituisce configurazione per step wizard"""
        
        if step_name == 'basic_info':
            return {
                'title': 'Informazioni Base',
                'description': 'Nome e descrizione del scenario',
                'fields': [
                    {'name': 'scenario_name', 'type': 'text', 'required': True, 'label': 'Nome Scenario'},
                    {'name': 'description', 'type': 'textarea', 'required': False, 'label': 'Descrizione'},
                    {'name': 'security_level', 'type': 'select', 'required': True, 'label': 'Livello Sicurezza',
                     'options': ['basic', 'standard', 'high', 'maximum']}
                ]
            }
        
        elif step_name == 'location_type':
            return {
                'title': 'Tipo di Location',
                'description': 'Seleziona il tipo di ambiente da monitorare',
                'fields': [
                    {'name': 'location', 'type': 'select', 'required': True, 'label': 'Tipo Location',
                     'options': ['jewelry_store', 'office', 'retail', 'warehouse', 'home', 'other']},
                    {'name': 'area_size', 'type': 'select', 'label': 'Dimensione Area',
                     'options': ['small', 'medium', 'large']},
                    {'name': 'indoor_outdoor', 'type': 'select', 'label': 'Ambiente',
                     'options': ['indoor', 'outdoor', 'mixed']}
                ]
            }
        
        elif step_name == 'target_selection':
            # Suggerimenti basati su risposte precedenti
            suggested_targets = ['people']  # Sempre suggerito
            if previous_answers and previous_answers.get('location') == 'jewelry_store':
                suggested_targets.append('jewelry')
            
            return {
                'title': 'Selezione Target',
                'description': 'Scegli cosa vuoi rilevare',
                'suggested_targets': suggested_targets,
                'fields': [
                    {'name': 'targets', 'type': 'checkbox_multiple', 'label': 'Targets da Rilevare',
                     'options': [
                         {'value': 'people', 'label': 'Persone', 'available': True, 'recommended': True},
                         {'value': 'jewelry', 'label': 'Gioielli', 'available': False, 'note': 'Richiede modello custom'},
                         {'value': 'faces', 'label': 'Volti', 'available': False, 'note': 'In sviluppo'},
                         {'value': 'bags', 'label': 'Borse', 'available': False, 'note': 'In sviluppo'}
                     ],
                     'suggested': suggested_targets}
                ]
            }
        
        return {'error': 'Step non trovato'}


if __name__ == "__main__":
    print("🔧 Scenario Configurator System - Test")
    
    # Mock detection system per test
    class MockDetectionSystem:
        def __init__(self):
            self.active_scenario = None
    
    # Test configurator
    mock_system = MockDetectionSystem()
    configurator = ScenarioConfigurator(mock_system)
    
    print("✅ Configurator initialized")
    print("📋 Available templates:", list(configurator.get_scenario_templates().keys()))
    print("🗄️ Available databases:", list(configurator.get_database_info().keys()))
    
    # Test status scenarios
    for scenario_name in ['jewelry_security', 'people_counting', 'advanced_jewelry']:
        status = configurator.get_scenario_status(scenario_name)
        print(f"🎭 {scenario_name}: Ready={status.get('ready_to_use', False)}")
    
    print("✅ All tests completed")
