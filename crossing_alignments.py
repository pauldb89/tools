import sys

def main():
  alignment_file = open(sys.argv[1], "r")

  crossing = 0
  for line in alignment_file:
    alignment = [tuple(map(int, link.split('-'))) for link in line.split()]

    for link in alignment:
      for other_link in alignment:
        crossing += link[0] > other_link[0] and link[1] < other_link[1]

  print "Number of crossing aligments:", crossing

if __name__ == "__main__":
  main()
