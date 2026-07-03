from enum import Enum


class AthleteStatus(Enum):

    ACTIVE = "Ativo"

    INACTIVE = "Inativo"

    PAUSED = "Pausado"

    INJURED = "Lesionado"

    FINISHED = "Encerrado"

    @classmethod
    def values(cls):

        return [item.value for item in cls]