import sqlite3
import argparse
import re
from collections import defaultdict

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('files', metavar="sqlite3db", nargs="+", help="File(s) to analyse.")
    parser.add_argument('-t', '--table', action='append', dest='table', help='Which table(s) to convert',
                        choices=['all', 'values', 'flags', 'runs', 'miss', 'ped_on', 'ped_off', 'tp', 'laser'])
    args = parser.parse_args()

    keyvals = {"PED_OFF_MEAN_G1": 1,
               "PED_OFF_MEAN_G6": 6,
               "PED_OFF_MEAN_G12": 12,
               "PED_OFF_RMS_G1": 101,
               "PED_OFF_RMS_G6": 106,
               "PED_OFF_RMS_G12": 112,
               "PED_ON_MEAN_G1": 1001,
               "PED_ON_MEAN_G6": 1006,
               "PED_ON_MEAN_G12": 1012,
               "PED_ON_RMS_G1": 1101,
               "PED_ON_RMS_G6": 1106,
               "PED_ON_RMS_G12": 1112,
               "ADC_MEAN_G1": 2001,
               "ADC_MEAN_G6": 2006,
               "ADC_MEAN_G12": 2012,
               "ADC_RMS_G1": 2101,
               "ADC_RMS_G6": 2106,
               "ADC_RMS_G12": 2112,
               "APD_MEAN": 3001,
               "APD_RMS": 3101,
               "APD_OVER_PN_MEAN": 3002,
               "APD_OVER_PN_RMS": 3102}

    seen_flags = defaultdict(list)

    if 'all' in args.table:
        args.table = ['flags', 'runs', 'miss', 'ped_on', 'ped_off', 'tp', 'laser']
    
    if 'values' in args.table:
        args.table = ['runs', 'ped_on', 'ped_off', 'tp', 'laser']

    for dbfile in sorted(args.files):
        dbh = None
        try:
            dbh = sqlite3.connect(dbfile)
        except sqlite3.Error as e:
            print("An error occurred while loading database", dbfile, ':', e.args[0])
            pass

        sqlfile = open(dbfile.replace('sqlite3', 'sql'), 'w')
        ghc_name = re.findall('ghc_(\d+)', dbfile)[0]
        ghc = "(SELECT ghc FROM ghc WHERE ghc_id = '%s')" % ghc_name

        if dbh is not None:
            print("Processing database", dbfile)
            dbh.row_factory = dict_factory
            cur = dbh.cursor()        
            sqlfile.write("BEGIN;\nINSERT INTO ghc (ghc_id) VALUES ('%s') ON CONFLICT DO NOTHING;\n" % ghc_name)
            if 'flags' in args.table:
                cur.execute("SELECT * FROM flags")
                sqlfile.write("--- Flags ---\nINSERT INTO flags VALUES ")
                data = []
                for row in cur:
                    data.append("({0}, {1}, '{2}')".format(ghc, row['channel_id'], row['flag']))
                sql = ",\n".join(data)
                sqlfile.write(sql + ';\n')

            if 'tp' in args.table:
                cur.execute("SELECT COUNT(*) FROM data_testpulse")
                if cur.fetchone()['COUNT(*)'] == 0:
                    print('No TP data found')
                else:
                    cur.execute("SELECT * FROM data_testpulse")
                    sqlfile.write("--- TestPulse data ---\nINSERT INTO \"values\" VALUES ")
                    data = []
                    for row in cur:
                        if row['key'] in seen_flags[row['channel_id']]:
                            print("Found duplicate: ", row)
                        else:
                            seen_flags[row['channel_id']].append(row['key'])
                            data.append("({0}, {1}, {2}, {3})".format(ghc, row['channel_id'], keyvals[row['key']], row['value']))
                    sql = ",\n".join(data)
                    sqlfile.write(sql + ';\n')

            if 'laser' in args.table:
                cur.execute("SELECT COUNT(*) FROM data_laser")
                if cur.fetchone()['COUNT(*)'] == 0:
                    print('No Laser data found')
                else:
                    cur.execute("SELECT * FROM data_laser")
                    sqlfile.write("--- Laser data ---\nINSERT INTO \"values\" VALUES ")
                    data = []
                    for row in cur:
                        if row['key'] in seen_flags[row['channel_id']]:
                            print("Found duplicate: ", row)
                        else:
                            seen_flags[row['channel_id']].append(row['key'])
                            data.append("({0}, {1}, {2}, {3})".format(ghc, row['channel_id'], keyvals[row['key']], row['value']))
                    sql = ",\n".join(data)
                    sqlfile.write(sql + ';\n')

            if 'ped_on' in args.table:
                cur.execute("SELECT COUNT(*) FROM data_pedestal_hvon")
                if cur.fetchone()['COUNT(*)'] == 0:
                    print('No PED_ON data found')
                else:
                    cur.execute("SELECT * FROM data_pedestal_hvon")
                    sqlfile.write("--- Pedestals w/HV data ---\nINSERT INTO \"values\" VALUES ")
                    data = []
                    for row in cur:
                        fullkey = row['key'].replace('PED', 'PED_ON')
                        keyid = keyvals[fullkey]
                        if fullkey in seen_flags[row['channel_id']]:
                            print("Found duplicate: ", row)
                        else:
                            seen_flags[row['channel_id']].append(fullkey)
                            data.append("({0}, {1}, {2}, {3})".format(ghc, row['channel_id'], keyid, row['value']))
                    sql = ",\n".join(data)
                    sqlfile.write(sql + ';\n')

            if 'ped_off' in args.table:
                cur.execute("SELECT COUNT(*) FROM data_pedestal_hvoff")
                if cur.fetchone()['COUNT(*)'] == 0:
                    print('No PED_OFF data found')
                else:
                    cur.execute("SELECT * FROM data_pedestal_hvoff")
                    sqlfile.write("--- Pedestals w/o HV data ---\nINSERT INTO \"values\" VALUES ")
                    data = []
                    for row in cur:
                        fullkey = row['key'].replace('PED', 'PED_OFF')
                        keyid = keyvals[fullkey]
                        if fullkey in seen_flags[row['channel_id']]:
                            print("Found duplicate: ", row)
                        else:
                            seen_flags[row['channel_id']].append(fullkey)
                            data.append("({0}, {1}, {2}, {3})".format(ghc, row['channel_id'], keyid, row['value']))
                    sql = ",\n".join(data)
                    sqlfile.write(sql + ';\n')

            sqlfile.write("COMMIT;\n")
            sqlfile.close()
            cur.close()
            dbh.close()
    pass


if __name__ == '__main__':
    main()
