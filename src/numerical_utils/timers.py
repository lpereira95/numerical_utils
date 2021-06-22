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
        # TODO: allow restart (create list with start and stop)
        self.name = name
        self.description = description
        self.total_times = []
        # empty initializations
        self._start_time = None

    def start(self):
        self._start_time = time.perf_counter()

    def stop(self):
        self.total_times.append(time.perf_counter() - self._start_time)

    @property
    def total_time(self):
        return sum(self.total_times)

    def get_info(self):
        info = {'name': self.name,
                'description': self.description,
                'total_times': self.total_times,
                }

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


def plot_var(x, timers, var_name='total_time', y_label='Total time /s',
             linestyle='--', marker='x', **kwargs):

    y = [getattr(timer, var_name) for timer in timers]

    return plot(x, y, y_label=y_label, linestyle=linestyle, marker=marker, **kwargs)


def plot(x, y, ax=None, scale='log', x_label=None, y_label=None, **kwargs):
    if ax is None:
        _, ax = plt.subplots()

    ax.plot(x, y, **kwargs)

    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)

    ax.set_xscale(scale)
    ax.set_yscale(scale)

    return ax


# TODO: create statistics
# TODO: create time bar plotter (including comparisons) - check f3dasm


# TODO: create plot for iterations
# TODO: create plot for benchmarks (or update existing one)?


# TODO: it should work fine within timeplotter; how to incorporate iterations?

# TODO: compute efficiency

class ParallelTimerArray:
    '''
    Timer composed of timers that worked in parallel.
    '''
    # TODO: think about inheritance

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
        filenames = [name for name in glob.glob(os.path.join(path, '*.json'))]

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

    @property
    def n_cpus(self):
        return len(self.timers.keys())


class BenchmarkTimerArray:
    '''
    # TODO: review and complete
    '''
    # TODO: some kind of loader from files? (hard to generalize...) - load by infer

    def __init__(self, timers):
        self.timers = timers

    def __iter__(self):
        return iter(self.timers)

    def _get_single_cpu_timer(self):
        for timer in self.timers:
            if timer.n_cpus == 1:
                return timer

    def compute_efficiencies(self):
        total_time_single = self._get_single_cpu_timer().total_time
        return [total_time_single / timer.total_cpu_time for timer in self.timers]

    def plot_total_times(self, x, ax=None):
        return plot_var(x, self.timers, var_name='total_time', ax=ax)

    def plot_efficiencies(self, x, ax=None):
        return plot_var(x, y=self.compute_efficiencies(),
                        y_label='Efficiency', ax=ax)

    def plot(self, ax=None):
        ax = self.plot_total_times(ax)
        ax.yaxis.label.set_color(ax.get_lines()[0].get_color())
        ax2 = ax.twinx()
        ax2._get_lines.get_next_color()
        self.plot_efficiencies(ax2)
        ax2.yaxis.label.set_color(ax2.get_lines()[0].get_color())
        return ax, ax2
