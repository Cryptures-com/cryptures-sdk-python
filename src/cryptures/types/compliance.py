"""Models for the ``compliance`` domain (KYC/KYB sessions, AML, wallet screening, monitoring)."""

from __future__ import annotations

from typing import Dict, List, Optional

from .._models import CrypturesModel, Number

__all__ = [
    "AmlCheck",
    "AmlResult",
    "AmlResultItem",
    "ComplianceReport",
    "MonitoringSubscription",
    "MonitoringSubscriptionList",
    "Preset",
    "PresetList",
    "Session",
    "SessionCreated",
    "SessionList",
    "SessionResultItem",
    "SessionStatusUpdate",
    "SessionSummary",
    "SessionWarning",
    "WalletRiskFactor",
    "WalletScreening",
    "WalletScreeningResult",
]


class SessionCreated(CrypturesModel):
    session_id: str
    url: str
    """Hosted verification page to redirect the end user to. Single-use."""
    status: str
    """Status as reported at creation (in practice ``"Not Started"``; do not assert on it)."""


class SessionResultItem(CrypturesModel):
    """One check outcome. Only the detail fields meaningful for ``feature`` are present."""

    feature: str
    status: str
    document_type: Optional[str] = None
    name: Optional[str] = None
    date_of_birth: Optional[str] = None
    issuing_state: Optional[str] = None
    method: Optional[str] = None
    score: Optional[Number] = None
    total_hits: Optional[int] = None
    entity_type: Optional[str] = None
    company_name: Optional[str] = None
    registration_number: Optional[str] = None
    country_code: Optional[str] = None
    tier: Optional[str] = None
    people_count: Optional[int] = None


class SessionWarning(CrypturesModel):
    feature: str
    short_description: str
    long_description: Optional[str] = None


class Session(CrypturesModel):
    """A verification session and its normalized result (compliance.session.get)."""

    session_id: str
    status: str
    """e.g. ``Not Started``, ``In Review``, ``Approved``, ``Declined``. This list can grow."""
    external_user_id: Optional[str] = None
    kind: str
    """``kyc``, ``kyb`` or ``aml_standalone``."""
    features: List[str]
    results: List[SessionResultItem]
    warnings: List[SessionWarning]
    document_urls: Optional[Dict[str, str]] = None
    """Document field name -> URL on the API's own documents endpoint (fetch with your API key)."""


class SessionSummary(CrypturesModel):
    session_id: str
    external_user_id: str
    preset_id: str
    status: str
    kind: str
    created_at: str
    updated_at: str


class SessionList(CrypturesModel):
    """One page of sessions. Pass ``next_cursor`` as ``cursor`` for the next page."""

    sessions: List[SessionSummary]
    next_cursor: Optional[str]


class Preset(CrypturesModel):
    id: str
    label: str
    kind: str
    """``kyc`` verifies a person, ``kyb`` verifies a company."""


class PresetList(CrypturesModel):
    presets: List[Preset]


class SessionStatusUpdate(CrypturesModel):
    session_id: str
    status: str


class AmlResultItem(CrypturesModel):
    feature: str
    status: str
    total_hits: Optional[int] = None
    entity_type: Optional[str] = None
    score: Optional[Number] = None


class AmlResult(CrypturesModel):
    features: List[str]
    results: List[AmlResultItem]
    warnings: List[SessionWarning]


class AmlCheck(CrypturesModel):
    """Result of a standalone AML screening (compliance.aml.check)."""

    check_id: str
    session_id: Optional[str]
    external_user_id: str
    status: str
    result: AmlResult
    created_at: str


class WalletRiskFactor(CrypturesModel):
    category: Optional[str] = None
    direction: Optional[str] = None
    exposure_type: Optional[str] = None
    percentage: Optional[Number] = None
    is_high_risk: Optional[bool] = None


class WalletScreeningResult(CrypturesModel):
    severity: str
    """``UNKNOWN``, ``LOW``, ``MEDIUM``, ``HIGH`` or ``CRITICAL``."""
    risk_score: Optional[int] = None
    sanctions_hit: bool
    pep_counterparty: Optional[bool] = None
    dominant_risk_category: Optional[str] = None
    risk_factors: List[WalletRiskFactor]


class WalletScreening(CrypturesModel):
    """A blockchain-address risk screening."""

    check_id: str
    address: str
    chain: str
    result: WalletScreeningResult
    screened_at: str


class MonitoringSubscription(CrypturesModel):
    entity_kind: str
    """``user`` or ``business``."""
    external_user_id: str
    status: str
    """``active``, ``cancelled`` or ``suspended_insufficient_balance``."""
    enabled_at: str
    next_renewal_at: str
    cancelled_at: Optional[str]
    created_at: str
    updated_at: str


class MonitoringSubscriptionList(CrypturesModel):
    subscriptions: List[MonitoringSubscription]
    next_cursor: Optional[str]


class ComplianceReport(CrypturesModel):
    """A generated verification report PDF (download it with ``download_report``)."""

    report_id: str
    session_id: str
    generated_at: str
    expires_at: str
    size_bytes: int
    download_url: str
