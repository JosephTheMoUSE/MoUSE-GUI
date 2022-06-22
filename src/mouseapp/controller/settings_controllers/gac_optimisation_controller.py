import os
import sys
import warnings

import ray
from ray import tune

import mouse.segmentation.optimisation
from mouse.utils import data_util
from mouse.utils.metrics import Metric
from mouseapp.controller.denoising_controller import apply_denoising
from mouseapp.controller.utils import (
    run_background_task,
    float_convert,
    process_qt_events,
)
from mouseapp.model.main_models import MainModel
from mouseapp.model.settings.utils import OptimisationResult, Denoising


class _OptimisationCallback(tune.Callback):

    def __init__(self, model: MainModel):
        self.model = model
        self.metric_name = model.settings_model.gac_model.metric
        self.last_iter = 0
        self.total_iters = (model.settings_model.gac_model.optimisation_random_iters +
                            model.settings_model.gac_model.optimisation_iters)
        self.model.settings_model.gac_model.progressbar_iter = 0

    def on_trial_result(self, iteration, trials, trial, result, **info):
        gac_model = self.model.settings_model.gac_model
        self.last_iter += 1
        self.model.settings_model.gac_model.progressbar_iter = int(
            self.last_iter / self.total_iters * 100)

        threshold = round(
            mouse.segmentation.threshold_from_latent(
                result["config"]["_balloon_latent"]),
            3)
        balloon = round(
            mouse.segmentation.balloon_from_latent(result["config"]["_balloon_latent"]),
            3)
        optimisation_result = OptimisationResult(
            metric_name=self.metric_name,
            metric=result["score"],
            precision=result["precision"],
            recall=result["recall"],
            box_count=result["box_count"],
            sigma=round(result["config"]["sigma"], 3),
            iters=int(result["config"]["iterations"]),
            balloon=balloon,
            threshold=round(threshold, 3),
            flood_threshold=round(result["config"]["flood_threshold"], 3),
            smoothing=int(result["config"]["smoothing"]),
        )

        if (gac_model.optimisation_best is None or
                gac_model.optimisation_best < optimisation_result):
            gac_model.optimisation_best = optimisation_result
        gac_model.optimisation_results = gac_model.optimisation_results + [
            optimisation_result
        ]


class _OptimisationQtCallback(tune.Callback):

    def __init__(self, model: MainModel):
        self.model = model

    def on_trial_result(self, iteration, trials, trial, result, **info):
        process_qt_events(self.model.settings_model.gac_model.background_task.worker)


def run_optimisation(model: MainModel):
    gac_model = model.settings_model.gac_model
    if not gac_model.optimisation_mutex.tryLock():
        return
    gac_model.optimisation_allowed = False

    spectrogram_data = model.spectrogram_model.spectrogram_data
    spectrogram_boxes = list(
        map(
            lambda x: x.to_squeak_box(spectrogram_data),
            model.spectrogram_model.annotation_table_model.annotations,
        ))

    spec, ground_truth = data_util.clip_spec_and_boxes(
        spec=spectrogram_data,
        boxes=spectrogram_boxes,
        t_start=gac_model.start_time,
        t_end=gac_model.end_time
    )
    gac_model.optimisation_box_count = len(ground_truth)

    chosen_denoising = model.settings_model.chosen_denoising_method
    if chosen_denoising != Denoising.NO_FILTER:
        denoised_spec = apply_denoising(model, spec)
    else:
        denoised_spec = spec

    use_ray = True
    if 'win' in sys.platform:
        # When the app is packaged ray can't be used due to multithreading problems.
        use_ray = False

    def optimise():
        try:
            os.environ["TUNE_DISABLE_SIGINT_HANDLER"] = "1"
            mouse.segmentation.optimisation.optimise_gac(
                spec=denoised_spec,
                ground_truth=ground_truth,
                metric=gac_model.metric,
                threshold_metric=gac_model.metric_threshold,
                num_samples=gac_model.optimisation_iters +
                gac_model.optimisation_random_iters,
                random_search_steps=gac_model.optimisation_random_iters,
                max_concurrent=gac_model.max_concurrent,
                alpha=gac_model.alpha,
                beta=gac_model.beta,
                callbacks=[
                    _OptimisationCallback(model=model),
                    _OptimisationQtCallback(model=model),
                ],
                use_ray=use_ray,
            )
        finally:
            gac_model.optimisation_mutex.unlock()
            gac_model.optimisation_allowed = True
            model.settings_model.gac_model.progressbar_exists = False
            os.putenv("TUNE_DISABLE_SIGINT_HANDLER", "0")
            ray.shutdown()

    task = run_background_task(main_model=model, task=optimise, can_be_stopped=False)
    model.settings_model.gac_model.background_task = task
    model.settings_model.gac_model.progressbar_exists = True


def autoconfigure_gac(model: MainModel):
    gac_model = model.settings_model.gac_model

    gac_model.smoothing = gac_model.optimisation_best.smoothing
    gac_model.iterations = gac_model.optimisation_best.iters
    gac_model.flood_threshold = gac_model.optimisation_best.flood_threshold
    gac_model.balloon = gac_model.optimisation_best.balloon
    gac_model.threshold = gac_model.optimisation_best.threshold
    gac_model.sigma = gac_model.optimisation_best.sigma


def set_optimisation_time_start(model: MainModel, value: str):
    _value = float_convert(value)
    _value = min(_value, model.settings_model.gac_model.end_time)
    model.settings_model.gac_model.start_time = _value


def set_optimisation_time_end(model: MainModel, value: str):
    _value = float_convert(value)
    _value = max(_value, model.settings_model.gac_model.start_time)
    model.settings_model.gac_model.end_time = _value


def set_optimisation_iters(model: MainModel, value: str):
    _value = int(float_convert(value))
    _value = max(_value, 1)
    model.settings_model.gac_model.optimisation_iters = _value


def set_optimisation_random_iters(model: MainModel, value: str):
    _value = int(float_convert(value))
    _value = max(_value, 1)
    model.settings_model.gac_model.optimisation_random_iters = _value


def set_beta(model: MainModel, value: str):
    _value = float_convert(value)
    _value = max(_value, 0)
    model.settings_model.gac_model.beta = _value


def set_metric(model: MainModel, value: str):
    if value[0].lower() == "f":
        model.settings_model.gac_model.metric = Metric.F_BETA
    elif "intersection" in value.lower():
        model.settings_model.gac_model.metric = Metric.IOU
    else:
        warnings.warn(f"{value} is not a name of a correct metric!")
