"""
ciss issue tracker. 
http://codespeak.net/ciss

(c) 2009 Holger Krekel, holger at merlinux eu

"""
import re, fnmatch
import py
from optparse import OptionParser

__version__ = '0.2.dev1'

class Issue:
    def __init__(self, basedir):
        self.title = None
        self.param = {}
        self.body = ""
        self.basedir = basedir

    def _addbody(self, line):
        if self.body:
            self.body += "\n" + line.rstrip()
        else:
            self.body = line.rstrip()

    def readtags(self):
        tags = self.param.get("tags")
        if tags:
            l = []
            for t in tags.split(","):
                if t:
                    l.extend(t.split())
            return filter(None, map(str.strip, l))
        return []

    def match(self, path=None, tags=None):
        pattern = self.param.get("path")
        if path:
            if not pattern:
                return False 
            pattern = pattern.strip().replace("/", path.sep)
            cand = path.relto(self.basedir)
            if not pattern.startswith(cand):
                return False
        if tags:
            issuetags = self.readtags()
            for t in tags:
                if t not in issuetags:
                    return False
        return True

def detect_issuefile(p):
    filenames = ('ISSUES.txt', 'ISSUES', 'TODO', 'TODO.txt',)
    for part in p.parts(reverse=True):
        for name in filenames:
            p = part.join(name)
            if p.check():
                return p

def is_title_separator(line):
    return line.startswith("------")

rex_keyvalue = re.compile(r"(\w+):\W*(.*)")

def parseissues(p):
    lines = p.readlines()
    issues = []
    i = 0
    basedir = p.dirpath()
    issue = Issue(basedir=basedir)
    while i < len(lines):
        line = lines[i]
        if line.strip():
            if issue.title is None:
                assert is_title_separator(lines[i+1])
                issue.title = line.rstrip()
                i += 2
                continue
            if not issue.body:
                match = rex_keyvalue.match(line)
                if match:
                    issue.param[match.group(1)] = match.group(2)
                    i += 1
                    continue
            if i+1 >= len(lines):
                issue._addbody(line)
                issues.append(issue)
                break
            if is_title_separator(lines[i+1]):
                issues.append(issue)
                issue = Issue(basedir=basedir)
                issue.title = line.rstrip()
                i += 2
                continue
            issue._addbody(line)
        i += 1
    if issue not in issues:
        issues.append(issue)
    return issues

def main():
    usage = ("%prog [options]\nshow all issues: %prog"
             "\nlimit to path: %prog FILE_OR_DIR"
             "\nlimit to tags: %prog -t TAG1,TAG2 FILE_OR_DIR"
            )
    parser = OptionParser(usage)
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose",
        help="show more verbose info")
    parser.add_option("-t", "--tags", action="store", dest="tags",
        help="show only issues carrying all comma-separated tags")
    #parser.add_option("-p", action="store", dest="path", 
    #    help="only show issues matching the given path glob-pattern")
    parser.add_option("--version", action="store_true", dest="version")
    options, args = parser.parse_args()
    if options.version:
        py.builtin.print_("ciss-%s" %(__version__))
        return
    if args:
        assert len(args) == 1
        basedir = match = py.path.local(args[0])
    else:
        basedir = py.path.local()
        match = None
    p = detect_issuefile(basedir)
    if not p:
        py.builtin.print_("ERROR: could not find issue file in parent directories")
        return 1
    tw = py.io.TerminalWriter()
    unmatched = []
    match_tags = options.tags and options.tags.split(",") or None
    for i, issue in enumerate(parseissues(p)):
        if not issue.match(path=match, tags=match_tags):
           unmatched.append(issue)
        else:  
            line = "[%d] " % i
            indent = len(line)
            line += issue.title
            tags = issue.readtags()
            if tags:
                line += (" [" + " ".join(tags) + "] ")
            tw.write(line, bold=True)
            if 'path' in issue.param: # and options.verbose:
                if not tags:
                    tw.write(" ")
                tw.write(issue.param['path'])
            tw.write("\n")
            if options.verbose:
                for line in issue.body.split("\n"):
                    tw.line(" " * indent + line)
    if unmatched:
        tw.line("%d issues did not match" %(len(unmatched)))
           
if __name__ == '__main__':
    main()
