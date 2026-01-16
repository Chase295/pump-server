"""
Pydantic Schemas für ML Training Service API
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, validator, Field

# ============================================================
# Request Schemas
# ============================================================

class SimpleTrainModelRequest(BaseModel):
    """Vereinfachte Request für regelbasierte Modell-Training (einfacher als TrainModelRequest)"""
    name: str = Field(..., description="Modell-Name (eindeutig)")
    model_type: str = Field(..., description="Modell-Typ: 'random_forest' oder 'xgboost'")
    target: str = Field(..., description="Ziel-Regel (z.B. 'price_close > 0.05' oder 'market_cap_close >= 0.1')")
    features: List[str] = Field(..., description="Liste der Feature-Namen (oder 'auto' für alle verfügbaren)")
    train_start: datetime = Field(..., description="Start-Zeitpunkt (ISO-Format mit UTC)")
    train_end: datetime = Field(..., description="Ende-Zeitpunkt (ISO-Format mit UTC)")
    description: Optional[str] = Field(None, description="Beschreibung des Modells")

    # Optionale erweiterte Parameter
    hyperparameters: Optional[Dict[str, Any]] = Field(None, description="Hyperparameter (überschreibt Defaults)")
    validation_split: Optional[float] = Field(0.2, description="Validierungs-Split (0.1-0.5)")

    @validator('model_type', allow_reuse=True)
    def validate_model_type(cls, v):
        """Validiert dass nur random_forest oder xgboost erlaubt sind"""
        allowed = ['random_forest', 'xgboost']
        if v not in allowed:
            raise ValueError(f'model_type muss einer von {allowed} sein')
        return v

    @validator('target')
    def validate_target(cls, v):
        """Validiert und parsed die Ziel-Regel (z.B. 'price_close > 0.05')"""
        if not isinstance(v, str):
            raise ValueError('target muss ein String sein (z.B. "price_close > 0.05")')

        # Parse die Regel (vereinfacht)
        parts = v.split()
        if len(parts) != 3:
            raise ValueError('target muss Format "variable operator value" haben (z.B. "price_close > 0.05")')

        var, op, val_str = parts

        # Validiere Operator
        allowed_ops = ['>', '<', '>=', '<=', '=']
        if op not in allowed_ops:
            raise ValueError(f'Operator muss einer von {allowed_ops} sein')

        # Validiere Variable (vereinfacht)
        allowed_vars = ['price_close', 'price_open', 'price_high', 'price_low', 'market_cap_close', 'volume_sol']
        if var not in allowed_vars:
            raise ValueError(f'Variable muss einer von {allowed_vars} sein')

        # Validiere Wert
        try:
            float(val_str)
        except ValueError:
            raise ValueError(f'Wert muss eine Zahl sein (du hast "{val_str}" verwendet)')

        return v

    @validator('features')
    def validate_features(cls, v):
        """Validiert Features - erlaubt 'auto' als Spezialwert"""
        if isinstance(v, str) and v.lower() == 'auto':
            # 'auto' wird in der API zu allen verfügbaren Features aufgelöst
            return ['auto']  # Wird später in der API zu allen Features erweitert
        elif isinstance(v, list):
            return v
        else:
            raise ValueError('features muss eine Liste von Strings oder "auto" sein')


class TrainModelRequest(BaseModel):
    """Request für Modell-Training"""
    name: str = Field(..., description="Modell-Name (eindeutig)")
    model_type: str = Field(..., description="Modell-Typ: 'random_forest' oder 'xgboost'")
    features: List[str] = Field(..., description="Liste der Feature-Namen")
    phases: Optional[List[int]] = Field(None, description="Liste der Coin-Phasen (z.B. [1, 2, 3])")
    params: Optional[Dict[str, Any]] = Field(None, description="Hyperparameter (optional, überschreibt Defaults)")
    train_start: datetime = Field(..., description="Start-Zeitpunkt (ISO-Format mit UTC)")
    train_end: datetime = Field(..., description="Ende-Zeitpunkt (ISO-Format mit UTC)")
    description: Optional[str] = Field(None, description="Beschreibung des Modells")
    
    # NEU: Zeitbasierte Vorhersagen (ZUERST, damit Validatoren darauf zugreifen können)
    use_time_based_prediction: bool = Field(False, description="Zeitbasierte Vorhersage aktivieren")
    future_minutes: Optional[int] = Field(None, description="Anzahl Minuten in die Zukunft (z.B. 10)")
    min_percent_change: Optional[float] = Field(None, description="Mindest-Prozent-Änderung (z.B. 5.0 für 5%)")
    direction: Optional[str] = Field("up", description="Richtung: 'up' (steigt) oder 'down' (fällt)")
    
    # NEU: Feature-Engineering
    use_engineered_features: bool = Field(False, description="Erweiterte Pump-Detection Features verwenden")
    feature_engineering_windows: Optional[List[int]] = Field(None, description="Fenstergrößen für Feature-Engineering (z.B. [5, 10, 15])")
    
    # NEU: SMOTE
    use_smote: bool = Field(True, description="SMOTE für Imbalanced Data Handling verwenden")
    
    # NEU: TimeSeriesSplit
    use_timeseries_split: bool = Field(True, description="TimeSeriesSplit für Cross-Validation verwenden (empfohlen für Zeitreihen)")
    cv_splits: Optional[int] = Field(5, description="Anzahl Splits für Cross-Validation (Standard: 5)")
    
    # NEU: Marktstimmung (Phase 2)
    use_market_context: bool = Field(False, description="Marktstimmung (SOL-Preis, etc.) für Training verwenden")
    
    # NEU: Feature-Ausschluss (Phase 2)
    exclude_features: Optional[List[str]] = Field(None, description="Liste von Features die ausgeschlossen werden sollen (z.B. ['dev_sold_amount'])")
    
    # Ziel-Variablen: Optional wenn zeitbasierte Vorhersage aktiviert (NACH use_time_based_prediction)
    target_var: Optional[str] = Field(None, description="Ziel-Variable (z.B. 'market_cap_close') - Optional wenn zeitbasierte Vorhersage aktiviert")
    operator: Optional[str] = Field(None, description="Vergleichsoperator: '>', '<', '>=', '<=', '=' - Optional wenn zeitbasierte Vorhersage aktiviert")
    target_value: Optional[float] = Field(None, description="Schwellwert - Optional wenn zeitbasierte Vorhersage aktiviert")
    
    @validator('model_type', allow_reuse=True)
    def validate_model_type(cls, v):
        """Validiert dass nur random_forest oder xgboost erlaubt sind"""
        allowed = ['random_forest', 'xgboost']
        if v not in allowed:
            raise ValueError(f'model_type muss einer von {allowed} sein')
        return v
    
    @validator('operator')
    def validate_operator(cls, v, values):
        """Validiert Operator - Optional wenn zeitbasierte Vorhersage aktiviert"""
        if v is None:
            # Prüfe ob zeitbasierte Vorhersage aktiviert ist
            if values.get('use_time_based_prediction', False):
                return v  # Erlaubt wenn zeitbasierte Vorhersage aktiviert
            raise ValueError('operator ist erforderlich wenn zeitbasierte Vorhersage nicht aktiviert ist (verwende ">" für "größer als", "<" für "kleiner als")')
        allowed = ['>', '<', '>=', '<=', '=']
        if v not in allowed:
            raise ValueError(f'operator muss einer von {allowed} sein (du hast "{v}" verwendet)')
        return v

    @validator('target_var')
    def validate_target_var(cls, v, values):
        """Validiert target_var - Bei zeitbasierter Vorhersage automatisch 'price_close' setzen"""
        if v is None:
            if values.get('use_time_based_prediction', False):
                return 'price_close'  # ✅ FIX: Automatisch price_close bei zeitbasierter Vorhersage
            raise ValueError('target_var ist erforderlich wenn zeitbasierte Vorhersage nicht aktiviert ist (z.B. "price_close", "market_cap_close")')
        return v

    @validator('target_value')
    def validate_target_value(cls, v, values):
        """Validiert target_value - Optional wenn zeitbasierte Vorhersage aktiviert"""
        if v is None:
            if values.get('use_time_based_prediction', False):
                return v  # Erlaubt wenn zeitbasierte Vorhersage aktiviert
            raise ValueError('target_value ist erforderlich wenn zeitbasierte Vorhersage nicht aktiviert ist (z.B. 0.05 für 5% Änderung)')
        return v

    @validator('future_minutes')
    def validate_future_minutes(cls, v, values):
        """Validiert future_minutes - Erforderlich wenn zeitbasierte Vorhersage aktiviert"""
        if values.get('use_time_based_prediction', False):
            if v is None or v <= 0:
                raise ValueError('future_minutes ist erforderlich und muss > 0 sein wenn zeitbasierte Vorhersage aktiviert ist (z.B. 15 für 15 Minuten)')
        return v

    @validator('min_percent_change')
    def validate_min_percent_change(cls, v, values):
        """Validiert min_percent_change - Erforderlich wenn zeitbasierte Vorhersage aktiviert"""
        if values.get('use_time_based_prediction', False):
            if v is None or v <= 0:
                raise ValueError('min_percent_change ist erforderlich und muss > 0 sein wenn zeitbasierte Vorhersage aktiviert ist (z.B. 0.05 für 5% Änderung)')
        return v

    @validator('direction')
    def validate_direction(cls, v, values):
        """Validiert direction - Muss gültig sein wenn zeitbasierte Vorhersage aktiviert"""
        if values.get('use_time_based_prediction', False):
            allowed = ['up', 'down', 'both']
            if v not in allowed:
                raise ValueError(f'direction muss einer von {allowed} sein wenn zeitbasierte Vorhersage aktiviert ist (du hast "{v}" verwendet)')
        return v
    
    @validator('train_start', 'train_end', pre=True)
    def ensure_utc(cls, v):
        """Konvertiert datetime zu UTC (tz-aware)"""
        from datetime import timezone
        
        if isinstance(v, str):
            # ISO-Format mit Z oder +00:00
            v = v.replace('Z', '+00:00')
            v = datetime.fromisoformat(v)
        
        if isinstance(v, datetime):
            if v.tzinfo is None:
                v = v.replace(tzinfo=timezone.utc)
            else:
                v = v.astimezone(timezone.utc)
        
        return v
    
    # # @model_validator(mode='after')  # Pydantic v1 compatibility  # Pydantic v1 compatibility
    # def validate_train_dates(self):
    #     """Validiert dass train_start < train_end (CHECK Constraint)"""
    #     if self.train_start and self.train_end and self.train_start >= self.train_end:
    #         raise ValueError('train_start muss vor train_end liegen (CHECK Constraint)')
    #     return self
    

class TestModelRequest(BaseModel):
    """Request für Modell-Test"""
    # model_id ist bereits im URL-Pfad, nicht im Body
    test_start: datetime = Field(..., description="Start-Zeitpunkt für Test-Daten (ISO-Format mit UTC)")
    test_end: datetime = Field(..., description="Ende-Zeitpunkt für Test-Daten (ISO-Format mit UTC)")
    
    @validator('test_start', 'test_end', pre=True)
    def ensure_utc(cls, v):
        """Konvertiert datetime zu UTC (tz-aware)"""
        from datetime import timezone
        
        if isinstance(v, str):
            v = v.replace('Z', '+00:00')
            v = datetime.fromisoformat(v)
        
        if isinstance(v, datetime):
            if v.tzinfo is None:
                v = v.replace(tzinfo=timezone.utc)
            else:
                v = v.astimezone(timezone.utc)
        
        return v
    
    # @model_validator(mode='after')  # Pydantic v1 compatibility
    def validate_test_dates(self):
        """Validiert dass test_start < test_end (CHECK Constraint)"""
        if self.test_start and self.test_end and self.test_start >= self.test_end:
            raise ValueError('test_start muss vor test_end liegen (CHECK Constraint)')
        return self

class UpdateModelRequest(BaseModel):
    """Request für Modell-Update (z.B. Name, Beschreibung)"""
    name: Optional[str] = Field(None, description="Neuer Modell-Name (eindeutig)")
    description: Optional[str] = Field(None, description="Neue Beschreibung des Modells")

    @validator('name')
    def validate_name_not_empty(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Name darf nicht leer sein')
        return v

class CompareModelsRequest(BaseModel):
    """Request für Modell-Vergleich (bis zu 4 Modelle)"""
    model_ids: List[int] = Field(..., description="Liste der Modell-IDs zum Vergleichen (2-4 Modelle)", min_items=2, max_items=4)
    test_start: datetime = Field(..., description="Start-Zeitpunkt für Test-Daten (ISO-Format mit UTC)")
    test_end: datetime = Field(..., description="Ende-Zeitpunkt für Test-Daten (ISO-Format mit UTC)")
    
    # Legacy-Support für alte API (model_a_id, model_b_id)
    model_a_id: Optional[int] = Field(None, description="[DEPRECATED] ID des ersten Modells - verwende model_ids")
    model_b_id: Optional[int] = Field(None, description="[DEPRECATED] ID des zweiten Modells - verwende model_ids")
    
    @validator('test_start', 'test_end', pre=True)
    def ensure_utc(cls, v):
        """Konvertiert datetime zu UTC (tz-aware)"""
        from datetime import timezone
        
        if isinstance(v, str):
            v = v.replace('Z', '+00:00')
            v = datetime.fromisoformat(v)
        
        if isinstance(v, datetime):
            if v.tzinfo is None:
                v = v.replace(tzinfo=timezone.utc)
            else:
                v = v.astimezone(timezone.utc)
        
        return v
    
    @validator('model_ids')
    def validate_unique_models(cls, v):
        """Validiert dass alle Modelle unterschiedlich sind"""
        if len(v) != len(set(v)):
            raise ValueError('Alle model_ids müssen unterschiedlich sein')
        if len(v) < 2:
            raise ValueError('Mindestens 2 Modelle erforderlich')
        if len(v) > 4:
            raise ValueError('Maximal 4 Modelle erlaubt')
        return v
    
    def get_model_ids(self) -> List[int]:
        """Gibt Liste der Modell-IDs zurück (mit Legacy-Support)"""
        if self.model_ids:
            return self.model_ids
        # Legacy-Support
        if self.model_a_id and self.model_b_id:
            return [self.model_a_id, self.model_b_id]
        return []

# ============================================================
# Response Schemas
# ============================================================

class ModelResponse(BaseModel):
    """Response für Modell-Details"""
    id: int
    name: str
    model_type: str
    status: str
    created_at: datetime
    updated_at: datetime
    is_deleted: bool
    target_variable: str
    target_operator: Optional[str] = None  # Optional für zeitbasierte Vorhersagen
    target_value: Optional[float] = None  # Optional für zeitbasierte Vorhersagen
    train_start: datetime
    train_end: datetime
    features: List[str]  # JSONB → List
    phases: Optional[List[int]]  # JSONB → List
    params: Optional[Dict[str, Any]]  # JSONB → Dict
    feature_importance: Optional[Dict[str, float]]  # JSONB → Dict
    training_accuracy: Optional[float]
    training_f1: Optional[float]
    training_precision: Optional[float]
    training_recall: Optional[float]
    # NEU: Zusätzliche Metriken (Verbesserung 1.5)
    roc_auc: Optional[float] = Field(None, description="ROC-AUC Score")
    mcc: Optional[float] = Field(None, description="Matthews Correlation Coefficient")
    fpr: Optional[float] = Field(None, description="False Positive Rate")
    fnr: Optional[float] = Field(None, description="False Negative Rate")
    confusion_matrix: Optional[Dict[str, int]] = Field(None, description="Confusion Matrix: {tp, tn, fp, fn}")
    simulated_profit_pct: Optional[float] = Field(None, description="Simulierter Profit in Prozent")
    # Legacy: Confusion Matrix als einzelne Felder (für Rückwärtskompatibilität)
    tp: Optional[int] = Field(None, description="True Positive (aus confusion_matrix)")
    tn: Optional[int] = Field(None, description="True Negative (aus confusion_matrix)")
    fp: Optional[int] = Field(None, description="False Positive (aus confusion_matrix)")
    fn: Optional[int] = Field(None, description="False Negative (aus confusion_matrix)")
    # CV-Ergebnisse (Verbesserung 1.4)
    cv_scores: Optional[Dict[str, Any]] = Field(None, description="Cross-Validation Ergebnisse")
    cv_overfitting_gap: Optional[float] = Field(None, description="Overfitting-Gap (Train-Test Accuracy Differenz)")
    model_file_path: Optional[str]
    description: Optional[str]
    
    class Config:
        from_attributes = True

class TestResultResponse(BaseModel):
    """Response für Test-Ergebnisse"""
    id: int
    model_id: int
    created_at: datetime
    test_start: datetime
    test_end: datetime
    accuracy: Optional[float]
    f1_score: Optional[float]
    precision_score: Optional[float]
    recall: Optional[float]
    # NEU: Zusätzliche Metriken (Verbesserung 1.5)
    roc_auc: Optional[float] = Field(None, description="ROC-AUC Score")
    mcc: Optional[float] = Field(None, description="Matthews Correlation Coefficient")
    fpr: Optional[float] = Field(None, description="False Positive Rate")
    fnr: Optional[float] = Field(None, description="False Negative Rate")
    confusion_matrix: Optional[Dict[str, int]] = Field(None, description="Confusion Matrix: {tp, tn, fp, fn}")
    simulated_profit_pct: Optional[float] = Field(None, description="Simulierter Profit in Prozent")
    # Legacy: Confusion Matrix als einzelne Felder (für Rückwärtskompatibilität)
    tp: Optional[int] = Field(None, description="True Positive (aus confusion_matrix)")
    tn: Optional[int] = Field(None, description="True Negative (aus confusion_matrix)")
    fp: Optional[int] = Field(None, description="False Positive (aus confusion_matrix)")
    fn: Optional[int] = Field(None, description="False Negative (aus confusion_matrix)")
    num_samples: Optional[int]
    num_positive: Optional[int]
    num_negative: Optional[int]
    has_overlap: bool
    overlap_note: Optional[str]
    feature_importance: Optional[Dict[str, float]]  # JSONB → Dict
    # Train vs. Test Vergleich (Phase 2)
    train_accuracy: Optional[float] = Field(None, description="Training Accuracy (aus ml_models)")
    train_f1: Optional[float] = Field(None, description="Training F1 (aus ml_models)")
    train_precision: Optional[float] = Field(None, description="Training Precision (aus ml_models)")
    train_recall: Optional[float] = Field(None, description="Training Recall (aus ml_models)")
    accuracy_degradation: Optional[float] = Field(None, description="Train - Test Accuracy (Overfitting-Indikator)")
    f1_degradation: Optional[float] = Field(None, description="Train - Test F1")
    is_overfitted: Optional[bool] = Field(None, description="True wenn accuracy_degradation > 0.1")
    # Test-Zeitraum Info (Phase 2)
    test_duration_days: Optional[float] = Field(None, description="Test-Zeitraum in Tagen")
    
    class Config:
        from_attributes = True

class ModelComparisonResult(BaseModel):
    """Ergebnis für ein einzelnes Modell im Vergleich"""
    model_id: int
    model_name: Optional[str] = None
    test_result_id: Optional[int] = None
    # Metriken
    accuracy: Optional[float] = None
    f1_score: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    roc_auc: Optional[float] = None
    mcc: Optional[float] = None
    fpr: Optional[float] = None
    fnr: Optional[float] = None
    simulated_profit_pct: Optional[float] = None
    confusion_matrix: Optional[Dict[str, int]] = None
    # Durchschnitts-Score (für Ranking)
    avg_score: Optional[float] = None
    rank: Optional[int] = None

class ComparisonResponse(BaseModel):
    """Response für Modell-Vergleich (bis zu 4 Modelle)"""
    id: int
    created_at: datetime
    test_start: datetime
    test_end: datetime
    num_samples: Optional[int] = None
    
    # Neue flexible Struktur (bis zu 4 Modelle)
    model_ids: Optional[List[int]] = None
    test_result_ids: Optional[List[int]] = None
    results: Optional[List[ModelComparisonResult]] = None
    
    # Gewinner-Info
    winner_id: Optional[int] = None
    winner_reason: Optional[str] = None
    
    # Legacy-Support (für alte Vergleiche mit nur 2 Modellen)
    model_a_id: Optional[int] = None
    model_b_id: Optional[int] = None
    a_accuracy: Optional[float] = None
    a_f1: Optional[float] = None
    a_precision: Optional[float] = None
    a_recall: Optional[float] = None
    b_accuracy: Optional[float] = None
    b_f1: Optional[float] = None
    b_precision: Optional[float] = None
    b_recall: Optional[float] = None
    a_mcc: Optional[float] = None
    a_fpr: Optional[float] = None
    a_fnr: Optional[float] = None
    a_simulated_profit_pct: Optional[float] = None
    a_confusion_matrix: Optional[Dict[str, int]] = None
    a_train_accuracy: Optional[float] = None
    a_train_f1: Optional[float] = None
    a_accuracy_degradation: Optional[float] = None
    a_f1_degradation: Optional[float] = None
    a_is_overfitted: Optional[bool] = None
    a_test_duration_days: Optional[float] = None
    b_mcc: Optional[float] = None
    b_fpr: Optional[float] = None
    b_fnr: Optional[float] = None
    b_simulated_profit_pct: Optional[float] = None
    b_confusion_matrix: Optional[Dict[str, int]] = None
    b_train_accuracy: Optional[float] = None
    b_train_f1: Optional[float] = None
    b_accuracy_degradation: Optional[float] = None
    b_f1_degradation: Optional[float] = None
    b_is_overfitted: Optional[bool] = None
    b_test_duration_days: Optional[float] = None
    
    class Config:
        from_attributes = True

class JobResponse(BaseModel):
    """Response für Job-Details"""
    id: int
    job_type: str
    status: str
    priority: int
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    progress: float
    progress_msg: Optional[str]
    error_msg: Optional[str]
    worker_id: Optional[str]
    train_model_type: Optional[str]
    train_target_var: Optional[str]
    train_operator: Optional[str]
    train_value: Optional[float]
    train_start: Optional[datetime]
    train_end: Optional[datetime]
    train_features: Optional[List[str]]  # JSONB → List
    train_phases: Optional[List[int]]  # JSONB → List
    train_params: Optional[Dict[str, Any]]  # JSONB → Dict
    result_model_id: Optional[int]
    test_model_id: Optional[int]
    test_start: Optional[datetime]
    test_end: Optional[datetime]
    result_test_id: Optional[int]
    compare_model_a_id: Optional[int]
    compare_model_b_id: Optional[int]
    compare_model_ids: Optional[List[int]] = None  # NEU: Bis zu 4 Modelle
    compare_start: Optional[datetime]
    compare_end: Optional[datetime]
    result_comparison_id: Optional[int]
    
    # NEU: Ergebnisse direkt inkludieren (wenn verfügbar)
    result_model: Optional[ModelResponse] = None  # Wenn result_model_id gesetzt
    result_test: Optional[TestResultResponse] = None  # Wenn result_test_id gesetzt
    result_comparison: Optional[ComparisonResponse] = None  # Wenn result_comparison_id gesetzt
    
    class Config:
        from_attributes = True

class CreateJobResponse(BaseModel):
    """Response für Job-Erstellung"""
    job_id: int
    message: str
    status: str

class HealthResponse(BaseModel):
    """Response für Health Check"""
    status: str
    db_connected: bool
    uptime_seconds: int
    start_time: Optional[float]
    total_jobs_processed: int
    last_error: Optional[str]

# ============================================================
# Configuration Schemas
# ============================================================

class ConfigResponse(BaseModel):
    """Response für Konfigurationsdaten"""
    # Database
    db_dsn: str
    db_refresh_interval: int

    # ML Training
    model_storage_path: str
    max_concurrent_jobs: int
    job_poll_interval: int
    default_training_hours: int
    max_training_hours: int
    min_training_hours: int

class ConfigUpdateRequest(BaseModel):
    """Request für Konfigurations-Update"""
    # Database
    db_dsn: Optional[str] = None
    db_refresh_interval: Optional[int] = None

    # ML Training
    model_storage_path: Optional[str] = None
    max_concurrent_jobs: Optional[int] = None
    job_poll_interval: Optional[int] = None
    default_training_hours: Optional[int] = None
    max_training_hours: Optional[int] = None
    min_training_hours: Optional[int] = None

class ConfigUpdateResponse(BaseModel):
    """Response für Konfigurations-Update"""
    message: str
    status: str
    updated_fields: List[str]

class SimpleTimeBasedRequest(BaseModel):
    """Vereinfachte Request für zeitbasierte Modell-Training"""
    name: str = Field(..., description="Modell-Name (eindeutig)")
    model_type: str = Field(..., description="Modell-Typ: 'random_forest' oder 'xgboost'")
    future_minutes: int = Field(..., description="Minuten in die Zukunft")
    min_percent_change: float = Field(..., description="Mindest-Preisänderung in Prozent")
    direction: str = Field(..., description="'up' oder 'down'")
    features: Optional[List[str]] = Field(None, description="Liste der Feature-Namen")
    train_start: Optional[str] = Field(None, description="Start-Zeitpunkt (ISO-Format)")
    train_end: Optional[str] = Field(None, description="Ende-Zeitpunkt (ISO-Format)")

    @validator('model_type', allow_reuse=True)
    def validate_model_type(cls, v):
        """Validiert dass nur random_forest oder xgboost erlaubt sind"""
        allowed = ['random_forest', 'xgboost']
        if v not in allowed:
            raise ValueError(f'model_type muss einer von {allowed} sein')
        return v

    # ML Training
    model_storage_path: Optional[str] = None
    max_concurrent_jobs: Optional[int] = None
    job_poll_interval: Optional[int] = None
    default_training_hours: Optional[int] = None
    max_training_hours: Optional[int] = None
    min_training_hours: Optional[int] = None

class ConfigUpdateResponse(BaseModel):
    """Response für Konfigurations-Update"""
    message: str
    status: str
    updated_fields: List[str]

class SimpleTimeBasedRequest(BaseModel):
    """Vereinfachte Request für zeitbasierte Modell-Training"""
    name: str = Field(..., description="Modell-Name (eindeutig)")
    model_type: str = Field(..., description="Modell-Typ: 'random_forest' oder 'xgboost'")
    future_minutes: int = Field(..., description="Minuten in die Zukunft")
    min_percent_change: float = Field(..., description="Mindest-Preisänderung in Prozent")
    direction: str = Field(..., description="'up' oder 'down'")
    features: Optional[List[str]] = Field(None, description="Liste der Feature-Namen")
    train_start: Optional[str] = Field(None, description="Start-Zeitpunkt (ISO-Format)")
    train_end: Optional[str] = Field(None, description="Ende-Zeitpunkt (ISO-Format)")

    @validator('model_type', allow_reuse=True)
    def validate_model_type(cls, v):
        """Validiert dass nur random_forest oder xgboost erlaubt sind"""
        allowed = ['random_forest', 'xgboost']
        if v not in allowed:
            raise ValueError(f'model_type muss einer von {allowed} sein')
        return v
