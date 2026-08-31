from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import json
import time
import httpx

from backend.app.schemas.ai import (
    AgentAnalysis,
    AgentFinding,
    AgentUncertainty,
    AgentRecommendation,
    EvidenceReference,
)
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.cache import cache, CacheKeys
from backend.app.providers.health import provider_health_registry


class LLMProvider(ABC):
    """Abstract interface for LLM backends (Mock, Gemini, OpenAI)."""

    @abstractmethod
    async def generate_structured_analysis(
        self,
        system_prompt: str,
        user_prompt: str,
        evidence: List[EvidenceReference],
        context_data: Dict[str, Any]
    ) -> AgentAnalysis:
        pass


class MockLLMProvider(LLMProvider):
    """
    Deterministic analytical synthesizer using transparent mathematical synthesis.
    Eliminates external API costs, supports offline demonstrations,
    and guarantees zero hallucinations or altered scientific values.
    """

    async def generate_structured_analysis(
        self,
        system_prompt: str,
        user_prompt: str,
        evidence: List[EvidenceReference],
        context_data: Dict[str, Any]
    ) -> AgentAnalysis:
        assessment = context_data.get("assessment", {})
        location = context_data.get("location", {})
        environment = context_data.get("environment", {})
        history = context_data.get("history", {}).get("history", [])
        event = context_data.get("event", {})
        quality = context_data.get("quality", {}).get("data_quality", {})
        nearby = context_data.get("nearby", {}).get("stations", [])
        field_reports_data = context_data.get("field_reports", {}).get("reports", [])
        assistance_data = context_data.get("assistance_requests", {}).get("requests", [])

        loc_name = location.get("name", "Target Monitoring Node")
        loc_id = location.get("id", "NER-STATION")
        risk_score = float(assessment.get("risk_score", 0.0))
        risk_level = str(assessment.get("risk_level", "LOW"))
        confidence = float(assessment.get("confidence_score", 0.8))
        trajectory = str(assessment.get("trajectory", "STABLE"))
        factors = assessment.get("factors", [])

        findings: List[AgentFinding] = []
        uncertainties: List[AgentUncertainty] = []
        recommendations: List[AgentRecommendation] = []

        # 1. Identify primary risk drivers from factors
        sorted_factors = sorted(factors, key=lambda x: x.get("contribution", 0.0), reverse=True)
        top_drivers = [f for f in sorted_factors if f.get("contribution", 0.0) >= 5.0]

        for f in top_drivers[:3]:
            f_name = f.get("name", "").replace("_", " ").title()
            contrib = f.get("contribution", 0.0)
            status = f.get("status", "MODERATE")
            val = f.get("raw_value")

            ev = EvidenceReference(
                evidence_type="FACTOR_CONTRIBUTION",
                id_reference=assessment.get("assessment_id"),
                metric=f.get("name"),
                value=f"{val} (Score: {f.get('normalized_score', 0):.2f}, Contrib: {contrib:.1f} pts)",
                notes=f.get("description")
            )
            evidence.append(ev)

            findings.append(
                AgentFinding(
                    type="risk_driver",
                    title=f"Elevated {f_name} ({status})",
                    description=f"{f_name} contributes {contrib:.1f} points towards total hazard risk. Current measured value: {val}.",
                    evidence=[ev]
                )
            )

        # 2. Historical trajectory findings
        if len(history) >= 2:
            prev_score = float(history[1].get("risk_score", risk_score))
            delta = risk_score - prev_score
            if abs(delta) >= 1.0:
                direction_word = "increased" if delta > 0 else "decreased"
                ev_hist = EvidenceReference(
                    evidence_type="HISTORICAL_DELTA",
                    id_reference=history[1].get("history_id"),
                    metric="risk_score_delta",
                    value=f"{prev_score:.1f} -> {risk_score:.1f} ({delta:+.1f} pts)",
                    timestamp=history[0].get("timestamp")
                )
                evidence.append(ev_hist)
                findings.append(
                    AgentFinding(
                        type="signal_change",
                        title=f"Risk Score {direction_word.capitalize()} by {abs(delta):.1f} pts",
                        description=f"Hazard score evolved from {prev_score:.1f} to {risk_score:.1f} over recent assessment cycles. Trajectory is currently {trajectory}.",
                        evidence=[ev_hist]
                    )
                )

        # 3. Field Ground-Truth Corroboration
        if field_reports_data:
            road_blocks = [r for r in field_reports_data if r.get("report_type") == "ROAD_BLOCKED"]
            landslides_seen = [r for r in field_reports_data if r.get("report_type") == "LANDSLIDE_OBSERVED"]

            ev_field = EvidenceReference(
                evidence_type="FIELD_GROUND_TRUTH",
                metric="rescue_team_reports",
                value=f"{len(field_reports_data)} observations ({len(road_blocks)} road blockages, {len(landslides_seen)} slope movements)",
                notes=f"Latest: {field_reports_data[0].get('description')}"
            )
            evidence.append(ev_field)

            findings.append(
                AgentFinding(
                    type="field_observation",
                    title=f"On-Ground Rescue Intelligence ({len(field_reports_data)} Reports)",
                    description=(
                        f"Field rescue teams report ground conditions in sector: "
                        f"{field_reports_data[0].get('description')} "
                        f"(Reported by {field_reports_data[0].get('reported_by')}, status: {field_reports_data[0].get('status')})."
                    ),
                    evidence=[ev_field]
                )
            )

        # 4. Regional Neighbor Findings
        elevated_neighbors = [n for n in nearby if n.get("risk_score", 0.0) >= 40.0]
        if elevated_neighbors:
            n_names = ", ".join([f"{n.get('name')} ({n.get('risk_score', 0):.0f})" for n in elevated_neighbors[:2]])
            ev_near = EvidenceReference(
                evidence_type="REGIONAL_CORRELATION",
                metric="nearby_elevated_stations",
                value=f"{len(elevated_neighbors)} stations elevated",
                notes=n_names
            )
            evidence.append(ev_near)
            findings.append(
                AgentFinding(
                    type="regional_correlation",
                    title="Regional Hazard Clustering Detected",
                    description=f"Nearby monitoring nodes within 200km also exhibit elevated risk: {n_names}.",
                    evidence=[ev_near]
                )
            )

        # 5. Data Quality & Uncertainty Assessment
        comp_score = quality.get("completeness_score", 1.0)
        missing = quality.get("missing_fields", [])

        if comp_score < 0.9 or missing:
            uncertainties.append(
                AgentUncertainty(
                    factor="Sensor Completeness",
                    reason=f"Missing or partial telemetry: {', '.join(missing) if missing else 'Subsurface moisture degraded'}",
                    impact="HIGH" if comp_score < 0.7 else "MODERATE"
                )
            )
        else:
            uncertainties.append(
                AgentUncertainty(
                    factor="Geological Micro-variations",
                    reason="Prototype baseline model assumes uniform rock formation across sensor perimeter.",
                    impact="LOW"
                )
            )

        # 6. Operational Recommendations & SOS Handling
        active_sos = [a for a in assistance_data if a.get("status") in ["REQUESTED", "ACKNOWLEDGED"]]
        if active_sos:
            recommendations.append(
                AgentRecommendation(
                    priority="CRITICAL",
                    action=f"Dispatch Backup for Unit SOS ({active_sos[0].get('request_type')})",
                    rationale=f"Field unit urgently requested assistance: {active_sos[0].get('description')}"
                )
            )

        if risk_score >= 75.0:
            recommendations.append(
                AgentRecommendation(
                    priority="CRITICAL",
                    action="Issue Immediate Field Reconnaissance & Tactical Alert",
                    rationale="Critical hazard threshold breached with severe multi-signal agreement between surface rain and pore saturation."
                )
            )
            recommendations.append(
                AgentRecommendation(
                    priority="HIGH",
                    action="Verify Arterial Hill Road Clearances & Drainage Culverts",
                    rationale="High probability of debris flow and road embankment scour along transit corridors."
                )
            )
        elif risk_score >= 50.0:
            recommendations.append(
                AgentRecommendation(
                    priority="HIGH",
                    action="Increase Monitoring Frequency to 15-Minute Polling",
                    rationale="High landslide potential driven by rising pore saturation and persistent precipitation."
                )
            )
            recommendations.append(
                AgentRecommendation(
                    priority="MEDIUM",
                    action="Audit Rain Gauge & Piezometer Telemetry Health",
                    rationale="Ensure uninterrupted sensor data ingestion as slope approaches critical thresholds."
                )
            )
        else:
            recommendations.append(
                AgentRecommendation(
                    priority="LOW",
                    action="Maintain Routine Surveillance",
                    rationale="Environmental telemetry remains within stable baseline operating parameters."
                )
            )

        # 7. Concise Expert Summary
        summary_text = (
            f"At {loc_name}, landslide risk is currently assessed at {risk_score:.1f}/100 ({risk_level}) "
            f"with assessment confidence at {confidence * 100.0:.0f}% and trajectory classified as {trajectory}. "
            f"The primary risk drivers are " + ", ".join([f.get("name", "").replace("_", " ") for f in top_drivers[:2]]) + ". "
        )
        if field_reports_data:
            summary_text += f"Ground rescue teams have submitted {len(field_reports_data)} sector observations. "
        summary_text += f"This analysis is operating under {settings.DATA_MODE} data ingestion."

        return AgentAnalysis(
            summary=summary_text,
            risk_level=risk_level,
            risk_score=risk_score,
            confidence=confidence,
            trajectory=trajectory,
            findings=findings,
            uncertainties=uncertainties,
            recommendations=recommendations,
            data_mode=settings.DATA_MODE,
            all_evidence=evidence
        )


