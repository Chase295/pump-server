"""
Alert-Evaluator Background Service
Wertet regelmäßig ausstehende Alerts aus
"""
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any
from app.database.alert_models import evaluate_pending_alerts
from app.database.ath_tracker import evaluate_pending_alerts_ath
from app.utils.logging_config import get_logger

logger = get_logger(__name__)


class AlertEvaluator:
    """Background-Service für Alert-Auswertung"""
    
    def __init__(self, interval_seconds: int = 30):
        """
        Args:
            interval_seconds: Intervall zwischen Auswertungs-Durchläufen (Standard: 30 Sekunden)
        """
        self.interval_seconds = interval_seconds
        self.running = False
        self.last_run: datetime | None = None
        self.stats: Dict[str, int] = {'total_evaluated': 0, 'total_success': 0, 'total_failed': 0, 'total_expired': 0}
    
    async def run_once(self) -> Dict[str, int]:
        """Führt eine einzelne Auswertungs-Runde durch"""
        try:
            logger.debug("🔄 Starte Alert-Auswertung...")
            
            # 1. ATH-Tracking: Prüfe alle pending/non_alert Alerts und aktualisiere ATH
            ath_stats = await evaluate_pending_alerts_ath(batch_size=100)
            if ath_stats.get('checked', 0) > 0:
                logger.debug(
                    f"📊 ATH-Tracking: {ath_stats.get('checked', 0)} geprüft, "
                    f"{ath_stats.get('ath_updated', 0)} ATH aktualisiert, "
                    f"{ath_stats.get('goal_reached', 0)} Ziel erreicht (aber noch nicht final evaluiert)"
                )
            
            # 2. Finale Evaluierung: Nur für Alerts, deren evaluation_timestamp erreicht wurde
            stats = await evaluate_pending_alerts(batch_size=100, include_non_alerts=True)
            
            # Update Gesamt-Statistiken
            self.stats['total_evaluated'] += stats.get('evaluated', 0)
            self.stats['total_success'] += stats.get('success', 0)
            self.stats['total_failed'] += stats.get('failed', 0)
            self.stats['total_expired'] += stats.get('expired', 0)
            
            if stats.get('evaluated', 0) > 0:
                logger.info(
                    f"✅ Alert-Auswertung abgeschlossen: "
                    f"{stats.get('evaluated', 0)} ausgewertet "
                    f"({stats.get('success', 0)} erfolgreich, "
                    f"{stats.get('failed', 0)} fehlgeschlagen, "
                    f"{stats.get('expired', 0)} abgelaufen)"
                )
            
            self.last_run = datetime.now(timezone.utc)
            return stats
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Alert-Auswertung: {e}", exc_info=True)
            return {'evaluated': 0, 'success': 0, 'failed': 0, 'expired': 0}
    
    async def start(self):
        """Startet den Alert-Evaluator als Background-Service"""
        self.running = True
        logger.info(f"🚀 Alert-Evaluator gestartet (Intervall: {self.interval_seconds}s)")
        
        # Warte kurz, damit die DB-Verbindung bereit ist
        await asyncio.sleep(5)
        
        while self.running:
            try:
                await self.run_once()
            except Exception as e:
                logger.error(f"❌ Fehler im Alert-Evaluator Loop: {e}", exc_info=True)
            
            # Warte auf nächstes Intervall
            await asyncio.sleep(self.interval_seconds)
    
    async def stop(self):
        """Stoppt den Alert-Evaluator"""
        self.running = False
        logger.info("🛑 Alert-Evaluator gestoppt")
    
    def get_stats(self) -> Dict[str, Any]:
        """Gibt aktuelle Statistiken zurück"""
        return {
            **self.stats,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'interval_seconds': self.interval_seconds,
            'running': self.running
        }


# Globale Instanz
_alert_evaluator: AlertEvaluator | None = None


async def start_alert_evaluator(interval_seconds: int = 30):
    """Startet den Alert-Evaluator als Background-Task"""
    global _alert_evaluator
    
    if _alert_evaluator is None:
        _alert_evaluator = AlertEvaluator(interval_seconds=interval_seconds)
        # Starte als Background-Task (blockiert nicht)
        asyncio.create_task(_alert_evaluator.start())
        logger.info("✅ Alert-Evaluator Background-Task gestartet")
    else:
        logger.warning("⚠️ Alert-Evaluator läuft bereits")


async def stop_alert_evaluator():
    """Stoppt den Alert-Evaluator"""
    global _alert_evaluator
    
    if _alert_evaluator:
        await _alert_evaluator.stop()
        _alert_evaluator = None
        logger.info("✅ Alert-Evaluator gestoppt")


async def main():
    """Main entry point für direkten Start (z.B. als separater Service)"""
    evaluator = AlertEvaluator(interval_seconds=30)
    try:
        await evaluator.start()
    except KeyboardInterrupt:
        logger.info("🛑 Alert-Evaluator wird beendet...")
        await evaluator.stop()


if __name__ == "__main__":
    asyncio.run(main())
