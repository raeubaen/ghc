

import codecs
import logging
import re
import sys

import textile

header = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
  <meta http-equiv="Content-Style-Type" content="text/css" />
  <meta name="generator" content="pandoc" />
  <title></title>
  <style type="text/css">code{white-space: pre;}</style>
  <link rel="stylesheet" href="../ghc.css" type="text/css" />
  <!-- SortTable, by Stuart Langridge, http://www.kryogenix.org/code/browser/sorttable/ -->
  <script src="../sorttable.js"></script>
  <!-- MathJAX -->
  <script type="text/javascript" async
    src="https://cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-MML-AM_CHTML">
  </script>
</head>
<body>
"""

footer = """</body>
</html>"""


def convert(fname, notoc=True):
  if not notoc:
    toc_textile = "<div id=\"toc\"><h2> Table of Contents </h2>\n\n"
    logging.debug("Converting file %s", fname)
    logging.debug("Building TOC...")
    with codecs.open(fname, 'r', encoding="UTF-8") as f:
      for line in f:
        m1 = re.match('h([1-3])[.] ([^<]+)', line)
        if m1:
          m2 = re.search(r'<a name="(h\d_\d)"', line)
          if m2:
            lvl = '*' * int(m1.group(1))
            text = m1.group(2)
            name = m2.group(1)
            toc_textile += ("{0} \"{2}\":#{1}\n".format(lvl, name, text.strip()))

    toc_textile += "</div>\n"
    toc_html = textile.textile(toc_textile)
  else:
    toc_html = ""

  with codecs.open(fname, 'r', encoding="UTF-8") as f:
    oname = fname.replace('.textile', '.html')
    logging.debug("Reading and converting file")
    html = textile.textile(f.read())
    logging.debug("Writing HTML output")

    with codecs.open(oname, 'w', encoding='UTF-8') as g:
      g.write(header)
      g.write(toc_html)
      g.write(html)
      g.write(footer)

    logging.debug("Done")


if __name__ == "__main__":
  for fname in sys.argv[1:]:
    convert(fname)
