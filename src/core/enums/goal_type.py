from enum import Enum


class GoalType(Enum):

    FIVE_K = "5 km"

    TEN_K = "10 km"

    FIFTEEN_K = "15 km"

    HALF = "21,1 km"

    MARATHON = "42,2 km"

    ULTRA = "Ultramaratona"

    TRAIL = "Trail"

    HEALTH = "Saúde"

    WEIGHT_LOSS = "Emagrecimento"

    PERFORMANCE = "Performance"

    OTHER = "Outro"

    @classmethod
    def values(cls):

        return [item.value for item in cls]