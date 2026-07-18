class WorkoutKnowledge:

    _knowledge = {
        "Corrida Fácil": {
            "objective": "Desenvolver a base aeróbia.",
            "adaptations": [
                "Aumento da capacidade aeróbia",
                "Melhora da capilarização muscular",
                "Melhora da economia de corrida",
            ],
            "perception": "Esforço leve, respiração controlada.",
            "errors": [
                "Correr rápido demais",
                "Transformar a rodagem em treino de ritmo",
            ],
        },

        "Longão": {
            "objective": "Desenvolver resistência específica.",
            "adaptations": [
                "Maior resistência muscular",
                "Melhor utilização de gordura como combustível",
                "Maior tolerância ao tempo de esforço",
            ],
            "perception": "Esforço confortável durante grande parte do treino.",
            "errors": [
                "Largar muito rápido",
                "Negligenciar hidratação",
                "Não utilizar estratégia nutricional",
            ],
        },

        "Limiar": {
            "objective": "Elevar o limiar de lactato.",
            "adaptations": [
                "Maior capacidade de sustentar ritmos elevados",
                "Menor acúmulo de lactato",
            ],
            "perception": "Esforço forte, porém controlado.",
            "errors": [
                "Correr acima do ritmo",
                "Transformar o treino em intervalado",
            ],
        },

        "Intervalado": {
            "objective": "Desenvolver o VO₂máx.",
            "adaptations": [
                "Aumento do débito cardíaco",
                "Melhora da potência aeróbia",
                "Maior consumo máximo de oxigênio",
            ],
            "perception": "Esforço elevado durante as repetições.",
            "errors": [
                "Primeiras séries rápidas demais",
                "Recuperação insuficiente",
            ],
        },

        "Repetição": {
            "objective": "Desenvolver velocidade e economia.",
            "adaptations": [
                "Melhora da mecânica",
                "Maior eficiência neuromuscular",
            ],
            "perception": "Esforços curtos e intensos.",
            "errors": [
                "Perder a técnica",
                "Exagerar na intensidade",
            ],
        },
    }

    @classmethod
    def get(cls, workout_name: str):

        return cls._knowledge.get(
            workout_name,
            None,
        )