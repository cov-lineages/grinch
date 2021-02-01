# grinch

global report investigating novel coronavirus haplotypes

```
usage: grinch -i <config.yaml> [options]

optional arguments:
  -h, --help            show this help message and exit

input output options:
  -i CONFIG, --config CONFIG
                        Input config file
  -j JSON, --json JSON  Input json file
  --outdir OUTDIR       Output directory. Default: current working directory
  -o OUTPUT_PREFIX, --output-prefix OUTPUT_PREFIX
                        Output prefix. Default: grinch

misc options:
  --tempdir TEMPDIR     Specify where you want the temporary stuff to go
                        Default: $TMPDIR
  --no-temp             Output all intermediate files
  --verbose             Print lots of stuff to screen
  --no-force            Dont force run rules
  -t THREADS, --threads THREADS
                        Number of threads
  -v, --version         show program's version number and exit
```
