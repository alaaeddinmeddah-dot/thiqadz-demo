from dataclasses import dataclass
from datetime import UTC, datetime
from app.models.entities import Order, OrderStatus, RiskLevel
from app.services.phone import is_valid_algerian_phone


@dataclass
class CustomerHistory:
    total_orders: int = 0
    delivered: int = 0
    refused: int = 0
    cancelled: int = 0
    recent_same_pending: int = 0


@dataclass
class RiskEvaluation:
    score: int
    risk_level: RiskLevel
    recommendation: str
    reasons: list[str]
    created_at: datetime


class RuleBasedRiskScorer:
    def evaluate(self, order: Order, history: CustomerHistory) -> RiskEvaluation:
        score = 72
        reasons: list[str] = []

        if not is_valid_algerian_phone(order.phone):
            score -= 35
            reasons.append("رقم الهاتف غير صالح أو لا يبدو رقمًا جزائريًا.")
        else:
            reasons.append("رقم الهاتف الجزائري بصيغة صحيحة.")

        if order.is_confirmed:
            score += 12
            reasons.append("تم تأكيد الطلب مع العميل.")
        else:
            score -= 18
            reasons.append("الطلب غير مؤكد.")

        if order.contact_attempts >= 3 and not order.is_confirmed:
            score -= 14
            reasons.append("عدة محاولات اتصال بدون تأكيد.")
        elif order.contact_attempts == 0 and not order.is_confirmed:
            score -= 5
            reasons.append("لم يتم الاتصال بالعميل بعد.")

        if order.amount_dzd >= 25000:
            score -= 12
            reasons.append("قيمة الطلب مرتفعة وتحتاج تحققًا إضافيًا.")
        elif order.amount_dzd >= 12000:
            score -= 6
            reasons.append("قيمة الطلب متوسطة إلى مرتفعة.")
        else:
            score += 3
            reasons.append("قيمة الطلب ضمن نطاق منخفض المخاطر.")

        if history.total_orders:
            reasons.append(f"لدى العميل {history.total_orders} طلبات سابقة في النظام.")
        if history.delivered:
            score += min(18, history.delivered * 6)
            reasons.append(f"العميل لديه {history.delivered} طلبات سابقة ناجحة.")
        if history.refused:
            score -= min(30, history.refused * 15)
            reasons.append(f"هناك {history.refused} طلبات مرفوضة سابقة لهذا الرقم.")
        if history.cancelled:
            score -= min(12, history.cancelled * 6)
            reasons.append(f"هناك {history.cancelled} طلبات ملغاة سابقة.")
        if history.recent_same_pending:
            score -= 10
            reasons.append("يوجد طلب مشابه حديث لنفس الرقم وربما يكون تكرارًا.")

        score = max(0, min(100, score))
        if score >= 70:
            level = RiskLevel.low
            recommendation = "آمن للإرسال مع متابعة عادية."
        elif score >= 45:
            level = RiskLevel.medium
            recommendation = "يفضل تأكيد إضافي قبل الإرسال."
        else:
            level = RiskLevel.high
            recommendation = "خطر مرتفع: لا ترسل قبل تحقق واضح من العميل."

        return RiskEvaluation(score, level, recommendation, reasons, datetime.now(UTC).replace(tzinfo=None))
