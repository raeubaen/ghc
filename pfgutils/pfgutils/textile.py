#!/usr/bin/env python

# pfgutils.textile module


def em(s):
  """
  Emphasised text

  :param s: text
  :type s: str
  :rtype: str
  """
  return "_%s_" % str(s)


def strong(s):
  """
  Bold (strong) text

  :param s: text
  :type s: str
  :rtype: str
  """
  return "*%s*" % str(s)


def i(s):
  """
  Italicized text

  :param s: text
  :type s: str
  :rtype: str
  """

  return "__%s__" % str(s)


def b(s):
  return "**%s**" % str(s)


def cite(s):
  return "??%s??" % str(s)


def deleted(s):
  return "-%s-" % str(s)


def ins(s):
  return "+%s+" % str(s)


def sup(s):
  return "^%s^" % str(s)


def sub(s):
  return "~%s~" % str(s)


def span(s, style):
  return "%{{{style}}}{text}%".format(style=style, text=s)


def hn(s, n=1):
  return "\nh{0}. {1}\n\n".format(n, s)


def p(s):
  return "\np. %s\n\n" % str(s)


# def pre(s):
#  return "\npre. %s\n" % str(s)


def link(s, target):
  return "\"{0}\":{1}".format(s, target)


def centrifyText(text, width=81):
  """
  Return text padded by spaces to width
  """
  if width <= len(text):
    return text
  return " " * ((width - (len(text) / 2 * 2)) / 2) + text + " " * ((width - len(text)) / 2)


def table(headers, body, caption=None, tablestyle=None, rowstyles=None, cellstyles=None):
  """
  Build simple table with 1+ headers, optional caption and colspans
  :param cellstyles:
  :param rowstyles:
  :param tablestyle:
  :param caption: optional table caption
  :type caption: str
  :param headers: one or more row of headers with colspans
  :type headers: list(str)
  :param body: table body
  :type body: list(list(str))
  :rtype: str
  """

  if rowstyles is None:
    rowstyles = {}

  if cellstyles is None:
    cellstyles = {}

  s = ""
  if tablestyle is not None:
    s += "table{%s}=.\n" % str(tablestyle)
  if caption is not None:
    s += "|=. " + str(caption) + "\n"
  s += "|_. " + " |_. ".join(map(str, headers)) + " |\n"
  if len(body) == 0:
    return ""
  maxwidth = [0] * len(headers)
  for line in list(body) + [headers]:
    for item in line:
      itemi = line.index(item)
      if len(str(item)) > maxwidth[itemi]:
        maxwidth[itemi] = len(str(item))
  for linei in range(len(body)):
    line = body[linei]
    if linei in rowstyles:
      s += "{%s}. " % rowstyles[linei]
    for celli in range(len(line)):
      cell = line[celli]
      if (linei, celli) in cellstyles:
        style = "{%s}." % cellstyles[(linei, celli)]
      else:
        style = ""
      s += "|{style} {text} ".format(style=style, text=centrifyText(str(cell), maxwidth[celli]))
    s += " |\n"
  return s


def fancy_table(fancy_headers, body, caption=None):
  """
  Build table with 1+ headers, optional caption and colspans
  :param caption: optional table caption
  :type caption: str
  :param fancy_headers: one or more row of headers with colspans
  :type fancy_headers: list(tuple(str, int)) | list(list(tuple(str, int)))
  :param body: table body
  :type body: list(list(str))
  :rtype: str
  """

  s = ""
  if caption is not None:
    s += "|=. " + str(caption) + "\n"

  if not isinstance(fancy_headers[0][0], str):
    headers_list = fancy_headers
  else:
    headers_list = [fancy_headers]

  for headers in headers_list:
    for header, colspan in headers:
      s += " |_{0}. {1} ".format("\\" + str(colspan) if colspan > 1 else "", header)

    s += " |\n"
  for line in body:
    s += "| " + " | ".join(map(str, line)) + " |\n"
  return s


def sortable_table(headers, body, caption=None):
  """
  Build sortable table

  :param caption: optional table caption
  :type: caption: None|str
  :param headers: table headers
  :type headers: list(tuple(str, bool))
  :param body: table body
  :type body: list(list(str))
  :rtype: str
  """

  s = "table(sortable).\n"
  if caption is not None:
    s += "|=. " + str(caption) + "\n"

  for header, is_sortable in headers:
    s += " |_{0}. {1} ".format("(sorttable_nosort)" if not is_sortable else "", header)
  s += " |\n"

  for line in body:
    s += "| " + " | ".join(map(str, line)) + " |\n"
  return s


def img(src, title=None, url=None):
  """
  Build image, with optional title and link
  :param src: Image source
  :type src: str
  :param title: Optional title
  :type title: None|str
  :param url: Optional URL
  :type url: None|str
  :rtype: str
  """
  if title is not None:
    title = "(%s)" % title
  s = "!%s!" % (src + title)
  if url is not None:
    s += ":%s" % url
  return s
