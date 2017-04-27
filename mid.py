import os

dirs = os.listdir('./zips')
for i in dirs:
    path = 'zips/' + i
    if not os.path.isdir(path):
        continue

    files = os.listdir(path)
    for f in files:
        filepath = path + '/' + f
        ext = os.path.splitext(filepath)[1]

        if ext == '.mid':
            csv = "csvs/%s.csv" % os.path.splitext(f)[0]
            os.system("midicsv %s %s" % (filepath, csv))
            os.system("sed -i.bak '6,7d' %s" % csv)
