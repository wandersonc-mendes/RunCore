from core.methodologies.base import (
    TrainingMethodology,
)


class JackDanielsMethodology(
    TrainingMethodology
):

    def __init__(self):

        self.table = {
            30: {
                "E": "08:00",
                "M": "07:20",
                "T": "06:55",
                "I": "06:25",
                "R": "06:10",
            },
            40: {
                "E": "06:30",
                "M": "05:55",
                "T": "05:35",
                "I": "05:05",
                "R": "04:50",
            },
            50: {
                "E": "05:10",
                "M": "04:40",
                "T": "04:22",
                "I": "03:58",
                "R": "03:45",
            },
            60: {
                "E": "04:25",
                "M": "03:58",
                "T": "03:43",
                "I": "03:25",
                "R": "03:15",
            },
        }

    def nearest(self, vdot):

        return min(
            self.table.keys(),
            key=lambda x: abs(x - vdot),
        )

    def _get(self, vdot, key):

        v = self.nearest(vdot)

        return self.table[v][key]

    def easy(self, vdot):

        return self._get(vdot, "E")

    def marathon(self, vdot):

        return self._get(vdot, "M")

    def threshold(self, vdot):

        return self._get(vdot, "T")

    def interval(self, vdot):

        return self._get(vdot, "I")

    def repetition(self, vdot):

        return self._get(vdot, "R")