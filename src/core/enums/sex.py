from enum import Enum


class Sex(Enum):

    MALE = "Masculino"

    FEMALE = "Feminino"

    OTHER = "Outro"

    @classmethod
    def values(cls):

        return [item.value for item in cls]