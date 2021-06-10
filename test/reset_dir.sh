rm -rf source
rm -rf dest
mkdir -p source/dir1 dest
touch source/dir1/f1 source/f2 source/f3
echo "this is original file f1 in source/dir1." > source/dir1/f1
echo "this is original file f2 in source." > source/f2
echo "this is original file f3 in source." > source/f3
tree -a

