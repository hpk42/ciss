
import py
import os, sys, re
import ciss

def setup_module(mod):
    py.std.sys.argv[1:] = []

def test_parse_one(tmpdir):
    p = tmpdir.join("issues.txt")
    p.write(py.code.Source("""
        title
        --------------
        key: value
        key2: value2
        
        text
    """))
    issues = list(ciss.parseissues(p))
    assert len(issues) == 1
    issue = issues[0]
    assert issue.title == "title"
    assert issue.param['key'] == "value"
    assert issue.param['key2'] == "value2"
    assert issue.body == "text"

def test_parse_two_empty_body(tmpdir):
    p = tmpdir.join("issues.txt")
    p.write(py.code.Source("""
        title
        --------------
        key: value

        title2
        --------------

    """))
    issues = list(ciss.parseissues(p))
    assert len(issues) == 2
    assert issues[0].title == "title"
    assert issues[0].body == ""
    assert issues[0].param['key'] == "value"
    assert issues[1].title == "title2"
    assert issues[1].body == ""

def test_parse_two(tmpdir):
    p = tmpdir.join("issues.txt")
    p.write(py.code.Source("""
        title1
        --------------
        key1: value1
        
        text
        title2
        ----------------
        key2: value2
        text2a
        text2b 
    """))
    issues = list(ciss.parseissues(p))
    assert len(issues) == 2
    issue1, issue2 = issues
    assert issue1.title == "title1"
    assert issue1.param['key1'] == "value1"
    assert issue1.body == "text"

    assert issue2.title == "title2"
    assert issue2.param['key2'] == "value2"
    assert issue2.body == "text2a\ntext2b"

def test_detect_issuefile(tmpdir):
    p = tmpdir.mkdir("hello").mkdir("subdir")
    x = tmpdir.ensure("ISSUES.txt")
    res = ciss.detect_issuefile(p)
    assert res == x

def test_main_simple(tmpdir, capsys):
    p = tmpdir.join("ISSUES.txt")
    p.write(py.code.Source("""
        ensure PEP8
        -------------------------
        tags: 0.2

        nada
    """))
    tmpdir.mkdir("hello").chdir()
    ciss.main()
    out, err = capsys.readouterr()
    assert re.match(".*0.*ensure PEP8.*", out), out
    assert "0.2" in out

class TestIssue:
    def test_readtags(self, tmpdir):
        p = tmpdir.join("issues.txt")
        p.write(py.code.Source("""
            do something
            --------------
            tags: 1.0,bug
            
            text
            do_more
            ------------ 
            tags: 1.1 feature
        """))
        issues = list(ciss.parseissues(p))
        assert len(issues) == 2
        assert issues[0].readtags() == ['1.0', 'bug']
        assert issues[1].readtags() == ['1.1', 'feature']

    def test_match(self, tmpdir, cmd):
        p = cmd.create_issues(
            [("do_something", dict(path="somedir/some.py"), "")])
        issues = list(ciss.parseissues(p))
        assert len(issues) == 1
        issue = issues[0]
        assert issue.match(path=tmpdir.join("somedir"))
        assert not issue.match(path=tmpdir.join("otherdir", 'some1.py'))
        assert issue.match(path=tmpdir.join("somedir", 'some.py'))
        assert issue.match(path=tmpdir.join("somedir"))
     
    def test_match_no_pattern(self, tmpdir, cmd):
        p = tmpdir.join("ISSUES.txt")
        p.write(py.code.Source("""
            do something
            --------------
            text
        """))
        issues = list(ciss.parseissues(p))
        assert len(issues) == 1
        issue = issues[0]
        assert not issue.match(path=tmpdir.join("somedir"))
        assert not issue.match(path=tmpdir.join("somedir", 'xyz.py'))
        assert not issue.match(path=tmpdir.join("somedir", 'some1.py'))

    def test_match_tags(self, tmpdir, cmd):
        p = cmd.create_issues(
            [("do_something", dict(tags="one two three"), ""),])
        issues = list(ciss.parseissues(p))
        assert len(issues) == 1
        issue = issues[0]
        assert issue.match(tags=['one'])
        assert issue.match(tags=['one', 'two'])
        assert not issue.match(tags=['one', 'four'])
        assert issue.match(tags=['three'])
        assert not issue.match(tags=['four'])
        assert issue.match()
      

class TestFunctional:
    def test_run_version(self, cmd):
        result = cmd.run("ciss", "--version")
        assert result.ret == 0
        assert result.out.fnmatch("ciss-*")

    def test_run_verbose(self, cmd):
        cmd.create_issues([("title", {}, "body")])
        result = cmd.run("ciss", "--verbose")
        assert result.ret == 0
        assert result.out.fnmatch([
            "*0*title",
            "    body"
        ])

    def test_show_no_tags(self, cmd):
        cmd.create_issues(
            [("do something", dict(path="PPP"), "")]
        )
        result = cmd.run("ciss")
        assert result.ret == 0
        assert result.out.fnmatch([
            "*0*do something PPP*"
        ])


    def test_match_by_path(self, cmd):
        cmd.create_issues(
            [("do something", dict(path="somedir/some1.py"), ""),
             ("issue2", dict(path="otherdir/other"), "")
        ])
        path = cmd.basedir.ensure("somedir", "some1.py")
        result = cmd.run("ciss", path)
        assert result.ret == 0
        assert result.out.fnmatch([
            "*0*do something*"
        ])
        assert "[1]" not in result.out.str()
        result = cmd.run("ciss", path.dirpath())
        assert result.ret == 0
        assert result.out.fnmatch([
            "*0*do something*"
        ])
        assert "[1]" not in result.out.str()

    def test_match_by_tag(self, cmd):
        cmd.create_issues(
            [("issue0", dict(tags="one two"), ""),
             ("issue1", dict(tags="two three"), ""),
             ("issue2", {}, "")])
        result = cmd.run("ciss", "-t", "two")
        assert result.ret == 0
        assert result.out.fnmatch([
            "*issue0*two*",
            "*issue1*two*",
            "1*did not match*",
        ])

    def test_not_existing_issues(self, cmd):
        result = cmd.run("ciss")
        assert result.ret == 1
        assert result.out.fnmatch([
            "*could not find issue file in parent directories*"
        ])
