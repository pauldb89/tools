#!/usr/bin/python

import string
import sys

def main():
  input = open(sys.argv[1], "r")
  output1 = open(sys.argv[2], "w")
  output2 = open(sys.argv[3], "w")

  for line in input:
    sentences = string.split(line.rstrip(), " ||| ")
    output1.write(sentences[0] + "\n")
    output2.write(sentences[1] + "\n")

if __name__ == "__main__":
  main()
