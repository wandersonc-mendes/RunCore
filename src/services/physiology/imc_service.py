class ImcService:
    """Serviço responsável pelos cálculos relacionados ao IMC."""

    @staticmethod
    def calculate(weight: float, height: float) -> float:

        if height <= 0:
            return 0

        return weight / (height ** 2)

    @staticmethod
    def classification(imc: float) -> str:

        if imc < 18.5:
            return "Baixo peso"

        if imc < 25:
            return "Peso normal"

        if imc < 30:
            return "Sobrepeso"

        if imc < 35:
            return "Obesidade I"

        if imc < 40:
            return "Obesidade II"

        return "Obesidade III"