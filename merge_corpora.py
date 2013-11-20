#!/usr/bin/python

import sys

def main():
  input1 = open(sys.argv[1], "r")
  input2 = open(sys.argv[2], "r")
  output = open(sys.argv[3], "w")

  for line1, line2 in zip(input1, input2):
    line1 = line1.rstrip()
    line2 = line2.rstrip()
    if line1 and line2:
      output.write(" ||| ".join([line1, line2]) + "\n")

if __name__ == "__main__":
  main()
