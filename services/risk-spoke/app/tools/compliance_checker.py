"""
Compliance Checker Tool
KYC/AML screening and regulatory compliance checks
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import hashlib
import re


class ComplianceCheckerTool:
    """Regulatory compliance and AML/KYC screening tool"""

    def __init__(self):
        self.data_dir = Path(__file__).parent.parent.parent.parent.parent / "data" / "stock-data"

        # High-risk jurisdictions (FATF grey/black list examples)
        self.high_risk_jurisdictions = {
            "AF", "BY", "BI", "CF", "CD", "IQ", "IR", "KP", "LB", "LY",
            "ML", "MM", "NI", "PK", "PA", "PH", "SN", "SS", "SD", "SY",
            "TT", "UG", "VU", "YE", "ZW"
        }

        # PEP (Politically Exposed Person) indicators
        self.pep_keywords = [
            "minister", "senator", "congressman", "parliament", "ambassador",
            "governor", "mayor", "president", "chairman", "director general",
            "commissioner", "judge", "military", "general", "admiral"
        ]

        # Suspicious activity indicators
        self.suspicious_patterns = {
            "rapid_trading": "Unusual number of trades in short period",
            "round_amounts": "Transactions in round amounts (possible structuring)",
            "layering": "Complex web of transactions (possible layering)",
            "smurfing": "Multiple small transactions below reporting threshold",
            "high_risk_jurisdiction": "Transaction involving high-risk jurisdiction",
            "unusual_volume": "Transaction volume inconsistent with profile",
            "time_pattern": "Unusual timing patterns (off-hours trading)"
        }

    async def get_tool_info(self) -> Dict:
        """Get tool information for MCP protocol"""
        return {
            "name": "risk_check_compliance",
            "description": "Perform KYC/AML screening and regulatory compliance checks",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "check_type": {
                        "type": "string",
                        "enum": ["entity_screening", "transaction_monitoring", "regulatory_compliance", "all"],
                        "description": "Type of compliance check"
                    },
                    "entity_name": {
                        "type": "string",
                        "description": "Entity name for screening (person or organization)"
                    },
                    "entity_type": {
                        "type": "string",
                        "enum": ["individual", "organization"],
                        "description": "Type of entity"
                    },
                    "jurisdiction": {
                        "type": "string",
                        "description": "Jurisdiction code (ISO 3166-1 alpha-2)"
                    },
                    "transaction_data": {
                        "type": "object",
                        "description": "Transaction data for monitoring analysis"
                    },
                    "symbol": {
                        "type": "string",
                        "description": "Stock symbol for trading pattern analysis"
                    },
                    "period": {
                        "type": "integer",
                        "description": "Analysis period in days (default: 90)"
                    }
                },
                "required": ["check_type"]
            }
        }

    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute compliance check"""
        try:
            check_type = arguments.get("check_type", "all")
            entity_name = arguments.get("entity_name", "")
            entity_type = arguments.get("entity_type", "individual")
            jurisdiction = arguments.get("jurisdiction", "").upper()
            transaction_data = arguments.get("transaction_data")
            symbol = arguments.get("symbol", "").upper()
            period = arguments.get("period", 90)

            result = {
                "timestamp": datetime.now().isoformat(),
                "check_type": check_type,
                "checks_performed": []
            }

            # Determine which checks to run
            if check_type == "all":
                check_types = ["entity_screening", "transaction_monitoring", "regulatory_compliance"]
            else:
                check_types = [check_type]

            # Entity Screening
            if "entity_screening" in check_types:
                if not entity_name:
                    result["entity_screening"] = {"error": "Entity name required for screening"}
                else:
                    result["entity_screening"] = self._entity_screening(
                        entity_name, entity_type, jurisdiction
                    )
                    result["checks_performed"].append("entity_screening")

            # Transaction Monitoring
            if "transaction_monitoring" in check_types:
                if transaction_data:
                    result["transaction_monitoring"] = self._transaction_monitoring(
                        transaction_data
                    )
                    result["checks_performed"].append("transaction_monitoring")
                elif symbol:
                    # Analyze trading patterns from stock data
                    result["transaction_monitoring"] = await self._analyze_trading_patterns(
                        symbol, period
                    )
                    result["checks_performed"].append("transaction_monitoring")
                else:
                    result["transaction_monitoring"] = {
                        "error": "Transaction data or symbol required"
                    }

            # Regulatory Compliance
            if "regulatory_compliance" in check_types:
                result["regulatory_compliance"] = self._regulatory_compliance_check(
                    entity_type, jurisdiction
                )
                result["checks_performed"].append("regulatory_compliance")

            # Overall compliance risk assessment
            result["compliance_assessment"] = self._generate_compliance_assessment(result)

            return result

        except Exception as e:
            return {"error": f"Compliance check failed: {str(e)}"}

    def _entity_screening(
        self, entity_name: str, entity_type: str, jurisdiction: str
    ) -> Dict:
        """Screen entity against sanctions lists and PEP databases"""

        # This is a simplified implementation
        # In production, integrate with OpenSanctions API, OFAC, UN, EU sanctions lists

        risks = []
        risk_score = 0
        max_score = 100

        # Check jurisdiction risk
        jurisdiction_risk = "UNKNOWN"
        if jurisdiction:
            if jurisdiction in self.high_risk_jurisdictions:
                jurisdiction_risk = "HIGH"
                risk_score += 40
                risks.append(f"High-risk jurisdiction: {jurisdiction}")
            else:
                jurisdiction_risk = "LOW"
                risk_score += 5

        # Check for PEP indicators
        pep_risk = "LOW"
        entity_lower = entity_name.lower()
        pep_matches = []

        for keyword in self.pep_keywords:
            if keyword in entity_lower:
                pep_matches.append(keyword)

        if pep_matches:
            pep_risk = "ELEVATED"
            risk_score += 25
            risks.append(f"PEP indicators found: {', '.join(pep_matches)}")

        # Name screening (simplified fuzzy matching simulation)
        # In production: integrate with OpenSanctions API
        sanctions_match = self._check_sanctions_list(entity_name)

        if sanctions_match["match_found"]:
            risk_score += 50
            risks.append(f"Potential sanctions match: {sanctions_match['details']}")

        # Additional risk factors
        risk_factors = {
            "jurisdiction_risk": jurisdiction_risk,
            "pep_risk": pep_risk,
            "sanctions_risk": "HIGH" if sanctions_match["match_found"] else "LOW",
            "entity_type": entity_type
        }

        # Determine overall risk level
        if risk_score >= 60:
            overall_risk = "HIGH"
            recommendation = "REJECT - Enhanced due diligence required. Consider escalation to compliance officer."
        elif risk_score >= 30:
            overall_risk = "MEDIUM"
            recommendation = "REVIEW - Additional verification required before proceeding."
        else:
            overall_risk = "LOW"
            recommendation = "ACCEPT - Standard due diligence procedures apply."

        return {
            "entity_name": entity_name,
            "entity_type": entity_type,
            "jurisdiction": jurisdiction,
            "risk_score": risk_score,
            "max_score": max_score,
            "risk_level": overall_risk,
            "risk_factors": risk_factors,
            "identified_risks": risks if risks else ["No significant risks identified"],
            "recommendation": recommendation,
            "requires_enhanced_dd": risk_score >= 30,
            "screening_timestamp": datetime.now().isoformat(),
            "note": "This is a basic screening. Production systems should integrate with OpenSanctions, OFAC, UN, and EU sanctions lists."
        }

    def _check_sanctions_list(self, entity_name: str) -> Dict:
        """Check entity against sanctions lists (simplified)"""

        # This is a simulation. In production, integrate with:
        # - OpenSanctions API (https://api.opensanctions.org/)
        # - OFAC SDN List
        # - UN Security Council Sanctions List
        # - EU Sanctions List

        # Simulate some known sanctioned entities/patterns
        high_risk_patterns = [
            "north korea", "dprk", "iran", "syria", "crimea", "taliban",
            "isis", "al-qaeda", "hezbollah", "wagner", "kadyrov"
        ]

        entity_lower = entity_name.lower()

        for pattern in high_risk_patterns:
            if pattern in entity_lower:
                return {
                    "match_found": True,
                    "confidence": 0.85,
                    "details": f"Pattern match: {pattern}",
                    "list": "Simulated sanctions list"
                }

        return {
            "match_found": False,
            "confidence": 0,
            "details": "No matches found",
            "list": None
        }

    def _transaction_monitoring(self, transaction_data: Dict) -> Dict:
        """Monitor transaction for suspicious patterns"""

        alerts = []
        risk_score = 0
        max_score = 100

        # Extract transaction details
        amount = transaction_data.get("amount", 0)
        currency = transaction_data.get("currency", "USD")
        sender = transaction_data.get("sender", {})
        receiver = transaction_data.get("receiver", {})
        timestamp = transaction_data.get("timestamp")
        transaction_type = transaction_data.get("type", "unknown")

        # Check for round amounts (structuring indicator)
        if amount > 0 and amount == round(amount, -3):  # Round to nearest 1000
            if amount < 10000:  # Below reporting threshold
                alerts.append({
                    "type": "round_amounts",
                    "severity": "MEDIUM",
                    "description": self.suspicious_patterns["round_amounts"]
                })
                risk_score += 20

        # Check for high-risk jurisdictions
        sender_jurisdiction = sender.get("jurisdiction", "").upper()
        receiver_jurisdiction = receiver.get("jurisdiction", "").upper()

        if (sender_jurisdiction in self.high_risk_jurisdictions or
            receiver_jurisdiction in self.high_risk_jurisdictions):
            alerts.append({
                "type": "high_risk_jurisdiction",
                "severity": "HIGH",
                "description": self.suspicious_patterns["high_risk_jurisdiction"],
                "details": f"Sender: {sender_jurisdiction}, Receiver: {receiver_jurisdiction}"
            })
            risk_score += 40

        # Check transaction timing (if timestamp provided)
        if timestamp:
            try:
                tx_time = pd.to_datetime(timestamp)
                hour = tx_time.hour
                # Off-hours trading (outside 9am-5pm in typical timezone)
                if hour < 6 or hour > 20:
                    alerts.append({
                        "type": "time_pattern",
                        "severity": "LOW",
                        "description": self.suspicious_patterns["time_pattern"],
                        "details": f"Transaction at {hour}:00 hours"
                    })
                    risk_score += 10
            except:
                pass

        # Categorize risk level
        if risk_score >= 50:
            risk_level = "HIGH"
            recommendation = "BLOCK - Suspicious activity detected. File SAR (Suspicious Activity Report)."
        elif risk_score >= 25:
            risk_level = "MEDIUM"
            recommendation = "REVIEW - Additional monitoring required. May require SAR filing."
        else:
            risk_level = "LOW"
            recommendation = "PROCEED - Transaction appears normal."

        return {
            "transaction_id": transaction_data.get("id", hashlib.md5(str(transaction_data).encode()).hexdigest()[:16]),
            "amount": amount,
            "currency": currency,
            "risk_score": risk_score,
            "max_score": max_score,
            "risk_level": risk_level,
            "alerts": alerts if alerts else [{"type": "none", "severity": "NONE", "description": "No suspicious patterns detected"}],
            "recommendation": recommendation,
            "requires_sar": risk_score >= 50,
            "monitoring_timestamp": datetime.now().isoformat()
        }

    async def _analyze_trading_patterns(self, symbol: str, period: int) -> Dict:
        """Analyze trading patterns for suspicious activity"""

        # Load data
        data_file = self.data_dir / f"{symbol}.csv"
        if not data_file.exists():
            return {"error": f"No data available for {symbol}"}

        df = pd.read_csv(data_file, index_col=0, parse_dates=True)
        if df.empty or 'Close' not in df.columns:
            return {"error": f"Invalid data for {symbol}"}

        # Get recent period
        df = df.tail(min(period, len(df)))

        if len(df) < 10:
            return {"error": f"Insufficient data: only {len(df)} days available"}

        alerts = []
        risk_score = 0

        # Calculate daily volume if available
        if 'Volume' in df.columns:
            avg_volume = df['Volume'].mean()
            std_volume = df['Volume'].std()

            # Check for unusual volume spikes
            volume_spikes = df[df['Volume'] > avg_volume + 3 * std_volume]
            if len(volume_spikes) > 0:
                # Convert dates to strings
                spike_dates = [d.strftime('%Y-%m-%d') for d in volume_spikes.index[-3:]] if len(volume_spikes) >= 3 else [d.strftime('%Y-%m-%d') for d in volume_spikes.index]
                alerts.append({
                    "type": "unusual_volume",
                    "severity": "MEDIUM",
                    "description": f"{len(volume_spikes)} days with unusual volume (>3σ)",
                    "dates": spike_dates
                })
                risk_score += 15

        # Check for rapid price movements (potential manipulation)
        returns = df['Close'].pct_change()
        extreme_moves = returns[abs(returns) > 0.10]  # >10% daily moves

        if len(extreme_moves) > period * 0.1:  # >10% of days
            alerts.append({
                "type": "rapid_trading",
                "severity": "HIGH",
                "description": f"High frequency of extreme price moves: {len(extreme_moves)} days >10%",
                "count": len(extreme_moves)
            })
            risk_score += 30

        # Check for layering patterns (rapid price changes followed by reversals)
        if len(returns) > 5:
            reversals = 0
            for i in range(len(returns) - 1):
                if abs(returns.iloc[i]) > 0.05 and abs(returns.iloc[i+1]) > 0.05:
                    if returns.iloc[i] * returns.iloc[i+1] < 0:  # Opposite signs
                        reversals += 1

            if reversals > len(returns) * 0.15:
                alerts.append({
                    "type": "layering",
                    "severity": "HIGH",
                    "description": f"Potential layering detected: {reversals} rapid reversals",
                    "count": reversals
                })
                risk_score += 25

        # Determine risk level
        if risk_score >= 40:
            risk_level = "HIGH"
            recommendation = "Potential market manipulation. Consider reporting to regulatory authorities."
        elif risk_score >= 20:
            risk_level = "MEDIUM"
            recommendation = "Elevated trading risk. Enhanced monitoring recommended."
        else:
            risk_level = "LOW"
            recommendation = "Trading patterns appear normal."

        return {
            "symbol": symbol,
            "period_days": len(df),
            "analysis_start": df.index.min().isoformat(),
            "analysis_end": df.index.max().isoformat(),
            "risk_score": risk_score,
            "risk_level": risk_level,
            "alerts": alerts if alerts else [{"type": "none", "severity": "NONE", "description": "No suspicious patterns detected"}],
            "recommendation": recommendation,
            "statistics": {
                "average_daily_return": round(returns.mean() * 100, 4),
                "volatility": round(returns.std() * np.sqrt(252) * 100, 2),
                "extreme_moves_count": len(extreme_moves),
                "max_daily_gain": round(returns.max() * 100, 2),
                "max_daily_loss": round(returns.min() * 100, 2)
            }
        }

    def _regulatory_compliance_check(self, entity_type: str, jurisdiction: str) -> Dict:
        """Check regulatory compliance requirements"""

        compliance_requirements = []
        recommendations = []

        # DORA (Digital Operational Resilience Act) - EU regulation
        if jurisdiction in ["EU", "GB", "DE", "FR", "IT", "ES", "NL", "BE", "AT", "IE"]:
            compliance_requirements.append({
                "regulation": "DORA",
                "name": "Digital Operational Resilience Act",
                "jurisdiction": "European Union",
                "applies": True,
                "requirements": [
                    "ICT risk management framework",
                    "Incident reporting mechanisms",
                    "Digital operational resilience testing",
                    "Third-party ICT risk management",
                    "Information sharing arrangements"
                ],
                "deadline": "2025-01-17"
            })
            recommendations.append("Ensure DORA compliance by January 17, 2025")

        # Basel III - International banking regulation
        if entity_type == "organization":
            compliance_requirements.append({
                "regulation": "Basel III",
                "name": "Basel III Capital Requirements",
                "jurisdiction": "International",
                "applies": True,
                "requirements": [
                    "Minimum capital ratios (CET1 ≥4.5%, Tier 1 ≥6%, Total ≥8%)",
                    "Leverage ratio ≥3%",
                    "Liquidity Coverage Ratio (LCR) ≥100%",
                    "Net Stable Funding Ratio (NSFR) ≥100%",
                    "Countercyclical capital buffer"
                ],
                "status": "Active"
            })

        # SR 21-14 (US Federal Reserve)
        if jurisdiction == "US":
            compliance_requirements.append({
                "regulation": "SR 21-14",
                "name": "Supervisory Guidance on Model Risk Management",
                "jurisdiction": "United States",
                "applies": True,
                "requirements": [
                    "Model development and implementation",
                    "Model validation (independent review)",
                    "Model governance and controls",
                    "Ongoing monitoring and review",
                    "Documentation and reporting"
                ],
                "status": "Active"
            })
            recommendations.append("Implement model risk management framework per SR 21-14")

        # AML/CFT regulations
        aml_requirements = {
            "regulation": "AML/CFT",
            "name": "Anti-Money Laundering / Counter-Terrorist Financing",
            "jurisdiction": "International (FATF Standards)",
            "applies": True,
            "requirements": [
                "Customer Due Diligence (CDD)",
                "Enhanced Due Diligence (EDD) for high-risk customers",
                "Ongoing monitoring of transactions",
                "Suspicious Activity Reporting (SAR)",
                "Record keeping (≥5 years)",
                "Risk-based approach to AML/CFT",
                "Know Your Customer (KYC) procedures"
            ],
            "status": "Active"
        }
        compliance_requirements.append(aml_requirements)
        recommendations.append("Maintain robust AML/CFT program with regular training")

        # GDPR (if handling EU personal data)
        if jurisdiction in ["EU", "GB", "DE", "FR", "IT", "ES", "NL", "BE", "AT", "IE"]:
            compliance_requirements.append({
                "regulation": "GDPR",
                "name": "General Data Protection Regulation",
                "jurisdiction": "European Union",
                "applies": True,
                "requirements": [
                    "Lawful basis for data processing",
                    "Data subject rights (access, rectification, erasure)",
                    "Data breach notification (<72 hours)",
                    "Privacy by design and default",
                    "Data Protection Impact Assessments (DPIA)"
                ],
                "status": "Active"
            })

        return {
            "entity_type": entity_type,
            "jurisdiction": jurisdiction,
            "applicable_regulations": len(compliance_requirements),
            "compliance_requirements": compliance_requirements,
            "recommendations": recommendations if recommendations else ["Maintain compliance with all applicable regulations"],
            "next_review_date": (datetime.now() + timedelta(days=90)).isoformat(),
            "compliance_officer_action_required": len(compliance_requirements) > 0
        }

    def _generate_compliance_assessment(self, result: Dict) -> Dict:
        """Generate overall compliance risk assessment"""

        total_risk_score = 0
        max_risk_score = 0
        critical_issues = []
        warnings = []
        recommendations = []

        # Entity screening assessment
        if "entity_screening" in result and "error" not in result["entity_screening"]:
            es = result["entity_screening"]
            risk_score = es.get("risk_score", 0)
            total_risk_score += risk_score
            max_risk_score += 100

            if es.get("risk_level") == "HIGH":
                critical_issues.append("High-risk entity identified in screening")
            elif es.get("risk_level") == "MEDIUM":
                warnings.append("Entity requires enhanced due diligence")

            if es.get("requires_enhanced_dd"):
                recommendations.append("Conduct enhanced due diligence before proceeding")

        # Transaction monitoring assessment
        if "transaction_monitoring" in result and "error" not in result["transaction_monitoring"]:
            tm = result["transaction_monitoring"]
            risk_score = tm.get("risk_score", 0)
            total_risk_score += risk_score
            max_risk_score += 100

            if tm.get("requires_sar"):
                critical_issues.append("Suspicious activity requiring SAR filing")

            alerts = tm.get("alerts", [])
            high_severity_alerts = [a for a in alerts if a.get("severity") == "HIGH"]
            if high_severity_alerts:
                warnings.append(f"{len(high_severity_alerts)} high-severity transaction alerts")

        # Regulatory compliance assessment
        if "regulatory_compliance" in result:
            rc = result["regulatory_compliance"]
            req_count = rc.get("applicable_regulations", 0)

            if req_count > 0:
                warnings.append(f"{req_count} regulatory frameworks applicable")
                recommendations.extend(rc.get("recommendations", []))

        # Calculate overall compliance risk
        if max_risk_score > 0:
            compliance_risk_percent = (total_risk_score / max_risk_score) * 100
        else:
            compliance_risk_percent = 0

        # Determine overall status
        if critical_issues:
            overall_status = "CRITICAL"
            action = "IMMEDIATE ACTION REQUIRED"
        elif compliance_risk_percent > 50:
            overall_status = "HIGH_RISK"
            action = "Enhanced monitoring and remediation required"
        elif compliance_risk_percent > 25 or warnings:
            overall_status = "MEDIUM_RISK"
            action = "Additional review and monitoring recommended"
        else:
            overall_status = "LOW_RISK"
            action = "Continue standard compliance procedures"

        return {
            "overall_status": overall_status,
            "compliance_risk_score": round(compliance_risk_percent, 2),
            "action_required": action,
            "critical_issues": critical_issues if critical_issues else ["None"],
            "warnings": warnings if warnings else ["None"],
            "recommendations": recommendations if recommendations else ["Maintain current compliance procedures"],
            "assessment_timestamp": datetime.now().isoformat(),
            "next_review": (datetime.now() + timedelta(days=30)).isoformat()
        }
