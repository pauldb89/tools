#!/usr/bin/python

import sys

def main():
  alignment_file = open(sys.argv[1], "r")

  crossing = 0
  total = 0
  num_lines = 0
  for line in alignment_file:
    alignment = [tuple(map(int, link.split('-'))) for link in line.split()]

    for link in alignment:
      for other_link in alignment:
        crossing += link[0] > other_link[0] and link[1] < other_link[1]
        total += 1

    num_lines += 1
    if num_lines % 10000 == 0:
      sys.stdout.write('.')
      if num_lines % 1000000 == 0:
        sys.stdout.write(' [%d]\n' % num_lines)
      sys.stdout.flush()

  sys.stdout.write('\n')
  print "Number of crossing aligments:", crossing
  print "Total number of alignment link pairs:", total

if __name__ == "__main__":
  main()
