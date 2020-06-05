#!/usr/bin/env bash
# capitalize first alphabetic letter and none else
awkg -F '\n' "
chars = list(R0)
for i, ch in enumerate(chars):
  if ch.isalpha():
    chars[i] = ch.upper()
    break
line = ''.join(chars)
print(line)
"
