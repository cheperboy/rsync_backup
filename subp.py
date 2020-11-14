#!/home/chep/.virtualenvs/py3/bin/python3

import os
import subprocess

def srun(path):
  # this shell command check if directory is reacheable with a timout (retcode 0 if success)
  cmd = 'timeout 4 ls '+path+' > /dev/null 2>&1 && exit 0 || exit 1;'  
  out = subprocess.run(cmd, shell=True, universal_newlines=True, check=False, capture_output=True)
  print(out)
  #print(out.stdout)
  if out.returncode != 0:
    print (path+"\tFail")
  else:  
    print (path+"\tSuccess")

if __name__ == "__main__":
  #print(subprocess.run(["ls", "-l"]).returncode)
  srun("/home")
  srun("/foo")
  
"""
check=False 
  don't raise an python exception whatever the shell command return code is)  
check=True 
  raise a python exception if the return code is not 0 (if shell command not success)
  
capture_output=True
  return also stdout and stderr

"""
