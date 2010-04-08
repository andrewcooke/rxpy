<html>
<head>
<title>/src/cmd/grep/main.c - Plan 9 from User Space</title>
</head>
<body>

<center>
<a href="/plan9port/">Plan 9 from User Space</a>'s
<b><a href="/usr/local/plan9/">/usr/local/plan9</a>/<a href="/usr/local/plan9/src">src</a>/<a href="/usr/local/plan9/src/cmd">cmd</a>/<a href="/usr/local/plan9/src/cmd/grep">grep</a>/<a href="/usr/local/plan9/src/cmd/grep/main.c">main.c</a></b>
</center>

<p>

<center>
<table cellspacing=0 cellpadding=5 bgcolor=#eeeeff>
<tr><td>
<pre>
#define	EXTERN
#include	"grep.h"

char *validflags = "bchiLlnsv";
void
usage(void)
{
	fprint(2, "usage: grep [-%s] [-f file] [-e expr] [file ...]\n", validflags);
	exits("usage");
}

void
main(int argc, char *argv[])
{
	int i, status;

	ARGBEGIN {
	default:
		if(utfrune(validflags, ARGC()) == nil)
			usage();
		flags[ARGC()]++;
		break;

	case 'q':	/* gnu grep -q means plan 9 grep -s */
		flags['s']++;
		break;

	case 'E':	/* ignore, turns gnu grep into egrep */
		break;

	case 'e':
		flags['e']++;
		lineno = 0;
		str2top(ARGF());
		break;

	case 'f':
		flags['f']++;
		filename = ARGF();
		rein = Bopen(filename, OREAD);
		if(rein == 0) {
			fprint(2, "grep: can't open %s: %r\n", filename);
			exits("open");
		}
		lineno = 1;
		str2top(filename);
		break;
	} ARGEND

	if(flags['f'] == 0 &amp;&amp; flags['e'] == 0) {
		if(argc &lt;= 0)
			usage();
		str2top(argv[0]);
		argc--;
		argv++;
	}

	follow = mal(maxfollow*sizeof(*follow));
	state0 = initstate(topre.beg);

	Binit(&amp;bout, 1, OWRITE);
	switch(argc) {
	case 0:
		status = search(0, 0);
		break;
	case 1:
		status = search(argv[0], 0);
		break;
	default:
		status = 0;
		for(i=0; i&lt;argc; i++)
			status |= search(argv[i], Hflag);
		break;
	}
	if(status)
		exits(0);
	exits("no matches");
}

