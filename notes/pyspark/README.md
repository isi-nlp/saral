# Py Spark Notes

Spark is a framework for massive parallelization and in memory computation.

- In memory computation:
  - Makes use of available RAM as cache to combat slower disks
  - For iterative tasks, read once, cache in memory
- Parallelization:
    - Takes advantage of lots of CPUs, if available, for parallelization
    - APIs to easily partition the dataset for parallelization

## Setup

    conda create -n pyspark
    source activate pyspark
    conda install pyspark ipython notebook