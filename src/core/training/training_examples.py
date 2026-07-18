from core.training.training_builder import (
    TrainingBuilder,
)


class TrainingExamples:

    @staticmethod
    def marathon_progression():

        return (
            TrainingBuilder()

            .warmup(
                distance=2.5,
                pace_min="05:15",
                pace_max="05:20",
                speed_min=11.43,
                speed_max=11.29,
            )

            .run(
                distance=6,
                pace_min="05:00",
                pace_max="05:10",
                speed_min=12.00,
                speed_max=11.61,
            )

            .run(
                distance=5.5,
                pace_min="04:50",
                pace_max="04:59",
                speed_min=12.41,
                speed_max=12.08,
            )

            .cooldown(
                distance=1.0,
                pace_min="05:40",
                pace_max="06:00",
                speed_min=10.59,
                speed_max=10.00,
            )

            .build()
        )