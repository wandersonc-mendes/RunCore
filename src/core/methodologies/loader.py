import csv
from pathlib import Path


class MethodologyLoader:

    @staticmethod
    def load_csv(filename: str):

        root = (
            Path(__file__)
            .parent.parent.parent
        )

        file = (
            root
            / "resources"
            / "methodologies"
            / filename
        )

        data = {}

        with open(
            file,
            encoding="utf-8",
            newline="",
        ) as csvfile:

            reader = csv.DictReader(csvfile)

            for row in reader:

                vdot = int(row["VDOT"])

                data[vdot] = row

        return data