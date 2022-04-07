import math
import sys
from datetime import datetime
from typing import Callable

from PySide6.QtCore import QObject, Signal, Slot, QThread
from PySide6.QtWidgets import QApplication
from mouseapp.model.main_models import MainModel
from mouseapp.model.utils import BackgroundTask


def warn_user(model: MainModel, message: str):
    warning_to_time = model.application_model.warning_to_time
    warning_delta = model.application_model.min_time_between_warnings
    if (message not in warning_to_time or
            datetime.now() - warning_to_time[message] > warning_delta):
        model.application_model.text_warning(message)
    warning_to_time[message] = datetime.now()


def run_background_task(main_model: MainModel,
                        task: Callable,
                        can_be_stopped: bool,
                        *args,
                        **kwargs) -> BackgroundTask:
    """Run `task` in the background.

    Creates a worker in a separate thread and starts it. If `BackgroundTask` is
    not needed, the returned value can be ignored as task's reference is saved
    in `ApplicationModel`.
    """
    # Remove finished threads
    main_model.application_model.background_tasks -= _get_finished_tasks(main_model)

    class Worker(QObject):
        finished = Signal()

        def __init__(self, task, *args, **kwargs):
            super(Worker, self).__init__()
            self.task = task
            self.args = args
            self.kwargs = kwargs

        @Slot()
        def run(self):
            try:
                self.task(*self.args, **self.kwargs)
            except:  # noqa
                # qt probabli uses exec to change execution context,
                # so we grab execution info to sprint stacktrace
                # otherwise tasks will fail silently
                (err_type, value, traceback) = sys.exc_info()
                sys.excepthook(err_type, value, traceback)
                raise
            finally:
                self.finished.emit()

    thread = QThread()
    worker = Worker(task, *args, **kwargs)

    worker.moveToThread(thread)

    # Connect signals
    thread.started.connect(worker.run)
    worker.finished.connect(thread.quit)
    worker.finished.connect(worker.deleteLater)
    thread.finished.connect(thread.deleteLater)

    if can_be_stopped:
        background_task = BackgroundTask(thread=thread,
                                         worker=worker,
                                         kill_signal=worker.finished)
    else:
        background_task = BackgroundTask(thread=thread, worker=worker, kill_signal=None)

    thread.start()

    # Save task's reference
    main_model.application_model.background_tasks.add(background_task)

    return background_task


def _get_finished_tasks(main_model):
    finished_tasks = set()
    for task in main_model.application_model.background_tasks:
        try:
            if task.thread.isFinished():
                finished_tasks.add(task)
        except RuntimeError:
            # Internal C++ object (PySide6.QtCore.QThread) already deleted.
            finished_tasks.add(task)
    return finished_tasks


def process_qt_events(receiver: QObject):
    QApplication.processEvents()
    # Process `DeferredDelete` event
    QApplication.sendPostedEvents(receiver, 52)


def float_convert(word: str) -> float:
    """Clean `word` and convert it to a finite float."""
    result = float(word.replace(",", "."))
    if math.isinf(result):
        raise ValueError(f"could not convert string to float: '{word}'")
    return result
