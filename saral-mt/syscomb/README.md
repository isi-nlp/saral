# fallback

`fallback.py` script accepts two files, typically outputs from two MT systems where one
 is main MT (`--hyp` argument) and the other is fallback MT (the `--fallback` argument)
 It copies `hyp` to output (`--out` argument, default is STDOUT), except
 when the `hyp` is too short or too long (relative to source length (`--src` argument).
 In that case, it uses output from `fallback` instead of `hyp`.
  The short and long threshold can be controlled using `--threshold` parameter.



 #### Example

```bash
data=$PWD/testdata
python fallback.py -s $data/src.txt --hyp $data/hyp.txt -f $data/fallback.txt -t 0.4
```