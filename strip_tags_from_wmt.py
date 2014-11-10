#!/usr/bin/python

"""
Strips XML tags from WMT test data.
"""

from optparse import OptionParser
import xml.etree.ElementTree as ET

def main():
  parser = OptionParser()
  parser.add_option("-i", "--input", dest="input", help="Input file")
  parser.add_option("-o", "--output", dest="output", help="Output file")
  options, _ = parser.parse_args()

  raw_data = open(options.input).read()

  escaped_data = raw_data.replace("&", "&amp;")

  tree = ET.fromstring(escaped_data)
  data = ET.tostring(tree, encoding="utf8", method="text")

  # Remove blank lines.
  sentences = filter(None, data.strip().split("\n"))

  f = open(options.output, "w")
  for sentence in sentences:
    print >> f, sentence

if __name__ == "__main__":
  main()
