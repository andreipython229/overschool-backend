from .box import (
    BoxDetailSerializer,
    BoxPrizeSerializer,
    BoxSerializer,
    PaymentSerializer,
    PrizeDetailSerializer,
    PrizeSerializer,
)
from .payment_methods import (
    ProdamusLinkSerializer,
    SchoolExpressPayLinkSerializer,
    SchoolPaymentMethodSerializer,
)
from .school import (
    SchoolGetSerializer,
    SchoolSerializer,
    SchoolStudentsTableSettingsSerializer,
    SchoolTaskSummarySerializer,
    SchoolUpdateSerializer,
    TariffSerializer,
)
from .school_banner import (
    BannerAcceptSerializer,
    BannerClickSerializer,
    BannerSerializer,
)
from .school_bonus import BonusGetSerializer, BonusSerializer
from .school_branding import SchoolBrandingSerializer
from .school_document import (
    SchoolDocumentsDetailSerializer,
    SchoolDocumentsSerializer,
    SchoolDocumentsUpdateSerializer,
)
from .school_header import (
    SchoolHeaderDetailSerializer,
    SchoolHeaderSerializer,
    SchoolHeaderUpdateSerializer,
)
from .school_newsletter import NewsletterTemplateSerializer
from .school_referral import ReferralClickSerializer, ReferralSerializer
from .school_roles import SchoolNewRoleSerializer
from .SchoolMeetings import SchoolMeetingsSerializer
from .userDomain import DomainSerializer
