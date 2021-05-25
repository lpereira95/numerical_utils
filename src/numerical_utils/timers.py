import os
import glob
import re
import statistics
import time
import json

from matplotlib import pyplot as plt

# TODO: change name (do not forget about dependencies)
# TODO: probably this should go to other lib (numerical_utils or utils)


def load_timer(filename):
    with open(filename, 'r') as file:
        info = json.load(file)

    Timer_ = Timer if 'iter_time' in info.keys() else TimerForIterations

    return Timer_()._update(info)


class Timer:
    def __init__(self, name='', description=''):
        self.name = name
        self.description = description
        # empty initializations
        self._start_time = None
        self._end_time = None

    def start(self):
        self._start_time = time.perf_counter()

    def stop(self):
        self._end_time = time.perf_counter()

    @property
    def total_time(self):
        return self._end_time - self._start_time

    def get_info(self):
        info = {'name': self.name,
                'description': self.description,
                '_start_time': self._start_time,
                '_end_time': self._end_time}

        return info

    def dump(self, filename):

        info = self.get_info()

        with open(filename, 'w') as file:
            json.dump(info, file, indent=4)

    def load(self, filename):
        with open(filename, 'r') as file:
            info = json.load(file)

        return self._update(info)

    def _update(self, info):
        for key, value in info.items():
            setattr(self, key, value)

        return self


class TimerForIterations(Timer):

    def __init__(self, name='', description=''):
        super().__init__(name, description)
        # empty initiatizations
        self.iter_time = []
        self._start_time_iter = None

    def start_iter(self):
        self._start_time_iter = time.perf_counter()

    def stop_iter(self):
        self.iter_time.append(time.perf_counter() - self._start_time_iter)
        self._start_time_iter = None

    def get_iteration_times(self):
        return self.iter_time

    def _append_info(self):

        info = {'iter_time': self.iter_time}

        return info

    def get_info(self):

        info = super().get_info()
        info.update(self._append_info())

        return info


# TODO: create statistics
# TODO: create time bar plotter (including comparisons) - check f3dasm

# TODO: rething this plotters

class TimePlotter:

    def __init__(self, timers, x=None):
        '''
        Parameters
        ----------
        x : list
            Corresponding `x` value for each timer (e.g. number of nodes).
        '''
        self.timers = timers
        self.update_x(x)

    def update_x(self, x):
        if x is None:
            x = [0 for _ in self.timers]
        self.x = x

    def plot_total_times(self, ax=None, add_legend=False, ylabel='Total time /s'):
        ax = self._get_ax(ax)

        for timer, xx in zip(self.timers, self.x):
            ax.scatter(xx, timer.total_time, label=timer.name)

        ax.set_ylabel(ylabel)

        if add_legend:
            ax.legend()

        return ax

    def _get_ax(self, ax):
        if ax is None:
            _, ax = plt.subplots()

        return ax


class TimePlotterForIterations(TimePlotter):

    def __init__(self, timers, x=None):
        super().__init__(timers, x)

    def plot_iter(self, ax=None, add_legend=False):
        ax = self._get_ax(ax)

        for timer in self.timers:
            iter_times = timer.get_iteration_times()
            iters = [i for i in range(len(iter_times))]

            ax.plot(iters, iter_times, label=timer.name)

        ax.set_xlabel('Iteration number')
        ax.set_ylabel("Time /s")

        if add_legend:
            ax.legend()

        return ax


# TODO: it should work fine within timeplotter; how to incorporate iterations?

# TODO: compute efficiency

class ParallelTimerArray:
    '''
    Container for timers that worked in parallel.
    '''

    def __init__(self, timers=None, name='', description=''):
        self.name = ''
        self.description = ''
        self.timers = timers if timers is not None else {}

        # key regex
        self.cpu_regex = re.compile(r'(\d{1,6})(?:.json)')

    def _get_filenames(self, path):
        '''Assumes all json files are timers. If not, you should explicitly
        specify filenames when loading.
        '''
        filenames = []
        for name in glob.glob(os.path.join(path, f'*.json')):
            filenames.append(name)

        return sorted(filenames, key=lambda x: self._get_cpu(os.path.split(x)[-1]))

    def _get_cpu(self, filename):
        return int(self.cpu_regex.search(filename).group(1))

    def load(self, path='.', filenames=None):

        if filenames is None:
            filenames = self._get_filenames(path)

        for filename in filenames:
            cpu_num = self._get_cpu(filename)
            self.timers[cpu_num] = load_timer(filename)

        return self

    def _collect_total_times(self):
        return [timer.total_time for timer in self.timers.values()]

    @property
    def total_cpu_time(self):
        return sum(self._collect_total_times())

    @property
    def total_time(self):
        '''Retrieves the time of the cpu that took longer
        '''
        return max(self._collect_total_times())

    @property
    def mean_time(self):
        return statistics.mean(self._collect_total_times())
