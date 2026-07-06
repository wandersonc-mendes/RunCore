from core.methodologies.jack_daniels import (
    JackDanielsMethodology,
)


class PaceService:

    _methodology = JackDanielsMethodology()

    @classmethod
    def easy(cls, vdot):

        return cls._methodology.easy(vdot)

    @classmethod
    def marathon(cls, vdot):

        return cls._methodology.marathon(vdot)

    @classmethod
    def threshold(cls, vdot):

        return cls._methodology.threshold(vdot)

    @classmethod
    def interval(cls, vdot):

        return cls._methodology.interval(vdot)

    @classmethod
    def repetition(cls, vdot):

        return cls._methodology.repetition(vdot)