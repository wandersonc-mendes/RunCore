from core.physiology.pace_service import PaceService


class TrainingStepGenerator:

    @staticmethod
    def for_session(session, vdot):

        easy = TrainingStepGenerator._pace_range(PaceService.easy(vdot))
        marathon = TrainingStepGenerator._pace_range(
            PaceService.marathon(vdot)
        )
        threshold = TrainingStepGenerator._pace_range(
            PaceService.threshold(vdot)
        )
        interval = TrainingStepGenerator._pace_range(
            PaceService.interval(vdot)
        )

        if session.zone == "Interval":
            return [
                TrainingStepGenerator._step(
                    "Aquecimento", 2, easy,
                    "Corra leve e inclua mobilidade antes das repetições.",
                ),
                {
                    "type": "Intervalado",
                    "distance": session.planned_distance,
                    "distance_unit": "m",
                    "repetitions": session.repetitions,
                    "pace_min": interval[0],
                    "pace_max": interval[1],
                    "notes": "Complete cada repetição de forma controlada.",
                    "recovery": "",
                },
                {
                    "type": "Recuperação",
                    "distance": 200,
                    "distance_unit": "m",
                    "repetitions": session.repetitions,
                    "pace_min": "",
                    "pace_max": "",
                    "notes": "Trote leve entre as repetições para recuperar sem parar completamente.",
                    "recovery": "",
                },
                TrainingStepGenerator._step(
                    "Desaquecimento", 2, easy,
                    "Finalize em ritmo bem confortável.",
                ),
            ]

        if session.zone == "Threshold":
            return TrainingStepGenerator._continuous_steps(
                session.planned_distance,
                easy,
                threshold,
                "Mantenha o esforço sustentado, forte e controlado.",
            )

        if session.zone == "Marathon":
            return TrainingStepGenerator._continuous_steps(
                session.planned_distance,
                easy,
                marathon,
                "Ritmo contínuo e econômico; evite acelerar no início.",
            )

        return TrainingStepGenerator._continuous_steps(
            session.planned_distance,
            easy,
            easy,
            "Mantenha uma conversa confortável durante toda a rodagem.",
        )

    @staticmethod
    def _continuous_steps(distance, easy_pace, main_pace, main_note):

        warmup = min(2, max(1, distance * 0.2))
        cooldown = warmup
        main_distance = max(0, distance - warmup - cooldown)

        steps = [
            TrainingStepGenerator._step(
                "Aquecimento", warmup, easy_pace,
                "Comece leve, soltando a passada gradualmente.",
            ),
        ]

        if main_distance:
            steps.append(
                TrainingStepGenerator._step(
                    "Corrida", main_distance, main_pace, main_note,
                )
            )

        steps.append(
            TrainingStepGenerator._step(
                "Desaquecimento", cooldown, easy_pace,
                "Reduza o ritmo e termine relaxado.",
            )
        )

        return steps

    @staticmethod
    def _step(step_type, distance, pace, notes):

        return {
            "type": step_type,
            "distance": round(distance, 1),
            "distance_unit": "km",
            "repetitions": 0,
            "pace_min": pace[0],
            "pace_max": pace[1],
            "notes": notes,
        }

    @staticmethod
    def _pace_range(value):

        minutes, seconds = map(int, value.split(":"))
        total = (minutes * 60) + seconds

        return (
            TrainingStepGenerator._format_pace(total + 8),
            TrainingStepGenerator._format_pace(max(1, total - 8)),
        )

    @staticmethod
    def _format_pace(seconds):

        return f"{seconds // 60:02}:{seconds % 60:02}"
