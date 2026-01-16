#!/usr/bin/env python3
"""
ML Training Service - Monitoring & Alerting System
Kontinuierliche Überwachung der API und Job-Verarbeitung
"""

import time
import requests
import logging
from datetime import datetime, timezone
import json
import sys

# Konfiguration
API_BASE_URL = "https://test.local.chase295.de"
CHECK_INTERVAL = 300  # 5 Minuten
LOG_FILE = "monitoring.log"

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class MonitoringSystem:
    def __init__(self, api_base_url: str):
        self.api_base_url = api_base_url
        self.last_alert_time = {}
        self.alert_cooldown = 1800  # 30 Minuten Cooldown zwischen gleichen Alerts

    def check_api_health(self):
        """Prüft grundlegende API-Verfügbarkeit"""
        try:
            response = requests.get(f"{self.api_base_url}/api/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    'status': 'healthy' if data.get('db_connected') else 'degraded',
                    'db_connected': data.get('db_connected', False),
                    'uptime': data.get('uptime_seconds', 0)
                }
            else:
                return {'status': 'unhealthy', 'error': f'HTTP {response.status_code}'}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}

    def check_job_queue(self):
        """Analysiert Job-Queue-Status"""
        try:
            response = requests.get(f"{self.api_base_url}/api/queue", timeout=30)
            if response.status_code == 200:
                jobs = response.json()
                total_jobs = len(jobs)

                stats = {
                    'total': total_jobs,
                    'pending': len([j for j in jobs if j['status'] == 'PENDING']),
                    'running': len([j for j in jobs if j['status'] == 'RUNNING']),
                    'completed': len([j for j in jobs if j['status'] == 'COMPLETED']),
                    'failed': len([j for j in jobs if j['status'] == 'FAILED'])
                }

                # Berechne Erfolgsrate
                if stats['total'] > 0:
                    stats['success_rate'] = round((stats['completed'] / stats['total']) * 100, 1)
                else:
                    stats['success_rate'] = 100.0

                return stats
            else:
                return {'error': f'HTTP {response.status_code}'}
        except Exception as e:
            return {'error': str(e)}

    def check_recent_failures(self):
        """Prüft kürzlich gescheiterte Jobs"""
        try:
            response = requests.get(f"{self.api_base_url}/api/queue?status=FAILED", timeout=30)
            if response.status_code == 200:
                failed_jobs = response.json()
                recent_failures = []

                for job in failed_jobs[-5:]:  # Letzte 5 gescheiterte Jobs
                    try:
                        created_at = datetime.fromisoformat(job.get('created_at', '').replace('Z', '+00:00'))
                        age_hours = (datetime.now(timezone.utc) - created_at).total_seconds() / 3600

                        if age_hours < 24:  # Nur Jobs der letzten 24 Stunden
                            recent_failures.append({
                                'id': job.get('id'),
                                'error_msg': job.get('error_msg', 'Unknown error'),
                                'age_hours': round(age_hours, 1)
                            })
                    except:
                        pass

                return recent_failures
            else:
                return []
        except Exception as e:
            logger.error(f"Fehler beim Prüfen gescheiterter Jobs: {e}")
            return []

    def send_alert(self, alert_type: str, message: str, level: str = 'WARNING'):
        """Sendet Alert (hier nur Logging, kann erweitert werden für Slack/Webhook/etc.)"""
        # Cooldown-Check
        now = time.time()
        if alert_type in self.last_alert_time:
            if now - self.last_alert_time[alert_type] < self.alert_cooldown:
                return  # Alert noch im Cooldown

        self.last_alert_time[alert_type] = now

        # Alert formatieren
        alert_msg = f"🚨 ALERT [{level}] {alert_type}: {message}"

        # Logging
        if level == 'ERROR':
            logger.error(alert_msg)
        elif level == 'WARNING':
            logger.warning(alert_msg)
        else:
            logger.info(alert_msg)

        # Hier können weitere Alert-Systeme integriert werden:
        # - Slack Webhook
        # - Email
        # - PagerDuty
        # - etc.

    def perform_health_check(self):
        """Führt vollständige Health-Check durch"""
        logger.info("🔍 Starte Health-Check...")

        # API Health prüfen
        health = self.check_api_health()
        if health['status'] == 'error':
            self.send_alert('API_UNAVAILABLE', f"API ist nicht erreichbar: {health['error']}", 'ERROR')
            return False
        elif health['status'] == 'unhealthy':
            self.send_alert('API_DEGRADED', "API ist verfügbar aber DB nicht verbunden", 'WARNING')

        # Job Queue analysieren
        job_queue_stats = self.check_job_queue()
        if 'error' in job_queue_stats:
            self.send_alert('JOB_QUEUE_ERROR', f"Job-Queue nicht verfügbar: {job_queue_stats['error']}", 'ERROR')
            return False

        # Job-Statistiken prüfen
        if job_queue_stats['failed'] > 0:
            self.send_alert('FAILED_JOBS', f"{job_queue_stats['failed']} von {job_queue_stats['total']} Jobs sind FAILED", 'ERROR')

        if job_queue_stats['pending'] > 10:
            self.send_alert('QUEUE_BACKLOG', f"{job_queue_stats['pending']} Jobs warten in der Queue", 'WARNING')

        if job_queue_stats['running'] > 3:
            logger.info(f"📊 {job_queue_stats['running']} Jobs werden parallel verarbeitet")

        # Erfolgsrate prüfen
        if job_queue_stats['success_rate'] < 50.0 and job_queue_stats['total'] > 5:
            self.send_alert('LOW_SUCCESS_RATE', f"Erfolgsrate nur {job_queue_stats['success_rate']}% bei {job_queue_stats['total']} Jobs", 'WARNING')

        # Kürzliche Fehler analysieren
        recent_failures = self.check_recent_failures()
        if len(recent_failures) > 0:
            error_summary = "; ".join([f"Job {f['id']}: {f['error_msg'][:50]}..." for f in recent_failures[:3]])
            self.send_alert('RECENT_FAILURES', f"Kürzliche Fehler: {error_summary}", 'WARNING')

        # Erfolgreicher Check
        logger.info(f"✅ Health-Check erfolgreich: {job_queue_stats['completed']} completed, {job_queue_stats['running']} running, {job_queue_stats['pending']} pending")
        return True

    def generate_report(self):
        """Generiert täglichen Report"""
        try:
            job_queue_stats = self.check_job_queue()
            health = self.check_api_health()

            report = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'period': 'daily',
                'metrics': {
                    'jobs': job_queue_stats,
                    'api_health': health
                }
            }

            # Report in Datei speichern
            with open('daily_report.json', 'w') as f:
                json.dump(report, f, indent=2)

            logger.info("📊 Täglicher Report generiert: daily_report.json")

        except Exception as e:
            logger.error(f"Fehler beim Generieren des Reports: {e}")

    def run_monitoring_loop(self):
        """Haupt-Monitoring-Loop"""
        logger.info("🚀 Starte Monitoring-System...")
        logger.info(f"📊 Check-Intervall: {CHECK_INTERVAL} Sekunden")
        logger.info(f"📁 Log-Datei: {LOG_FILE}")

        check_count = 0

        while True:
            try:
                self.perform_health_check()
                check_count += 1

                # Täglichen Report generieren (alle 24h / 288 Checks)
                if check_count % 288 == 0:
                    self.generate_report()

            except Exception as e:
                logger.error(f"❌ Fehler im Monitoring-Loop: {e}")

            time.sleep(CHECK_INTERVAL)


def main():
    """Hauptfunktion"""
    if len(sys.argv) > 1 and sys.argv[1] == '--report':
        # Einzelner Report
        monitor = MonitoringSystem(API_BASE_URL)
        monitor.generate_report()
        print("📊 Report generiert: daily_report.json")
        return

    # Kontinuierliches Monitoring
    monitor = MonitoringSystem(API_BASE_URL)

    try:
        monitor.run_monitoring_loop()
    except KeyboardInterrupt:
        logger.info("👋 Monitoring beendet durch Benutzer")
    except Exception as e:
        logger.error(f"❌ Kritischer Fehler im Monitoring-System: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
