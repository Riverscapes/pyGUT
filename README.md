# pyGUT: Geomorphic Unit Detection in ArcPy


How to use GUTs

## Usage:

```
python main.py step input_xml [--verbose]
```

#### step

Step is which step of gut to run. This is here because sometimes you want to tweak things between tier2 and tier3. The steps are as follows:

1. `all` run everything
2. `evidence` Just run the evidence rasters
3. `tier2` Just run tier2 classification
4. `tier3` Just run tier3 classification 