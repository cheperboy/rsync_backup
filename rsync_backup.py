#!/home/cheperboy/.virtualenvs/py3/bin/python3

# This progam reads a file "tasks.ini" and call rsync to make backup for each task
# A task defines source dir, dest dir, mountpoint (directory to check if dest is recheable)
# A task may defines "files_from". 
# In this case a list of files/directory is provided in separate config file 

###################
# Call the script #
###################
# Example Anacrontab entry below:
# 1	10	backup_tasks	/home/cheperboy/.virtualenvs/py3/bin/python3 /home/cheperboy/script/rsync_backup/rsync_backup.py
#
# Console call:
# workon py3
# python /home/cheperboy/script/rsync_backup/rsync_backup.py
# 
#######
# Log #
#######
# log is not done by rsync but by python program
# "last.log"      Always up to date with list of tasks, last run, error count.
# "prog_name.log" Program log with precise start/end timestamp of execution, error count
# "task_name.log" stderrreturned by rsync call incase retcode not success    
#
# Last.log
# Task_name date error_count
# Task_foo 2020-12-25 0
# Task_bar 2020-12-25 1

##################### 
# exemple tasks.ini #
#####################
# [Images]
# NAME       = Images
# SOURCE     = /home/Images/
# DEST       = /media/NAS/photo/
# MOUNTPOINT = /media/NAS/

# [Some Files]
# NAME       = some_files
# SOURCE     = /
# FILES_FROM = /home/some_files.txt
# DEST       = /media/NAS/backup/some_files
# MOUNTPOINT = /media/NAS/backup

####################
# Some rsync options
# --size-only       
#   saute les fichiers qui sont similaires par la date
#   Normalement rsync ignore tous les fichiers qui ont la même taille et une horodate identique. Avec l'option --size-only, les fichiers seront ignorés s'ils ont la même taille, indépendamment de l'horodate. Ceci est utile lorsque l'on commence à se servir de rsync après avoir utilisé un autre outil de miroitage qui peut ne pas préserver les horodates exactement. 

#--backup-dir=REP   
#   utilisé avec l'option --backup, ceci dit à rsync de garder garder les fichiers supprimés dans le répertoire spécifié
# 

import configparser
import sys
import os
import subprocess
from tabulate import tabulate # pretty print table
from datetime import datetime, date

# Get the directory where this program is located
PROG_NAME     = "rsync_backup"
DIR           = os.path.dirname(os.path.realpath(__file__))
DEFAULT_CONF  = os.path.join("etc", "tasks.ini")
TRASH_DIR     = ".rsync_trash/"
VERBOSE       = None
LOG_DIR       = "/var/log/"+PROG_NAME
PROG_LOG      = os.path.join(LOG_DIR, __file__[:-2] + "log")
LAST_LOG      = os.path.join(LOG_DIR, "last.log")
LAST_LOG_DATE = os.path.join(LOG_DIR, "date.log")


def short_date():
  today = date.today()
  return(today.strftime("%Y/%m/%d"))

def long_date():
  today = datetime.now()
  return(today.strftime("%Y/%m/%d %H:%M:%S"))

def append_log(file, content):
  """ Append content to log file """
  with open(file, 'a+') as f:
    f.write(content + '\n')
  print(content)

def create_log(file, content):
  """ Overwrite existing log file """
  if os.path.exists(file):
    os.remove(file) 
  with open(file, 'w') as f:
    f.write(content + '\n')

def show_task(conf):
  #for key in conf:  
    #print(key, conf[key], sep="\t")
  data = list(conf.items())  
  return(tabulate(data, tablefmt="plain"))

def dir_is_reacheable(path):
  # this shell command check if directory is reacheable with a timout (retcode 0 if success)
  cmd = 'timeout 4 ls '+path+' > /dev/null 2>&1 && exit 0 || exit 1;'  
  out = subprocess.run(cmd, shell=True, universal_newlines=True, check=False, capture_output=True)
  # print(out)
  if out.returncode != 0:
    return (False)
  else:  
    return (True)
  
def check_file_list(filename):
  """ Check consistency of file_list. 
  No spaces allowed,
  If file or directory listed don't exists, this is a warning (rsync will also raise an error) 
  """
  with open(filename) as f: 
    num = 0
    out = err = warn = ""
    lines = f.readlines() 
    for line in lines:
      num += 1
      if " " in line:
        err += "\t\tline "+ str(num) +" space not allowed " + str(line)
      if not os.path.exists(line.rstrip()):
        warn += "\t\tline "+ str(num) +" file don't exists "+ str(line)
    
    if warn != "" or err != "": 
        out = "Problem found in conf file " + filename 
    if warn != "": out +="\n\tWarnings: \n" + warn 
    if err != "": out += "\n\tErrors: \n" + err 
    return out

def rsync_standard(conf):
  cmd = 'rsync \
--recursive \
-x --verbose \
--progress \
--delete \
--size-only \
--protect-args \
--exclude=@eaDir/ \
--filter "- lost+found/" --filter "- .cache/" \
--backup --backup-dir='+conf['trash']+' \
--exclude='+conf['trash']+' \
'+conf['source']+' \
'+conf['dest']
  return (cmd)

