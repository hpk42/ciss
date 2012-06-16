import sys, os, py
from py.builtin import print_

rsyncdirs = ['test_ciss.py', 'ciss.py', 'conftest.py']

class CissRunner:
    def __init__(self, basedir):
        self.basedir = basedir

    def popen(self, cmdargs, stdout, stderr, **kw):
        if not hasattr(py.std, 'subprocess'):
            py.test.skip("no subprocess module")
        env = os.environ.copy()
        env['PYTHONPATH'] = ":".join(filter(None, [
            str(os.getcwd()), env.get('PYTHONPATH', '')]))
        kw['env'] = env
        #print "env", env
        return py.std.subprocess.Popen(cmdargs, stdout=stdout, stderr=stderr, **kw)
    def run(self, *cmdargs):
        self.basedir.chdir()
        cmdargs = [str(x) for x in cmdargs]
        p1 = py.path.local("stdout")
        p2 = py.path.local("stderr")
        py.builtin.print_("running", cmdargs, "curdir=", py.path.local())
        f1 = p1.open("w")
        f2 = p2.open("w")
        popen = self.popen(cmdargs, stdout=f1, stderr=f2, 
            close_fds=(sys.platform != "win32"))
        ret = popen.wait()
        f1.close()
        f2.close()
        out, err = p1.readlines(cr=0), p2.readlines(cr=0)
        if err:
            for line in err: 
                py.builtin.print_(line, file=sys.stderr)
        if out:
            for line in out: 
                py.builtin.print_(line, file=sys.stdout)
        return RunResult(ret, out, err)

    def create_issues(self, ilist):
        lines = []
        for issuedef in ilist:
            title, keyvalue, body = issuedef
            lines.append(title)
            lines.append("---------------")
            for keyvalue in keyvalue.items():
                lines.append("%s: %s" % keyvalue)
            lines.append(body)
            lines.append("")
        p = self.basedir.join("ISSUES.txt")
        p.write("\n".join(lines))
        return p

def pytest_funcarg__cmd(request):
    tmpdir = request.getfuncargvalue("tmpdir")
    runner = CissRunner(tmpdir)
    return runner

class RunResult:
    def __init__(self, ret, outlines, errlines):
        self.ret = ret
        self.outlines = outlines
        self.errlines = errlines
        self.out = LineMatcher(outlines)
        self.err = LineMatcher(errlines)

class LineMatcher:
    def __init__(self,  lines):
        self.lines = lines

    def str(self):
        return "\n".join(self.lines)

    def fnmatch(self, lines2):
        if isinstance(lines2, str):
            lines2 = py.code.Source(lines2)
        if isinstance(lines2, py.code.Source):
            lines2 = lines2.strip().lines

        from fnmatch import fnmatch
        __tracebackhide__ = True
        lines1 = self.lines[:]
        nextline = None
        extralines = []
        for line in lines2:
            nomatchprinted = False
            while lines1:
                nextline = lines1.pop(0)
                if line == nextline:
                    print_("exact match:", repr(line))
                    break 
                elif fnmatch(nextline, line):
                    print_("fnmatch:", repr(line))
                    print_("   with:", repr(nextline))
                    break
                else:
                    if not nomatchprinted:
                        print_("nomatch:", repr(line))
                        nomatchprinted = True
                    print_("    and:", repr(nextline))
                extralines.append(nextline)
            else:
                if line != nextline:
                    #__tracebackhide__ = True
                    raise AssertionError("expected line not found: %r" % line)
        extralines.extend(lines1)
        return extralines 

