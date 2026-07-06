from core.methodologies.jack_daniels import (
    JackDanielsMethodology,
)


class MethodologyFactory:

    @staticmethod
    def create(name="jack_daniels"):

        if name == "jack_daniels":
            return JackDanielsMethodology()

        raise ValueError(
            f"Metodologia '{name}' não encontrada."
        )