int
search(char *file, int flag)
{
	State *s, *ns;
	int c, fid, eof, nl, empty;
	long count, lineno, n;
	uchar *elp, *lp, *bol;

	if(file == 0) {
		file = "stdin";
		fid = 0;
		flag |= Bflag;
	} else
		fid = open(file, OREAD);

	if(fid &lt; 0) {
		fprint(2, "grep: can't open %s: %r\n", file);
		return 0;
	}

	if(flags['b'])
		flag ^= Bflag;		/* dont buffer output */
	if(flags['c'])
		flag |= Cflag;		/* count */
	if(flags['h'])
		flag &amp;= ~Hflag;		/* do not print file name in output */
	if(flags['i'])
		flag |= Iflag;		/* fold upper-lower */
	if(flags['l'])
		flag |= Llflag;		/* print only name of file if any match */
	if(flags['L'])
		flag |= LLflag;		/* print only name of file if any non match */
	if(flags['n'])
		flag |= Nflag;		/* count only */
	if(flags['s'])
		flag |= Sflag;		/* status only */
	if(flags['v'])
		flag |= Vflag;		/* inverse match */

	s = state0;
	lineno = 0;
	count = 0;
	eof = 0;
	empty = 1;
	nl = 0;
	lp = u.u.buf;
	bol = lp;

loop0:
	n = lp-bol;
	if(n &gt; sizeof(u.u.pre))
		n = sizeof(u.u.pre);
	memmove(u.u.buf-n, bol, n);
	bol = u.u.buf-n;
	n = read(fid, u.u.buf, sizeof(u.u.buf));
	/* if file has no final newline, simulate one to emit matches to last line */
	if(n &gt; 0) {
		empty = 0;
		nl = u.u.buf[n-1]=='\n';
	} else {
		if(n &lt; 0){
			fprint(2, "grep: read error on %s: %r\n", file);
			return count != 0;
		}
		if(!eof &amp;&amp; !nl &amp;&amp; !empty) {
			u.u.buf[0] = '\n';
			n = 1;
			eof = 1;
		}
	}
	if(n &lt;= 0) {
		close(fid);
		if(flag &amp; Cflag) {
			if(flag &amp; Hflag)
				Bprint(&amp;bout, "%s:", file);
			Bprint(&amp;bout, "%ld\n", count);
		}
		if(((flag&amp;Llflag) &amp;&amp; count != 0) || ((flag&amp;LLflag) &amp;&amp; count == 0))
			Bprint(&amp;bout, "%s\n", file);
		Bflush(&amp;bout);
		return count != 0;
	}
	lp = u.u.buf;
	elp = lp+n;
	if(flag &amp; Iflag)
		goto loopi;

/*
 * normal character loop
 */
loop:
	c = *lp;
	ns = s-&gt;next[c];
	if(ns == 0) {
		increment(s, c);
		goto loop;
	}
/*	if(flags['2']) */
/*		if(s-&gt;match) */
/*			print("%d: %.2x**\n", s, c); */
/*		else */
/*			print("%d: %.2x\n", s, c); */
	lp++;
	s = ns;
	if(c == '\n') {
		lineno++;
		if(!!s-&gt;match == !(flag&amp;Vflag)) {
			count++;
			if(flag &amp; (Cflag|Sflag|Llflag|LLflag))
				goto cont;
			if(flag &amp; Hflag)
				Bprint(&amp;bout, "%s:", file);
			if(flag &amp; Nflag)
				Bprint(&amp;bout, "%ld: ", lineno);
			/* suppress extra newline at EOF unless we are labeling matches with file name */
			Bwrite(&amp;bout, bol, lp-bol-(eof &amp;&amp; !(flag&amp;Hflag)));
			if(flag &amp; Bflag)
				Bflush(&amp;bout);
		}
		if((lineno &amp; Flshcnt) == 0)
			Bflush(&amp;bout);
	cont:
		bol = lp;
	}
	if(lp != elp)
		goto loop;
	goto loop0;

/*
 * character loop for -i flag
 * for speed
 */
loopi:
	c = *lp;
	if(c &gt;= 'A' &amp;&amp; c &lt;= 'Z')
		c += 'a'-'A';
	ns = s-&gt;next[c];
	if(ns == 0) {
		increment(s, c);
		goto loopi;
	}
	lp++;
	s = ns;
	if(c == '\n') {
		lineno++;
		if(!!s-&gt;match == !(flag&amp;Vflag)) {
			count++;
			if(flag &amp; (Cflag|Sflag|Llflag|LLflag))
				goto conti;
			if(flag &amp; Hflag)
				Bprint(&amp;bout, "%s:", file);
			if(flag &amp; Nflag)
				Bprint(&amp;bout, "%ld: ", lineno);
			/* suppress extra newline at EOF unless we are labeling matches with file name */
			Bwrite(&amp;bout, bol, lp-bol-(eof &amp;&amp; !(flag&amp;Hflag)));
			if(flag &amp; Bflag)
				Bflush(&amp;bout);
		}
		if((lineno &amp; Flshcnt) == 0)
			Bflush(&amp;bout);
	conti:
		bol = lp;
	}
	if(lp != elp)
		goto loopi;
	goto loop0;
}

State*
initstate(Re *r)
{
	State *s;
	int i;

	addcase(r);
	if(flags['1'])
		reprint("r", r);
	nfollow = 0;
	gen++;
	fol1(r, Cbegin);
	follow[nfollow++] = r;
	qsort(follow, nfollow, sizeof(*follow), fcmp);

	s = sal(nfollow);
	for(i=0; i&lt;nfollow; i++)
		s-&gt;re[i] = follow[i];
	return s;
}

</pre>
</table>
</center>

<p>

<center>
<a href="http://swtch.com/plan9port/"><img src="/plan9port/dist/glendacircle.png" alt="Space Glenda" border=0></a>
</center>

<p>

<center>
<font size=-1>
Copyright &copy; 2005 Lucent Technologies, Russ Cox, MIT.<br>
See <a href="/usr/local/plan9/LICENSE">license</a> for details.
</font>
</center>

</body>
</html>
