extremely basic for now, but I'll add more functionality as I get the chance.

# what it does:
extremely basic backup for your patches. offload them from your synth to text files on your computer, and put them back another time.

# dependencies:
 - mido (`pip install mido`)

# how to use it:
- clone this git repository: `git clone https://github.com/r-b-g-b/SH201Librarian.git`
- `cd SH201Librarian`

## backup all patches
dumps all of your user patches to .syx files

- `python librarian.py --backup_directory DIRECTORY --backup_prefix PREFIX --ioport_name MIDIIOPORTNAME`
  - DIRECTORY is the path to the directory you want to save to
  - PREFIX (optional) a filename prefix to keep things organized

## restore a patch
- python librarian.py --patch_path PATH --program_number PROGRAMNUMBER
  - PATCHPATH is the path to the .syx file you previously saved
  - PROGRAMNUMBER is the slot on your keyboard you want the patch to go to. this can be expressed as a number from 0-31 or the letter/number combo, i.e. `A4`, `D2`, etc.

`python librarian.py -h` will print mostly this info
