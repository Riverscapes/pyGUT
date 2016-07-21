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


### Where to find thing:

* `main.py` This is what you run. It's just the run logic. All it does is read arguments and put functions in the right order.
* `gutlog.py` This is our logging library. Writes all the log files.
* `grainsizecalc.py` James wrote this for me so we can get the D50/D84 etc.
* `fns.py` The guts of gut. This is where the actual arcpy lives. It's pretty long
* `xml/inputs_template.xml` This is a sample input file. Metadata gets passed through to the output.