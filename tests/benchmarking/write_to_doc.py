from importlib import import_module
from pathlib import Path

from tests.benchmarking.util import Benchmark


def main():
    benchmark_dir = Path(__file__).parent
    target_file = benchmark_dir / "../../doc/source/benchmark.rst"
    with target_file.open('w') as output:
        output.write('=========\nBenchmark\n=========\n')
        for bench_path in benchmark_dir.glob('bench_*.py'):
            mod = import_module('tests.benchmarking.' + bench_path.with_suffix('').name)
            bm: Benchmark = mod.bm
            output.write(bm.rst())


if __name__ == '__main__':
    main()
