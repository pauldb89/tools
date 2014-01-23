import os, sys, time
from multiprocessing import Process, Queue
from optparse import OptionParser

def list_phrases(sentence):
  sentence = sentence.split()
  for l in range(1, 5):
    for i in range(len(sentence) - l + 1):
      yield tuple(sentence[i: i+l])

def extract_common_phrases(reference, translation):
  reference_phrases = set([phrase for phrase in list_phrases(reference)])

  common_phrases = []
  for phrase in list_phrases(translation):
    if phrase in reference_phrases:
      common_phrases.append(phrase)

  return common_phrases

def eval_bleu(key, index):
  index = str(index)
  os.system("""sed -n """ + index + """,""" + index + """p \
      data/wmt09/en-de/clean/experiments/dev-""" + key + """-grammars.sgm \
      > """ + key + """-""" + index + """.tmp""")

  os.system("rm -r evals/eval." + key + "-" + index + ".* 2> /dev/null")
  os.system("""workspace/cdec/training/utils/decode-and-evaluate.pl \
      -d evals/ \
      -c data/wmt09/en-de/clean/experiments/cdec.ini \
      -w data/wmt09/en-de/clean/experiments/mira-""" + key + """/weights.final \
      -i """ + key + """-""" + index + """.tmp 2> /dev/null \
      | grep BLEU= | sed -E s/\ +BLEU=//""")

  root_dir = "evals/" + key + "-" + index;
  os.system("mv evals/eval." + key + "-" + index + ".*/ " + root_dir)

  reference = open(root_dir + "/test.refs").read()
  translation = open(root_dir + "/test.trans").read()
  print index, extract_common_phrases(reference, translation)
  os.system("rm -r " + root_dir)

class TimedProcess(Process):
  def __init__(self, function, task, timeout):
    super(TimedProcess, self).__init__(
        target=function, args=(task.key, task.index))
    self.task = task
    self.timeout = timeout

  def start(self):
    self.start_time = time.time()
    super(TimedProcess, self).start()

  def should_terminate(self, current_time):
    return self.start_time + self.timeout <= current_time

class Task:
  def __init__(self, key, index, num_retries):
    self.key = key
    self.index = index
    self.num_retries = num_retries

class TaskScheduler:
  def __init__(self, function, key, num_entries, num_processes, max_retries,
               timeout):
    self.function = function
    self.key = key
    self.num_entries = num_entries
    self.num_processes = num_processes
    self.max_retries = max_retries
    self.timeout = timeout

  def cleanup(self):
    os.system("ps ax | grep sentserver | awk '{print $1}' | xargs kill")
    os.system("ps ax | grep parallelize | awk '{print $1}' | xargs kill")

  def run(self):
    queue = Queue()
    for i in range(1, self.num_entries + 1):
      queue.put(Task(self.key, i, 0))

    total_retries = 0
    num_alive_processes = 0
    processes = [None] * self.num_processes
    failed_indexes = []
    while not queue.empty() or num_alive_processes:
      for i in range(len(processes)):
        if processes[i]:
          if processes[i].is_alive() and processes[i].should_terminate(time.time()):
            processes[i].terminate()

            failed_task = processes[i].task
            sys.stderr.write("Killed task %d\n" % failed_task.index)
            sys.stderr.flush()
            if failed_task.num_retries < self.max_retries:
              failed_task.num_retries += 1
              total_retries += 1
              queue.put(failed_task)
            else:
              failed_indexes.append(failed_task.index)

            processes[i] = None
            num_alive_processes -= 1
          elif not processes[i].is_alive():
            processes[i] = None
            num_alive_processes -= 1

        if not queue.empty() and not processes[i]:
            processes[i] = TimedProcess(
                self.function, queue.get(), self.timeout)
            processes[i].start()
            num_alive_processes += 1

      time.sleep(1)

    sys.stderr.write("Total retries %d\n" % total_retries)
    sys.stderr.write("Failed task indexes: %s\n" % str(failed_indexes))

    self.cleanup()

def main():
  parser = OptionParser()
  parser.add_option("-k", "--key", dest="key",
                    help="Key to identify grammar and weights file")
  parser.add_option("-e", "--entries", dest="entries",
                    help="Number of entries for which to compute BLEU")
  parser.add_option("-p", "--processes", dest="processes", default="20",
                    help="Number of parallel processes")
  parser.add_option("-r", "--retries", dest="retries", default="3",
                    help="Number of times a failed task is retried")
  parser.add_option("-t", "--timeout", dest="timeout", default="60",
                    help="Timeout in seconds after which a process is killed")
  (options, args) = parser.parse_args()

  scheduler = TaskScheduler(eval_bleu, options.key, int(options.entries),
      int(options.processes), int(options.retries), int(options.timeout))
  scheduler.run()

if __name__ == "__main__":
  main()
