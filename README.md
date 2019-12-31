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

When running with Krun, the experiment directory will need to be writable by
the `krun` user. Do this by changing the experiment directory to mode 7777.
Don't be tempted to grant user/group ownership to the `krun` user: we can't
guarantee it will get the same UID and GID every time it is created.