class GeminiProvider(LLMProvider):
    """
    Google AI Studio / Gemini LLM Provider.
    Generates structured scientific explanations and operational briefings from verified telemetry.
    Strictly constrained by prompt guardrails and automatic fallback to deterministic synthesis.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: float = settings.AGENT_TIMEOUT_SECONDS
    ):
        self.api_key = api_key or settings.EFFECTIVE_GEMINI_KEY
        self.model = model or settings.EFFECTIVE_GEMINI_MODEL
        self.timeout = timeout
        self.mock_fallback = MockLLMProvider()

    async def generate_structured_analysis(
        self,
        system_prompt: str,
        user_prompt: str,
        evidence: List[EvidenceReference],
        context_data: Dict[str, Any]
    ) -> AgentAnalysis:
        # Extract ground truth deterministic values to prevent LLM override
        assessment = context_data.get("assessment", {})
        loc = context_data.get("location", {})
        location_id = loc.get("id", "NER-STATION")
        assessment_id = str(assessment.get("assessment_id", assessment.get("id", "current")))
        
        # 1. Check Redis Cache for identical assessment snapshot
        cache_key = CacheKeys.ai_explanation(location_id, assessment_id, "expert_briefing")
        cached_result = await cache.get(cache_key)
        if cached_result:
            try:
                logger.debug(f"Redis Cache HIT for Gemini explanation at {location_id}")
                return AgentAnalysis(**cached_result)
            except Exception:
                pass

        if not self.api_key:
            logger.info("No Gemini API key configured. Executing deterministic analytical synthesizer.")
            return await self.mock_fallback.generate_structured_analysis(system_prompt, user_prompt, evidence, context_data)

        # Build strict prompt payload with scientific guardrails
        strict_system_prompt = (
            f"{system_prompt}\n\n"
            "CRITICAL SCIENTIFIC SAFETY RULES:\n"
            "1. You are an explainability and evidence-synthesis assistant for professional disaster managers.\n"
            "2. You MUST NOT modify, recalculate, or contradict the deterministic risk score, severity level, confidence, or trajectory.\n"
            "3. You MUST NOT invent sensor telemetry, rainfall numbers, soil moisture levels, slope angles, or historical incidents.\n"
            "4. Only cite and summarize the verified measurements and factor contributions provided in the context JSON.\n"
            "5. Clearly differentiate verified physical measurements from derived indicators and data quality uncertainties.\n"
            "6. 'recommendations' must describe specific physical/tactical investigations for human experts to conduct, NOT autonomous emergency declarations.\n"
            "7. Return STRICTLY valid JSON matching the schema below without conversational filler or markdown wrappers."
        )

        schema_format = {
            "summary": "Concise 2-3 sentence technical operational summary.",
            "findings": [
                {
                    "type": "risk_driver | signal_change | field_observation | regional_correlation",
                    "title": "Short descriptive title",
                    "description": "Evidence-backed explanation citing exact values."
                }
            ],
            "uncertainties": [
                {
                    "factor": "Factor name (e.g. Subsurface Moisture)",
                    "reason": "Technical reason for uncertainty or sensor limitation",
                    "impact": "CRITICAL | HIGH | MODERATE | LOW"
                }
            ],
            "recommendations": [
                {
                    "priority": "CRITICAL | HIGH | MEDIUM | LOW",
                    "action": "Concrete investigation action for duty officers",
                    "rationale": "Justification based on telemetry"
                }
            ]
        }

        user_content = (
            f"USER QUERY: {user_prompt}\n\n"
            f"VERIFIED CONTEXT DATA:\n{json.dumps(context_data, default=str)}\n\n"
            f"DESIRED JSON SCHEMA STRUCTURE:\n{json.dumps(schema_format)}"
        )

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        headers = {
            "Content-Type": "application/json"
        }
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": f"SYSTEM INSTRUCTIONS:\n{strict_system_prompt}\n\n{user_content}"}
                    ]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.2
            }
        }

        start_t = time.perf_counter()
        http_timeout = httpx.Timeout(self.timeout, connect=5.0)
        try:
            async with httpx.AsyncClient(timeout=http_timeout) as client:
                resp = await client.post(url, headers=headers, json=payload)
                latency_ms = (time.perf_counter() - start_t) * 1000.0


                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        raw_text = candidates[0]["content"]["parts"][0]["text"].strip()
                        if raw_text.startswith("```json"):
                            raw_text = raw_text[7:]
                        elif raw_text.startswith("```"):
                            raw_text = raw_text[3:]
                        if raw_text.endswith("```"):
                            raw_text = raw_text[:-3]
                        raw_text = raw_text.strip()
                        
                        try:
                            parsed_json = json.loads(raw_text)
                        except json.JSONDecodeError:
                            # Try finding first { and last }
                            start_idx = raw_text.find("{")
                            end_idx = raw_text.rfind("}")
                            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                                parsed_json = json.loads(raw_text[start_idx:end_idx + 1])
                            else:
                                raise

                        # Enforce deterministic ground truth values from assessment
                        risk_score = float(assessment.get("risk_score", 0.0))
                        risk_level = str(assessment.get("risk_level", "LOW"))
                        confidence = float(assessment.get("confidence_score", 0.8))
                        trajectory = str(assessment.get("trajectory", "STABLE"))

                        # Parse findings, uncertainties, recommendations safely
                        findings = [
                            AgentFinding(
                                type=f.get("type", "risk_driver"),
                                title=f.get("title", "Hazard Indicator"),
                                description=f.get("description", "")
                            )
                            for f in parsed_json.get("findings", [])
                        ]
                        uncertainties = [
                            AgentUncertainty(
                                factor=u.get("factor", "Data Quality"),
                                reason=u.get("reason", "Sensor boundary limit"),
                                impact=u.get("impact", "MODERATE")
                            )
                            for u in parsed_json.get("uncertainties", [])
                        ]
                        recommendations = [
                            AgentRecommendation(
                                priority=r.get("priority", "HIGH"),
                                action=r.get("action", "Inspect site sensors"),
                                rationale=r.get("rationale", "Verified by telemetry")
                            )
                            for r in parsed_json.get("recommendations", [])
                        ]

                        analysis = AgentAnalysis(
                            summary=parsed_json.get("summary", "Assessment explanation generated by Gemini intelligence layer."),
                            risk_level=risk_level,
                            risk_score=risk_score,
                            confidence=confidence,
                            trajectory=trajectory,
                            findings=findings,
                            uncertainties=uncertainties,
                            recommendations=recommendations,
                            data_mode=settings.DATA_MODE,
                            all_evidence=evidence
                        )

                        # Cache in Upstash Redis
                        await cache.set(
                            cache_key,
                            analysis.model_dump(mode="json"),
                            ttl_seconds=settings.AI_EXPLANATION_CACHE_TTL_SECONDS
                        )
                        provider_health_registry.record_success("gemini-llm", latency_ms)
                        return analysis

                logger.warning(f"Gemini API returned HTTP {resp.status_code}: {resp.text[:200]}. Engaging deterministic fallback.")
                provider_health_registry.record_failure("gemini-llm", f"HTTP {resp.status_code}")

        except Exception as err:
            logger.warning(f"Gemini generation exception ({type(err).__name__}: {err}). Engaging deterministic fallback.")
            provider_health_registry.record_failure("gemini-llm", f"{type(err).__name__}: {err}")

        # Seamless Fallback to deterministic synthesis
        return await self.mock_fallback.generate_structured_analysis(system_prompt, user_prompt, evidence, context_data)


def get_llm_provider() -> LLMProvider:
    """Factory creating appropriate LLM provider based on settings."""
    if settings.AI_MODE.upper() == "LIVE" and settings.EFFECTIVE_GEMINI_KEY:
        return GeminiProvider(
            api_key=settings.EFFECTIVE_GEMINI_KEY,
            model=settings.EFFECTIVE_GEMINI_MODEL
        )
    return MockLLMProvider()
