from .box import BoxViewSet, PrizeViewSet
from .school import (
    AddPaymentMethodViewSet,
    ProdamusPaymentLinkViewSet,
    SchoolPaymentLinkViewSet,
    SchoolStudentsTableSettingsViewSet,
    SchoolTasksViewSet,
    SchoolViewSet,
    TariffViewSet,
)
from .school_banner import BannerViewSet
from .school_bonus import BonusViewSet
from .school_branding import SchoolByDomainView
from .school_document import SchoolDocumentViewSet
from .school_header import SchoolHeaderViewSet
from .school_newsletter import NewsletterTemplateViewSet
from .school_referral import (
    ReferralClickRedirectView,
    ReferralClickViewSet,
    ReferralViewSet,
)
from .school_roles import SchoolNewRoleViewSet
from .schoolMeetings import SchoolMeetingsViewSet
from .userDomain import (
    ConfiguredDomainViewSet,
    DomainViewSet,
    UnconfiguredDomainViewSet,
)
