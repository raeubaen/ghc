#!/usr/bin/env python3
from ghc_modules import Data
import argparse 

def clear_ghc_range(start=0, end=30):
    """
    Deletes all rows in "values", flags and ghc for each ghc ID in [start,end].
    """
    for ghc_id in range(start, end + 1):
        d = Data.Data(ghc_id, keep=False)
        
        d.cur.execute('DELETE FROM "values" WHERE ghc = %s', (d.ghc_id,))
        d.cur.execute('DELETE FROM flags WHERE ghc = %s', (d.ghc_id,))
        d.cur.execute('DELETE FROM ghc WHERE ghc = %s', (d.ghc_id,))
        d.cur.execute('DELETE FROM runs WHERE ghc = %s', (d.ghc_id,))

        d.dbh.commit()
        print(f"Cleared GHC {d.ghc_id}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', dest='start', type=int, required=True, help="Starting index of ghc to remove")
    parser.add_argument('-e', dest='end', type=int, required=True, help="Ending index of ghc to remove")
    args = parser.parse_args()

    clear_ghc_range(args.start, args.end)

