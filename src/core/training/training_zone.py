from enum import Enum


class TrainingZone(Enum):

    EASY = "Easy"

    MARATHON = "Marathon"

    THRESHOLD = "Threshold"

    INTERVAL = "Interval"

    REPETITION = "Repetition"

    @classmethod
    def values(cls):
        return [item.value for item in cls]