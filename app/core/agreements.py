from dataclasses import dataclass

from app.core.settings import settings


@dataclass(frozen=True)
class AgreementDefinition:
    terms_type: str
    terms_version: str
    terms_title: str
    terms_content_url: str
    is_required: bool


def get_agreement_catalog() -> tuple[AgreementDefinition, ...]:
    return (
        AgreementDefinition(
            "TERMS_OF_SERVICE",
            settings.terms_of_service_version,
            "서비스 이용약관",
            "/terms/service",
            True,
        ),
        AgreementDefinition(
            "PRIVACY_POLICY",
            settings.privacy_policy_version,
            "개인정보 처리방침",
            "/terms/privacy",
            True,
        ),
        AgreementDefinition(
            "IMAGE_ANALYSIS",
            settings.image_analysis_version,
            "이미지 AI 분석 동의",
            "/terms/image-analysis",
            True,
        ),
        AgreementDefinition(
            "MATCHING_INFO",
            settings.matching_info_version,
            "시공자 매칭 정보 제공 동의",
            "/terms/matching-info",
            True,
        ),
    )
