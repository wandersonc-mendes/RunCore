from dataclasses import dataclass


@dataclass(frozen=True)
class IptResult:

    short_speed: float
    long_speed: float
    ipt_percentage: float
    profile: str
    interpretation: str
    emphasis: str


class IptService:

    PROTOCOLS = (
        {
            "code": "DIST_500_1600",
            "name": "500 m + 1600 m",
            "protocol_type": "distance",
            "short_value": 500,
            "long_value": 1600,
            "input_mode": "time",
        },
        {
            "code": "DIST_1000_2400",
            "name": "1000 m + 2400 m",
            "protocol_type": "distance",
            "short_value": 1000,
            "long_value": 2400,
            "input_mode": "time",
        },
        {
            "code": "DIST_1000_3000",
            "name": "1000 m + 3000 m",
            "protocol_type": "distance",
            "short_value": 1000,
            "long_value": 3000,
            "input_mode": "time",
        },
        {
            "code": "DIST_1000_3200",
            "name": "1000 m + 3200 m",
            "protocol_type": "distance",
            "short_value": 1000,
            "long_value": 3200,
            "input_mode": "time",
        },
        {
            "code": "DIST_1000_5000",
            "name": "1000 m + 5000 m",
            "protocol_type": "distance",
            "short_value": 1000,
            "long_value": 5000,
            "input_mode": "time",
        },
        {
            "code": "TIME_2_5",
            "name": "2 minutos + 5 minutos",
            "protocol_type": "time",
            "short_value": 120,
            "long_value": 300,
            "input_mode": "distance",
        },
        {
            "code": "TIME_4_12",
            "name": "4 minutos + 12 minutos",
            "protocol_type": "time",
            "short_value": 240,
            "long_value": 720,
            "input_mode": "distance",
        },
    )

    @classmethod
    def calculate(
        cls,
        protocol_type,
        short_value,
        long_value,
        short_result,
        long_result,
    ):
        cls._validate_positive(
            short_value=short_value,
            long_value=long_value,
            short_result=short_result,
            long_result=long_result,
        )

        if protocol_type == "distance":
            short_speed = cls._distance_speed(
                distance_m=short_value,
                time_seconds=short_result,
            )
            long_speed = cls._distance_speed(
                distance_m=long_value,
                time_seconds=long_result,
            )
        elif protocol_type == "time":
            short_speed = cls._time_speed(
                distance_m=short_result,
                duration_seconds=short_value,
            )
            long_speed = cls._time_speed(
                distance_m=long_result,
                duration_seconds=long_value,
            )
        else:
            raise ValueError("Tipo de protocolo IPT invÃ¡lido.")

        ipt_percentage = (
            1 - long_speed / short_speed
        ) * 100

        profile, interpretation, emphasis = cls.classify(
            ipt_percentage
        )

        return IptResult(
            short_speed=round(short_speed, 2),
            long_speed=round(long_speed, 2),
            ipt_percentage=round(ipt_percentage, 2),
            profile=profile,
            interpretation=interpretation,
            emphasis=emphasis,
        )

    @staticmethod
    def classify(ipt_percentage):

        if ipt_percentage < 9:
            return (
                "Resistente",
                "O atleta apresenta boa capacidade de sustentar a velocidade "
                "entre os esforÃ§os curto e longo.",
                "Preservar a resistÃªncia e desenvolver velocidade e potÃªncia.",
            )

        if ipt_percentage <= 11:
            return (
                "Equilibrado",
                "O atleta apresenta equilÃ­brio entre velocidade e capacidade "
                "de sustentaÃ§Ã£o.",
                "Distribuir os estÃ­mulos entre velocidade, limiar e resistÃªncia.",
            )

        return (
            "Potente",
            "O atleta apresenta maior expressÃ£o de velocidade no esforÃ§o curto "
            "em relaÃ§Ã£o Ã  capacidade de sustentaÃ§Ã£o.",
            "Desenvolver ritmos sustentados, limiares e resistÃªncia especÃ­fica.",
        )

    @staticmethod
    def _distance_speed(distance_m, time_seconds):
        return distance_m / time_seconds * 3.6

    @staticmethod
    def _time_speed(distance_m, duration_seconds):
        return distance_m / duration_seconds * 3.6

    @staticmethod
    def _validate_positive(**values):
        if any(value <= 0 for value in values.values()):
            raise ValueError(
                "DistÃ¢ncias, duraÃ§Ãµes e resultados devem ser maiores que zero."
            )