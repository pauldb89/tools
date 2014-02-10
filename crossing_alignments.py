#!/usr/bin/python

import sys

def main():
  alignment_file = open(sys.argv[1], "r")

  crossing_pairs = 0
  total_pairs = 0
  total_links = 0
  num_lines = 0
  for line in alignment_file:
    alignment = [tuple(map(int, link.split('-'))) for link in line.split()]

    for link in alignment:
      for other_link in alignment:
        crossing_pairs += link[0] > other_link[0] and link[1] < other_link[1]
        total_pairs += 1
      total_links += 1

    num_lines += 1
    if num_lines % 10000 == 0:
      sys.stdout.write('.')
      if num_lines % 1000000 == 0:
        sys.stdout.write(' [%d]\n' % num_lines)
      sys.stdout.flush()

  sys.stdout.write('\n')
  print "Total number of links:", total_links
  print "Number of crossing alignment link pairs:", crossing_pairs
  print "Total number of alignment link pairs:", total_pairs

if __name__ == "__main__":
  main()
