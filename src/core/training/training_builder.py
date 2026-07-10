from core.training.training_step import (
    TrainingStep,
)


class TrainingBuilder:

    def __init__(self):

        self.steps = []

    def add_step(
        self,
        title,
        instruction,
        distance=None,
        duration=None,
        repetitions=None,
        interval_distance=None,
        interval_duration=None,
        pace_min="",
        pace_max="",
        speed_min=None,
        speed_max=None,
        recovery="",
        notes="",
        cadence="",
        incline="",
        heart_rate="",
        terrain="",
    ):

        self.steps.append(
            TrainingStep(
                order=len(self.steps) + 1,
                title=title,
                instruction=instruction,
                distance=distance,
                duration=duration,
                repetitions=repetitions,
                interval_distance=interval_distance,
                interval_duration=interval_duration,
                pace_min=pace_min,
                pace_max=pace_max,
                speed_min=speed_min,
                speed_max=speed_max,
                recovery=recovery,
                notes=notes,
                cadence=cadence,
                incline=incline,
                heart_rate=heart_rate,
                terrain=terrain,
            )
        )

        return self

    def warmup(self, **kwargs):

        return self.add_step(
            title="Aquecimento",
            instruction="Aquecer por",
            **kwargs,
        )

    def run(self, **kwargs):

        return self.add_step(
            title="Corrida",
            instruction="Correr por",
            **kwargs,
        )

    def interval(self, **kwargs):

        return self.add_step(
            title="Intervalado",
            instruction="Executar",
            **kwargs,
        )

    def cooldown(self, **kwargs):

        return self.add_step(
            title="Desaquecimento",
            instruction="Desaquecer por",
            **kwargs,
        )

    def walk(self, **kwargs):

        return self.add_step(
            title="Caminhada",
            instruction="Caminhar por",
            **kwargs,
        )

    def build(self):

        return self.steps