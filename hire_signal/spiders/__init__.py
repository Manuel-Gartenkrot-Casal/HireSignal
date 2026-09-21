from .ashby import AshbySpider
from .getonbrd import GetonbrdSpider
from .greenhouse import GreenhouseSpider
from .lever import LeverSpider
from .meli import MeliSpider
from .smartrecruiters import SmartRecruitersSpider

ALL_SPIDERS = [
    GreenhouseSpider,
    LeverSpider,
    AshbySpider,
    GetonbrdSpider,
    SmartRecruitersSpider,
    MeliSpider,
]