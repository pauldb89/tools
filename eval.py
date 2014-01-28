#!/usr/bin/python

import os
import sys
import time
import re
import subprocess
import psutil
import signal
import multiprocessing
from multiprocessing import Process, Queue, Lock
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

def extract_bleu_score(scoring):
  return re.search("BLEU=(\d.\d+|\d)", scoring).group(1)

def create_subprocess(command, stdout=None, stderr=None, shell=False):
  current_process = multiprocessing.current_process()
  current_process.subprocess = subprocess.Popen(
      command, stdout=stdout, stderr=stderr, shell=shell)
  current_process.subprocess.wait()

def eval_bleu(key_type, key, index, lock):
  index = str(index)
  devnull = open(os.devnull, 'w')

  create_subprocess(
      ["rm -r evals/eval." + key + "-" + index + ".*"],
      stderr=devnull, shell=True)

  tmp_file = "evals/" + key + "-" + index + ".tmp"
  create_subprocess(
      ["sed", "-n", index + "," + index + "p",
       "data/wmt09/en-de/clean/experiments/" + key_type + "-" + key + "-grammars.sgm"],
       stdout=open(tmp_file, "w"))

  create_subprocess(
      ["workspace/cdec/training/utils/decode-and-evaluate.pl",
       "-d", "evals",
       "-c", "data/wmt09/en-de/clean/experiments/cdec.ini",
       "-w", "data/wmt09/en-de/clean/experiments/mira-" + key + "/weights.final",
       "-i", tmp_file],
       stdout=devnull, stderr=devnull)

  root_dir = "evals/" + key + "-" + index;
  create_subprocess(
      ["mv evals/eval." + key + "-" + index + ".*/ " + root_dir],
      shell=True)

  scoring = open(root_dir + "/test.scores").read()
  bleu_score = extract_bleu_score(scoring)

  reference = open(root_dir + "/test.refs").read()
  translation = open(root_dir + "/test.trans").read()
  common_phrases = extract_common_phrases(reference, translation)

  lock.acquire()
  print "bleu score:", index, bleu_score
  print "common phrases:", index, common_phrases
  lock.release()

  create_subprocess(["rm", "-r", root_dir])
  create_subprocess(["rm", tmp_file])

class TimedProcess(Process):
  def __init__(self, function, task, timeout, lock):
    super(TimedProcess, self).__init__(
        target=function, args=(task.key_type, task.key, task.index, lock))
    self.task = task
    self.timeout = timeout

  def start(self):
    self.start_time = time.time()
    super(TimedProcess, self).start()

  def run(self):
    def terminate_subprocesses(num, frame):
      if self.subprocess.poll() is None:
        subprocess = psutil.Process(self.subprocess.pid)
        for child_process in subprocess.get_children(recursive=True):
          child_process.send_signal(signal.SIGTERM)
        self.subprocess.terminate()

      sys.exit()

    signal.signal(signal.SIGTERM, terminate_subprocesses)

    super(TimedProcess, self).run()

  def should_terminate(self, current_time):
    return self.start_time + self.timeout <= current_time

class Task:
  def __init__(self, key_type, key, index, num_retries):
    self.key_type = key_type
    self.key = key
    self.index = index
    self.num_retries = num_retries

class TaskScheduler:
  def __init__(self, function, key_type, key, num_entries, num_processes,
               max_retries, timeout):
    self.function = function
    self.key_type = key_type
    self.key = key
    self.num_entries = num_entries
    self.num_processes = num_processes
    self.max_retries = max_retries
    self.timeout = timeout

  def run(self):
    queue = Queue()
    lock = Lock()
    for i in range(1, self.num_entries + 1):
      queue.put(Task(self.key_type, self.key, i, 0))

    total_retries = 0
    num_alive_processes = 0
    processes = [None] * self.num_processes
    failed_indexes = []
    time.sleep(1)
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
                self.function, queue.get(), self.timeout, lock)
            processes[i].start()
            num_alive_processes += 1

      time.sleep(1)

    sys.stderr.write("Total retries %d\n" % total_retries)
    sys.stderr.write("Failed task indexes: %s\n" % str(failed_indexes))

def main():
  parser = OptionParser()
  parser.add_option("--key", dest="key",
                    help="Key to identify grammar and weights file")
  parser.add_option("--entries", dest="entries",
                    help="Number of entries for which to compute BLEU")
  parser.add_option("--processes", dest="processes", default="20",
                    help="Number of parallel processes")
  parser.add_option("--retries", dest="retries", default="3",
                    help="Number of times a failed task is retried")
  parser.add_option("--timeout", dest="timeout", default="60",
                    help="Timeout in seconds after which a process is killed")
  parser.add_option("--key_type", dest="key_type", default="dev",
                    help="Type of test set: dev/devtest")
  (options, args) = parser.parse_args()

  scheduler = TaskScheduler(eval_bleu, options.key_type, options.key,
      int(options.entries), int(options.processes), int(options.retries),
      int(options.timeout))
  scheduler.run()

if __name__ == "__main__":
  main()
