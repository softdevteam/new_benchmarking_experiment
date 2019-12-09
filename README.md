# The New Benchmarking Experiment

This is a research experiment designed to investigate how large a performance
deviation must be before it can be reliably measured.

## Usage

To fetch the VMs and the benchmarks:
```sh
$ make setup
```

To run using the simple runner (without Krun):

```sh
$ make run-standalone
```

To run using Krun, see the included Krun config file, `experiment.krun`.
