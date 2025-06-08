#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test-Report Generator für RFID & QR Scanner
Erstellt umfassende HTML- und JSON-Reports aus Test-Ergebnissen
"""

import sys
import os
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
import glob

# Projekt-Pfad hinzufügen
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


class TestReportGenerator:
    """Generiert umfassende Test-Reports"""

    def __init__(self):
        self.report_data = {
            'meta': {
                'generated_at': datetime.now().isoformat(),
                'generator_version': '1.0.0',
                'project': 'RFID & QR Scanner System'
            },
            'summary': {},
            'test_categories': {},
            'performance_metrics': {},
            'recommendations': [],
            'system_info': {}
        }

    def collect_test_results(self, logs_dir='logs'):
        """Sammelt alle Test-Ergebnisse aus Log-Dateien"""
        logs_path = Path(logs_dir)

        if not logs_path.exists():
            print(f"⚠️ Logs-Verzeichnis nicht gefunden: {logs_dir}")
            return

        # Sammle verschiedene Report-Dateien
        report_files = {
            'comprehensive': glob.glob(str(logs_path / 'comprehensive_test_report_*.json')),
            'full_test': glob.glob(str(logs_path / 'full_test_report_*.json')),
            'performance': glob.glob(str(logs_path / '*performance*.json')),
            'hardware': glob.glob(str(logs_path / '*hardware*.json')),
        }

        # Lade neueste Reports
        for category, files in report_files.items():
            if files:
                # Neueste Datei
                latest_file = max(files, key=os.path.getmtime)

                try:
                    with open(latest_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        self.report_data['test_categories'][category] = {
                            'file': latest_file,
                            'data': data,
                            'timestamp': datetime.fromtimestamp(os.path.getmtime(latest_file)).isoformat()
                        }
                        print(f"✅ Geladen: {category} ({os.path.basename(latest_file)})")

                except Exception as e:
                    print(f"❌ Fehler beim Laden {latest_file}: {e}")

        # Sammle Log-Dateien
        log_files = glob.glob(str(logs_path / '*.log'))
        self.report_data['log_files'] = [
            {
                'name': os.path.basename(f),
                'path': f,
                'size': os.path.getsize(f),
                'modified': datetime.fromtimestamp(os.path.getmtime(f)).isoformat()
            }
            for f in log_files
        ]

    def analyze_results(self):
        """Analysiert die gesammelten Test-Ergebnisse"""
        total_tests = 0
        total_failures = 0
        total_errors = 0
        total_time = 0

        category_results = {}

        # Analysiere jede Test-Kategorie
        for category, info in self.report_data['test_categories'].items():
            data = info['data']

            # Extrahiere relevante Metriken
            if 'summary' in data:
                summary = data['summary']
                cat_tests = summary.get('total_tests', 0)
                cat_failures = summary.get('failed_tests', 0)
                cat_errors = summary.get('errors', 0)

                total_tests += cat_tests
                total_failures += cat_failures
                total_errors += cat_errors

                category_results[category] = {
                    'tests': cat_tests,
                    'failures': cat_failures,
                    'errors': cat_errors,
                    'success_rate': summary.get('success_rate', 0),
                    'timestamp': info['timestamp']
                }

            elif 'test_results' in data:
                # Alternative Struktur
                test_results = data['test_results']
                cat_tests = len(test_results)
                cat_failures = sum(1 for r in test_results.values() if not r)

                total_tests += cat_tests
                total_failures += cat_failures

                category_results[category] = {
                    'tests': cat_tests,
                    'failures': cat_failures,
                    'errors': 0,
                    'success_rate': (cat_tests - cat_failures) / cat_tests if cat_tests > 0 else 0,
                    'timestamp': info['timestamp']
                }

            # Performance-Metriken extrahieren
            if 'performance_metrics' in data:
                self.report_data['performance_metrics'][category] = data['performance_metrics']

        # Gesamt-Summary
        overall_success_rate = (total_tests - total_failures - total_errors) / total_tests if total_tests > 0 else 0

        self.report_data['summary'] = {
            'total_tests': total_tests,
            'total_failures': total_failures,
            'total_errors': total_errors,
            'overall_success_rate': overall_success_rate,
            'category_results': category_results,
            'categories_tested': len(category_results)
        }

    def generate_recommendations(self):
        """Generiert Empfehlungen basierend auf Test-Ergebnissen"""
        summary = self.report_data['summary']
        success_rate = summary.get('overall_success_rate', 0)

        recommendations = []

        # Allgemeine Empfehlungen basierend auf Erfolgsrate
        if success_rate >= 0.95:
            recommendations.append({
                'type': 'success',
                'priority': 'low',
                'title': 'Exzellente Test-Ergebnisse',
                'description': 'Das System zeigt hervorragende Stabilität und Funktionalität.',
                'actions': [
                    'System ist produktionsreif',
                    'Regelmäßige Überwachung einrichten',
                    'Performance-Optimierungen erwägen'
                ]
            })
        elif success_rate >= 0.8:
            recommendations.append({
                'type': 'warning',
                'priority': 'medium',
                'title': 'Gute Ergebnisse mit kleineren Problemen',
                'description': 'Das System funktioniert gut, aber einige Bereiche benötigen Aufmerksamkeit.',
                'actions': [
                    'Fehlgeschlagene Tests analysieren',
                    'Problembereiche beheben',
                    'Zusätzliche Tests durchführen'
                ]
            })
        elif success_rate >= 0.6:
            recommendations.append({
                'type': 'error',
                'priority': 'high',
                'title': 'Erhebliche Probleme festgestellt',
                'description': 'Das System hat mehrere kritische Probleme die behoben werden müssen.',
                'actions': [
                    'Umfassende Fehleranalyse durchführen',
                    'Kritische Komponenten überprüfen',
                    'Hardware-Verbindungen prüfen',
                    'Konfiguration validieren'
                ]
            })
        else:
            recommendations.append({
                'type': 'critical',
                'priority': 'critical',
                'title': 'Schwerwiegende System-Probleme',
                'description': 'Das System ist nicht funktionsfähig und benötigt umfassende Reparaturen.',
                'actions': [
                    'System nicht in Produktion einsetzen',
                    'Grundlegende System-Diagnose durchführen',
                    'Hardware-Setup überprüfen',
                    'Support kontaktieren'
                ]
            })

        # Kategorie-spezifische Empfehlungen
        category_results = summary.get('category_results', {})

        for category, results in category_results.items():
            if results['success_rate'] < 0.7:
                recommendations.append({
                    'type': 'category_issue',
                    'priority': 'high',
                    'title': f'Probleme in {category.title()}-Tests',
                    'description': f'Die {category}-Tests zeigen eine niedrige Erfolgsrate von {results["success_rate"]:.1%}.',
                    'actions': [
                        f'{category.title()}-Komponenten überprüfen',
                        f'Spezielle {category}-Diagnose durchführen',
                        f'Log-Dateien für {category} analysieren'
                    ]
                })

        # Performance-basierte Empfehlungen
        if 'performance' in self.report_data['performance_metrics']:
            perf_data = self.report_data['performance_metrics']['performance']

            # Beispiel-Analyse (würde je nach verfügbaren Daten angepasst)
            if isinstance(perf_data, dict):
                for metric_name, metric_value in perf_data.items():
                    if 'time' in metric_name.lower() and isinstance(metric_value, (int, float)):
                        if metric_value > 1000:  # > 1 Sekunde
                            recommendations.append({
                                'type': 'performance',
                                'priority': 'medium',
                                'title': f'Langsame {metric_name}',
                                'description': f'{metric_name} dauert {metric_value:.1f}ms, was relativ langsam ist.',
                                'actions': [
                                    'Performance-Optimierung erwägen',
                                    'System-Ressourcen überprüfen',
                                    'Hardware-Upgrade evaluieren'
                                ]
                            })

        self.report_data['recommendations'] = recommendations

    def collect_system_info(self):
        """Sammelt System-Informationen"""
        try:
            import platform
            import psutil

            # Basis-System-Info
            system_info = {
                'platform': platform.system(),
                'platform_version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'python_version': platform.python_version(),
            }

            # Hardware-Info (falls psutil verfügbar)
            try:
                system_info.update({
                    'cpu_count': psutil.cpu_count(),
                    'memory_total_gb': round(psutil.virtual_memory().total / (1024 ** 3), 2),
                    'disk_total_gb': round(psutil.disk_usage('/').total / (1024 ** 3), 2),
                })
            except:
                pass

            # Projekt-spezifische Info
            try:
                from config import DB_CONFIG, APP_CONFIG

                system_info.update({
                    'database_server': DB_CONFIG.get('server', 'Unknown'),
                    'database_name': DB_CONFIG.get('database', 'Unknown'),
                    'camera_indices': APP_CONFIG.get('CAMERA_INDICES', []),
                    'max_scanners': APP_CONFIG.get('MAX_SCANNERS', 'Unknown'),
                })
            except:
                pass

            self.report_data['system_info'] = system_info

        except ImportError:
            self.report_data['system_info'] = {
                'platform': 'Unknown',
                'note': 'System-Info-Module nicht verfügbar'
            }

    def generate_html_report(self, output_file='test_report.html'):
        """Generiert HTML-Report"""

        html_content = f"""
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RFID & QR Scanner - Test-Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}

        .header .meta {{
            opacity: 0.9;
            font-size: 1.1em;
        }}

        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}

        .summary-card {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }}

        .summary-card h3 {{
            color: #666;
            margin-bottom: 10px;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .summary-card .value {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 10px;
        }}

        .success {{ color: #27ae60; }}
        .warning {{ color: #f39c12; }}
        .error {{ color: #e74c3c; }}
        .info {{ color: #3498db; }}

        .section {{
            background: white;
            margin-bottom: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
        }}

        .section-header {{
            background: #f8f9fa;
            padding: 20px;
            border-bottom: 1px solid #dee2e6;
        }}

        .section-header h2 {{
            color: #495057;
            margin: 0;
        }}

        .section-content {{
            padding: 25px;
        }}

        .category-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }}

        .category-card {{
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 20px;
        }}

        .category-title {{
            font-weight: bold;
            margin-bottom: 15px;
            font-size: 1.2em;
        }}

        .progress-bar {{
            background: #f1f1f1;
            border-radius: 10px;
            height: 20px;
            margin: 10px 0;
            overflow: hidden;
        }}

        .progress-fill {{
            height: 100%;
            border-radius: 10px;
            transition: width 0.3s ease;
        }}

        .recommendation {{
            border-left: 4px solid;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 0 5px 5px 0;
        }}

        .recommendation.success {{ border-color: #27ae60; background: #d5f4e6; }}
        .recommendation.warning {{ border-color: #f39c12; background: #fef5e7; }}
        .recommendation.error {{ border-color: #e74c3c; background: #fdeaea; }}
        .recommendation.critical {{ border-color: #c0392b; background: #f8d7da; }}

        .recommendation h4 {{
            margin-bottom: 10px;
        }}

        .recommendation ul {{
            margin-left: 20px;
        }}

        .stats-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}

        .stats-table th,
        .stats-table td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }}

        .stats-table th {{
            background: #f8f9fa;
            font-weight: 600;
        }}

        .footer {{
            text-align: center;
            padding: 30px;
            color: #666;
            border-top: 1px solid #dee2e6;
            margin-top: 50px;
        }}

        @media (max-width: 768px) {{
            .container {{
                padding: 10px;
            }}

            .header h1 {{
                font-size: 2em;
            }}

            .summary {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔧 RFID & QR Scanner Test-Report</h1>
            <div class="meta">
                Generiert am: {datetime.now().strftime('%d.%m.%Y um %H:%M:%S')}<br>
                System: {self.report_data['system_info'].get('platform', 'Unknown')} | 
                Python: {self.report_data['system_info'].get('python_version', 'Unknown')}
            </div>
        </div>

        <div class="summary">
            <div class="summary-card">
                <h3>Gesamt-Tests</h3>
                <div class="value info">{self.report_data['summary'].get('total_tests', 0)}</div>
            </div>
            <div class="summary-card">
                <h3>Erfolgsrate</h3>
                <div class="value {self._get_status_class(self.report_data['summary'].get('overall_success_rate', 0))}">{self.report_data['summary'].get('overall_success_rate', 0):.1%}</div>
            </div>
            <div class="summary-card">
                <h3>Fehlschläge</h3>
                <div class="value error">{self.report_data['summary'].get('total_failures', 0)}</div>
            </div>
            <div class="summary-card">
                <h3>Test-Kategorien</h3>
                <div class="value info">{self.report_data['summary'].get('categories_tested', 0)}</div>
            </div>
        </div>

        <div class="section">
            <div class="section-header">
                <h2>📊 Test-Kategorien Übersicht</h2>
            </div>
            <div class="section-content">
                <div class="category-grid">
                    {self._generate_category_cards()}
                </div>
            </div>
        </div>

        <div class="section">
            <div class="section-header">
                <h2>💡 Empfehlungen</h2>
            </div>
            <div class="section-content">
                {self._generate_recommendations_html()}
            </div>
        </div>

        <div class="section">
            <div class="section-header">
                <h2>🖥️ System-Informationen</h2>
            </div>
            <div class="section-content">
                {self._generate_system_info_html()}
            </div>
        </div>

        <div class="section">
            <div class="section-header">
                <h2>📄 Log-Dateien</h2>
            </div>
            <div class="section-content">
                {self._generate_log_files_html()}
            </div>
        </div>

        <div class="footer">
            <p>RFID & QR Scanner System Test-Report | Generiert von TestReportGenerator v1.0.0</p>
        </div>
    </div>
</body>
</html>
"""

        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"📄 HTML-Report erstellt: {output_file}")

        except Exception as e:
            print(f"❌ Fehler beim Erstellen des HTML-Reports: {e}")

    def _get_status_class(self, success_rate):
        """Gibt CSS-Klasse basierend auf Erfolgsrate zurück"""
        if success_rate >= 0.9:
            return 'success'
        elif success_rate >= 0.7:
            return 'warning'
        else:
            return 'error'

    def _generate_category_cards(self):
        """Generiert HTML für Kategorie-Karten"""
        cards_html = ""

        for category, results in self.report_data['summary'].get('category_results', {}).items():
            success_rate = results['success_rate']
            status_class = self._get_status_class(success_rate)

            cards_html += f"""
            <div class="category-card">
                <div class="category-title">{category.title()}</div>
                <div class="progress-bar">
                    <div class="progress-fill {status_class}" style="width: {success_rate * 100}%"></div>
                </div>
                <div style="margin-top: 10px;">
                    <strong>{success_rate:.1%}</strong> Erfolgsrate<br>
                    {results['tests']} Tests, {results['failures']} Fehlschläge
                </div>
            </div>
            """

        return cards_html if cards_html else "<p>Keine Test-Kategorien verfügbar</p>"

    def _generate_recommendations_html(self):
        """Generiert HTML für Empfehlungen"""
        recommendations_html = ""

        for rec in self.report_data['recommendations']:
            rec_type = rec.get('type', 'info')

            actions_html = ""
            for action in rec.get('actions', []):
                actions_html += f"<li>{action}</li>"

            recommendations_html += f"""
            <div class="recommendation {rec_type}">
                <h4>{rec.get('title', 'Empfehlung')}</h4>
                <p>{rec.get('description', '')}</p>
                {f'<ul>{actions_html}</ul>' if actions_html else ''}
            </div>
            """

        return recommendations_html if recommendations_html else "<p>Keine spezifischen Empfehlungen verfügbar</p>"

    def _generate_system_info_html(self):
        """Generiert HTML für System-Informationen"""
        system_info = self.report_data.get('system_info', {})

        info_html = "<table class='stats-table'>"

        for key, value in system_info.items():
            if isinstance(value, list):
                value = ', '.join(map(str, value))
            info_html += f"<tr><th>{key.replace('_', ' ').title()}</th><td>{value}</td></tr>"

        info_html += "</table>"

        return info_html

    def _generate_log_files_html(self):
        """Generiert HTML für Log-Dateien"""
        log_files = self.report_data.get('log_files', [])

        if not log_files:
            return "<p>Keine Log-Dateien gefunden</p>"

        files_html = "<table class='stats-table'>"
        files_html += "<tr><th>Datei</th><th>Größe</th><th>Zuletzt geändert</th></tr>"

        for log_file in log_files:
            size_kb = log_file['size'] / 1024
            modified = datetime.fromisoformat(log_file['modified']).strftime('%d.%m.%Y %H:%M')

            files_html += f"""
            <tr>
                <td>{log_file['name']}</td>
                <td>{size_kb:.1f} KB</td>
                <td>{modified}</td>
            </tr>
            """

        files_html += "</table>"

        return files_html

    def generate_json_report(self, output_file='test_report.json'):
        """Generiert JSON-Report"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.report_data, f, indent=2, ensure_ascii=False, default=str)
            print(f"📄 JSON-Report erstellt: {output_file}")

        except Exception as e:
            print(f"❌ Fehler beim Erstellen des JSON-Reports: {e}")

    def generate_complete_report(self, base_name='complete_test_report'):
        """Generiert sowohl HTML- als auch JSON-Report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Sammle alle Daten
        print("📊 Sammle Test-Ergebnisse...")
        self.collect_test_results()

        print("🔍 Analysiere Ergebnisse...")
        self.analyze_results()

        print("💡 Generiere Empfehlungen...")
        self.generate_recommendations()

        print("🖥️ Sammle System-Informationen...")
        self.collect_system_info()

        # Erstelle Reports
        html_file = f"{base_name}_{timestamp}.html"
        json_file = f"{base_name}_{timestamp}.json"

        print("📄 Erstelle Reports...")
        self.generate_html_report(html_file)
        self.generate_json_report(json_file)

        # Summary ausgeben
        summary = self.report_data['summary']

        print("\n" + "=" * 60)
        print("📊 TEST-REPORT ZUSAMMENFASSUNG")
        print("=" * 60)
        print(f"📈 Gesamt-Tests: {summary.get('total_tests', 0)}")
        print(f"✅ Erfolgsrate: {summary.get('overall_success_rate', 0):.1%}")
        print(f"❌ Fehlschläge: {summary.get('total_failures', 0)}")
        print(f"💥 Fehler: {summary.get('total_errors', 0)}")
        print(f"📁 Kategorien: {summary.get('categories_tested', 0)}")
        print(f"💡 Empfehlungen: {len(self.report_data['recommendations'])}")
        print()
        print(f"📄 HTML-Report: {html_file}")
        print(f"📄 JSON-Report: {json_file}")
        print("=" * 60)

        return html_file, json_file


def main():
    """Hauptfunktion"""
    import argparse

    parser = argparse.ArgumentParser(description='Test-Report Generator für RFID & QR Scanner')
    parser.add_argument('--logs-dir', default='logs', help='Verzeichnis mit Log-Dateien')
    parser.add_argument('--output', default='complete_test_report', help='Basis-Name für Output-Dateien')
    parser.add_argument('--format', choices=['html', 'json', 'both'], default='both', help='Report-Format')

    args = parser.parse_args()

    print("📊 Test-Report Generator")
    print("=" * 40)

    generator = TestReportGenerator()

    if args.format == 'both':
        html_file, json_file = generator.generate_complete_report(args.output)

    elif args.format == 'html':
        generator.collect_test_results(args.logs_dir)
        generator.analyze_results()
        generator.generate_recommendations()
        generator.collect_system_info()

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        html_file = f"{args.output}_{timestamp}.html"
        generator.generate_html_report(html_file)

    elif args.format == 'json':
        generator.collect_test_results(args.logs_dir)
        generator.analyze_results()
        generator.generate_recommendations()
        generator.collect_system_info()

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        json_file = f"{args.output}_{timestamp}.json"
        generator.generate_json_report(json_file)


if __name__ == '__main__':
    main()