/home/cheperboy/.virtualenvs/py3/bin/python ~/script/rsync_backup/rsync_backup.py -vc ~/poubelle/test_rsync/mytask.ini
#rsync -ab --backup-dir=old_`date +%F` --delete --exclude=old_* source/ dest/
#rsync -a --delete -b --backup-dir=old_ --exclude=old_* source/ dest/

#rsync --recursive -x --verbose --progress --delete --size-only --backup \
#--backup-dir=.rsync_trash_`date +%s`/ --exclude=.rsync_trash_*/ \
#~/poubelle/test_rsync/source/ ~/poubelle/test_rsync/dest/

tree -a
