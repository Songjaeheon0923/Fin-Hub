"""
Compliance Checker Tool - Check regulatory compliance
"""
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List

from .base_tool import BaseTool


class ComplianceChecker(BaseTool):
    """Tool for checking regulatory compliance"""

    def __init__(self):
        super().__init__(
            tool_id="risk.check_compliance",
            name="Check Compliance",
            description="규제 준수 여부를 확인합니다"
        )

    async def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute compliance check"""
        try:
            # Validate required arguments
            self.validate_arguments(arguments, ["transaction_id"])

            transaction_id = arguments["transaction_id"]
            check_type = arguments.get("check_type", "comprehensive")
            jurisdiction = arguments.get("jurisdiction", "US")
            customer_info = arguments.get("customer_info", {})

            print(f"Checking compliance for transaction: {transaction_id}")

            # Mock compliance check
            compliance_result = await self._check_mock_compliance(
                transaction_id, check_type, jurisdiction, customer_info
            )

            return self.create_success_response(
                data=compliance_result,
                metadata={
                    "check_type": check_type,
                    "jurisdiction": jurisdiction,
                    "compliance_engine": "mock_v1.0",
                    "timestamp": datetime.now().isoformat()
                }
            )

        except Exception as e:
            return await self.handle_error(e, "compliance_check")

    async def get_tool_info(self) -> Dict[str, Any]:
        """Get tool information for MCP schema"""
        return {
            "name": self.tool_id,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": {
                    "transaction_id": {
                        "type": "string",
                        "description": "Unique transaction identifier"
                    },
                    "check_type": {
                        "type": "string",
                        "enum": ["basic", "comprehensive", "aml", "kyc", "sanctions"],
                        "description": "Type of compliance check to perform",
                        "default": "comprehensive"
                    },
                    "jurisdiction": {
                        "type": "string",
                        "enum": ["US", "EU", "UK", "CA", "AU", "SG"],
                        "description": "Regulatory jurisdiction",
                        "default": "US"
                    },
                    "customer_info": {
                        "type": "object",
                        "description": "Customer information for compliance checks",
                        "properties": {
                            "customer_id": {"type": "string"},
                            "name": {"type": "string"},
                            "country": {"type": "string"},
                            "risk_profile": {"type": "string"},
                            "kyc_status": {"type": "string"}
                        }
                    }
                },
                "required": ["transaction_id"]
            }
        }

    async def _check_mock_compliance(self, transaction_id: str, check_type: str,
                                   jurisdiction: str, customer_info: Dict[str, Any]) -> Dict[str, Any]:
        """Mock compliance checking implementation"""

        # Generate mock transaction data
        transaction_amount = random.uniform(1000, 100000)
        transaction_type = random.choice(["transfer", "withdrawal", "deposit", "wire", "crypto"])

        # Perform different compliance checks
        compliance_results = {}

        # AML (Anti-Money Laundering) Check
        aml_result = await self._check_aml_compliance(transaction_amount, transaction_type, customer_info)
        compliance_results["aml"] = aml_result

        # KYC (Know Your Customer) Check
        kyc_result = await self._check_kyc_compliance(customer_info, transaction_amount)
        compliance_results["kyc"] = kyc_result

        # Sanctions Check
        sanctions_result = await self._check_sanctions_compliance(customer_info)
        compliance_results["sanctions"] = sanctions_result

        # Transaction Monitoring
        monitoring_result = await self._check_transaction_monitoring(transaction_amount, transaction_type)
        compliance_results["transaction_monitoring"] = monitoring_result

        # Jurisdiction-specific checks
        jurisdiction_result = await self._check_jurisdiction_compliance(jurisdiction, transaction_amount)
        compliance_results["jurisdiction"] = jurisdiction_result

        # Calculate overall compliance status
        overall_status = await self._calculate_overall_compliance(compliance_results)

        # Generate violations and recommendations
        violations = await self._identify_violations(compliance_results)
        recommendations = await self._generate_compliance_recommendations(violations, overall_status)

        # Generate compliance report
        compliance_report = await self._generate_compliance_report(
            compliance_results, violations, jurisdiction
        )

        return {
            "transaction_id": transaction_id,
            "overall_status": overall_status,
            "compliance_score": round(random.uniform(0.7, 0.98), 3),
            "jurisdiction": jurisdiction,
            "check_timestamp": datetime.now().isoformat(),
            "compliance_checks": {
                "aml": compliance_results["aml"],
                "kyc": compliance_results["kyc"],
                "sanctions": compliance_results["sanctions"],
                "transaction_monitoring": compliance_results["transaction_monitoring"],
                "jurisdiction_specific": compliance_results["jurisdiction"]
            },
            "violations": violations,
            "risk_assessment": {
                "overall_risk": random.choice(["low", "medium", "high"]),
                "risk_factors": await self._identify_risk_factors(compliance_results),
                "risk_score": round(random.uniform(0.1, 0.8), 3)
            },
            "recommendations": recommendations,
            "compliance_report": compliance_report,
            "next_review_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
            "regulatory_requirements": await self._get_regulatory_requirements(jurisdiction)
        }

    async def _check_aml_compliance(self, amount: float, transaction_type: str,
                                  customer_info: Dict[str, Any]) -> Dict[str, Any]:
        """Check AML compliance"""
        violations = []
        score = 0.9

        # Check for large cash transactions
        if amount > 10000 and transaction_type in ["cash", "withdrawal"]:
            violations.append("Large cash transaction requires CTR filing")
            score -= 0.2

        # Check for structuring patterns
        if 9000 <= amount <= 10000:
            violations.append("Potential structuring - amount just below reporting threshold")
            score -= 0.3

        # Check customer risk profile
        customer_risk = customer_info.get("risk_profile", "medium")
        if customer_risk == "high" and amount > 25000:
            violations.append("High-risk customer with large transaction")
            score -= 0.1

        status = "compliant" if score >= 0.7 else "violation"

        return {
            "status": status,
            "score": max(0.1, score),
            "violations": violations,
            "required_actions": [
                "File CTR if amount > $10,000",
                "File SAR if suspicious activity detected",
                "Enhanced due diligence for high-risk customers"
            ],
            "regulations": ["BSA", "USA PATRIOT Act", "FinCEN"]
        }

    async def _check_kyc_compliance(self, customer_info: Dict[str, Any], amount: float) -> Dict[str, Any]:
        """Check KYC compliance"""
        violations = []
        score = 0.9

        kyc_status = customer_info.get("kyc_status", "unknown")
        customer_id = customer_info.get("customer_id", "unknown")

        # Check if KYC is complete
        if kyc_status != "complete":
            violations.append("Incomplete KYC documentation")
            score -= 0.4

        # Check for high-value transactions without enhanced KYC
        if amount > 50000 and kyc_status != "enhanced":
            violations.append("High-value transaction requires enhanced KYC")
            score -= 0.2

        # Check customer identification
        if customer_id == "unknown":
            violations.append("Customer identification required")
            score -= 0.5

        status = "compliant" if score >= 0.7 else "violation"

        return {
            "status": status,
            "score": max(0.1, score),
            "violations": violations,
            "kyc_level": kyc_status,
            "required_documents": [
                "Government-issued ID",
                "Proof of address",
                "Source of funds documentation"
            ],
            "regulations": ["KYC Rule", "CDD Rule"]
        }

    async def _check_sanctions_compliance(self, customer_info: Dict[str, Any]) -> Dict[str, Any]:
        """Check sanctions compliance"""
        violations = []
        score = 1.0

        customer_name = customer_info.get("name", "Unknown")
        customer_country = customer_info.get("country", "Unknown")

        # Mock sanctions screening
        sanctioned_countries = ["Country A", "Country B", "Country C"]  # Mock data
        if customer_country in sanctioned_countries:
            violations.append(f"Customer from sanctioned country: {customer_country}")
            score = 0.0

        # Mock name screening
        if "SANCTIONS" in customer_name.upper():  # Mock trigger
            violations.append("Customer name matches sanctions list")
            score = 0.0

        status = "compliant" if score >= 0.9 else "violation"

        return {
            "status": status,
            "score": score,
            "violations": violations,
            "screening_lists": [
                "OFAC SDN List",
                "UN Security Council List",
                "EU Sanctions List",
                "UK HMT List"
            ],
            "last_screening": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "regulations": ["OFAC", "UN", "EU Sanctions"]
        }

    async def _check_transaction_monitoring(self, amount: float, transaction_type: str) -> Dict[str, Any]:
        """Check transaction monitoring compliance"""
        violations = []
        score = 0.9

        # Check for unusual patterns
        if transaction_type == "crypto" and amount > 10000:
            violations.append("Large cryptocurrency transaction requires enhanced monitoring")
            score -= 0.1

        # Check for rapid transactions
        if random.random() < 0.3:  # Mock: 30% chance of rapid transaction pattern
            violations.append("Rapid succession of transactions detected")
            score -= 0.2

        # Check for round amounts (potential indicator)
        if amount % 1000 == 0 and amount >= 10000:
            violations.append("Round amount transaction - potential indicator")
            score -= 0.1

        status = "compliant" if score >= 0.7 else "violation"

        return {
            "status": status,
            "score": max(0.1, score),
            "violations": violations,
            "monitoring_alerts": len(violations),
            "patterns_detected": [
                "Round amount",
                "High frequency",
                "Unusual timing"
            ] if violations else [],
            "regulations": ["BSA Transaction Monitoring"]
        }

    async def _check_jurisdiction_compliance(self, jurisdiction: str, amount: float) -> Dict[str, Any]:
        """Check jurisdiction-specific compliance"""
        violations = []
        score = 0.9

        jurisdiction_rules = {
            "US": {"reporting_threshold": 10000, "wire_limit": 3000},
            "EU": {"reporting_threshold": 15000, "wire_limit": 1000},
            "UK": {"reporting_threshold": 15000, "wire_limit": 1000},
            "CA": {"reporting_threshold": 10000, "wire_limit": 3000},
            "AU": {"reporting_threshold": 10000, "wire_limit": 1000},
            "SG": {"reporting_threshold": 20000, "wire_limit": 5000}
        }

        rules = jurisdiction_rules.get(jurisdiction, jurisdiction_rules["US"])

        # Check reporting thresholds
        if amount > rules["reporting_threshold"]:
            violations.append(f"Amount exceeds {jurisdiction} reporting threshold")
            score -= 0.1

        status = "compliant" if score >= 0.8 else "violation"

        return {
            "status": status,
            "score": max(0.1, score),
            "violations": violations,
            "jurisdiction": jurisdiction,
            "applicable_thresholds": rules,
            "regulations": [f"{jurisdiction} AML Laws", f"{jurisdiction} Banking Regulations"]
        }

    async def _calculate_overall_compliance(self, results: Dict[str, Any]) -> str:
        """Calculate overall compliance status"""
        violation_count = sum(1 for result in results.values() if result["status"] == "violation")

        if violation_count == 0:
            return "compliant"
        elif violation_count <= 2:
            return "minor_violations"
        else:
            return "major_violations"

    async def _identify_violations(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify all compliance violations"""
        all_violations = []

        for check_type, result in results.items():
            for violation in result.get("violations", []):
                all_violations.append({
                    "type": check_type,
                    "description": violation,
                    "severity": random.choice(["low", "medium", "high"]),
                    "regulation": result.get("regulations", ["Unknown"])[0]
                })

        return all_violations

    async def _generate_compliance_recommendations(self, violations: List[Dict],
                                                 overall_status: str) -> List[str]:
        """Generate compliance recommendations"""
        recommendations = []

        if overall_status == "compliant":
            recommendations.append("Transaction is compliant - proceed with processing")
            recommendations.append("Continue regular monitoring")
            return recommendations

        if any(v["type"] == "aml" for v in violations):
            recommendations.append("File required AML reports (CTR/SAR)")
            recommendations.append("Enhanced transaction monitoring required")

        if any(v["type"] == "kyc" for v in violations):
            recommendations.append("Complete KYC documentation before processing")
            recommendations.append("Request additional customer information")

        if any(v["type"] == "sanctions" for v in violations):
            recommendations.append("BLOCK TRANSACTION - Sanctions violation detected")
            recommendations.append("Report to relevant authorities immediately")

        if any(v["severity"] == "high" for v in violations):
            recommendations.append("Escalate to compliance officer")
            recommendations.append("Consider account restrictions")

        recommendations.append("Document all compliance actions taken")
        recommendations.append("Review and update customer risk profile")

        return recommendations[:6]

    async def _identify_risk_factors(self, results: Dict[str, Any]) -> List[str]:
        """Identify risk factors from compliance results"""
        risk_factors = []

        for check_type, result in results.items():
            if result["score"] < 0.7:
                risk_factors.append(f"{check_type}_violations")

            if result.get("violations"):
                risk_factors.extend([f"{check_type}_{v.lower().replace(' ', '_')}"
                                   for v in result["violations"][:2]])

        return risk_factors[:5]

    async def _generate_compliance_report(self, results: Dict[str, Any],
                                        violations: List[Dict], jurisdiction: str) -> Dict[str, Any]:
        """Generate detailed compliance report"""
        return {
            "report_id": f"CR_{random.randint(100000, 999999)}",
            "generated_at": datetime.now().isoformat(),
            "jurisdiction": jurisdiction,
            "summary": {
                "total_checks": len(results),
                "passed_checks": sum(1 for r in results.values() if r["status"] == "compliant"),
                "failed_checks": sum(1 for r in results.values() if r["status"] == "violation"),
                "total_violations": len(violations)
            },
            "compliance_matrix": {
                check: {
                    "status": result["status"],
                    "score": result["score"],
                    "violations": len(result.get("violations", []))
                }
                for check, result in results.items()
            },
            "regulatory_impact": "high" if len(violations) > 3 else ("medium" if violations else "low"),
            "follow_up_required": len(violations) > 0
        }

    async def _get_regulatory_requirements(self, jurisdiction: str) -> List[str]:
        """Get regulatory requirements for jurisdiction"""
        requirements = {
            "US": [
                "Bank Secrecy Act (BSA) compliance",
                "USA PATRIOT Act requirements",
                "OFAC sanctions screening",
                "FinCEN reporting obligations"
            ],
            "EU": [
                "4th Anti-Money Laundering Directive",
                "Payment Services Directive 2 (PSD2)",
                "General Data Protection Regulation (GDPR)",
                "Markets in Financial Instruments Directive (MiFID II)"
            ],
            "UK": [
                "Money Laundering Regulations 2017",
                "Proceeds of Crime Act 2002",
                "Financial Services and Markets Act 2000",
                "UK Sanctions List compliance"
            ]
        }

        return requirements.get(jurisdiction, requirements["US"])