def rsync_files_from(conf):
  """rsync -av --files-from=file_list.txt / nas:backup/"""
  cmd = 'rsync \
--archive \
--verbose \
--progress \
--delete \
--exclude=@eaDir/ \
--filter "- lost+found/" --filter "- .cache/" \
--backup --backup-dir='+conf['trash']+' \
--exclude='+conf['trash']+' \
--files-from='+conf['files_from']+' \
'+conf['source']+' \
'+conf['dest']
  
  return (cmd)

def prepare_task(conf):
  """ Log infos and make some checks before processing the task
  """
  if VERBOSE:
    append_log(conf['log'], "\n" + show_task(conf))
  
  if not (os.path.exists(conf['mountpoint']) and dir_is_reacheable(conf['mountpoint'])):
    append_log(conf['log'], "Error: directory not reacheable" + conf['mountpoint'])
    return False
  
  # Call rsync shell command   
  if 'files_from' in conf:
    err = check_file_list(conf['files_from'])
    if err != "":
      append_log(conf['log'], err)
      return False

  return True

def process_task(conf):
  try:
    # set additional variables for this task
    conf['trash'] = os.path.join(conf['dest'], TRASH_DIR)
    conf['log']   = os.path.join(LOG_DIR, "task_" +conf['name']+ ".log")
    conf['date_success_log'] = os.path.join(LOG_DIR, "task_" +conf['name']+ "_success.log")
    append_log(conf['log'], "\n" + long_date() + " Starting task " + conf['name'] + STR_DRY)
    
    if not prepare_task(conf):
      return False
    
    # Call rsync shell command   
    if 'files_from' in conf:
      cmd = rsync_files_from(conf)
    else:
      cmd = rsync_standard(conf)

    if VERBOSE:
      append_log(conf['log'], "CMD:" + cmd)
    
    if not DRY:
      out = subprocess.run(cmd, shell=True, universal_newlines=True, check=False, capture_output=True)
      if VERBOSE:
        append_log(conf['log'], "STDOUT:" + out.stdout)
        append_log(conf['log'], "STDERR:" + out.stderr)
        append_log(conf['log'], "RETCODE:" + str(out.returncode))
      
      # if return code not succes then log stderr and return false 
      if out.returncode != 0:
        append_log(conf['log'], "\nError: " + out.stderr)
        return False
  except Exception as e:
    append_log(conf['log'], "\nError: " + str(e))
    return False
  
  # Success
  append_log(conf['log'], "\n" + long_date() + " Ending task " + conf['name'] + STR_DRY)
  create_log(conf['date_success_log'], long_date())
  return True
  
if __name__ == "__main__":
  # --------------------
  # Check log dir exists
  if not os.path.exists(LOG_DIR):
    print("Error: directory must be created " + LOG_DIR) 
    print("sudo mkdir " + LOG_DIR) 
    print("sudo chown user:group " + LOG_DIR)
    sys.exit()

  # ---------------
  # Parse arguments
  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument("-v", "--verbose", action="store_true", help="Increase output verbosity.")
  parser.add_argument("-l", "--list",    action="store_true", help="Read config file and list tasks.")
  parser.add_argument("-d", "--dry",     action="store_true", help="Dry run. Don't exec rsync. show tasks")
  parser.add_argument("-c", "--config",  help="Manually specify config file. provide FULL PATH.")
  args = parser.parse_args()
  if args.verbose: VERBOSE = True
  if args.dry:
    DRY     = True 
    STR_DRY = " DRY RUN"
  else:
    DRY     = False 
    STR_DRY = ""

  # ----------------
  # Load config file
  config_file = os.path.join(DIR, DEFAULT_CONF)
  # override conf file path if --config foo.ini provided when calling the program 
  if args.config: 
    config_file = os.path.join(args.config)
  if not os.path.exists(config_file):
    append_log(PROG_LOG, "\n" + " Exit. Config file not found " + config_file)
    exit()
  config = configparser.ConfigParser()
  config.read(config_file)
  
  if args.list:
    print('List of tasks {}'.format(config.sections()))
    for task_config in config.sections():
      conf = config[task_config]
      print("\n" + show_task(conf))
    sys.exit()

  # ---------------
  # Show tasks list
  append_log(PROG_LOG, "\n" + long_date() + " Starting job" + STR_DRY)
  append_log(PROG_LOG, ('List of tasks {}'.format(config.sections())))
  
  # -------------
  # Process tasks
  res = ""
  for task_config in config.sections():
    conf = config[task_config]
    result = process_task(conf)
    res += '{} {} {}\n'.format(conf["name"], short_date(), int(not result))
  
  if not DRY: 
    create_log(LAST_LOG, res)
    create_log(LAST_LOG_DATE, long_date())
  append_log(PROG_LOG, "\n" + res)
  append_log(PROG_LOG, long_date()+ " Ending job" +STR_DRY)

