<html>
<head>
<title>/src/cmd/grep/comp.c - Plan 9 from User Space</title>
</head>
<body>

<center>
<a href="/plan9port/">Plan 9 from User Space</a>'s
<b><a href="/usr/local/plan9/">/usr/local/plan9</a>/<a href="/usr/local/plan9/src">src</a>/<a href="/usr/local/plan9/src/cmd">cmd</a>/<a href="/usr/local/plan9/src/cmd/grep">grep</a>/<a href="/usr/local/plan9/src/cmd/grep/comp.c">comp.c</a></b>
</center>

<p>

<center>
<table cellspacing=0 cellpadding=5 bgcolor=#eeeeff>
<tr><td>
<pre>
#include	"grep.h"

/*
 * incremental compiler.
 * add the branch c to the
 * state s.
 */
void
increment(State *s, int c)
{
	int i;
	State *t, **tt;
	Re *re1, *re2;

	nfollow = 0;
	gen++;
	matched = 0;
	for(i=0; i&lt;s-&gt;count; i++)
		fol1(s-&gt;re[i], c);
	qsort(follow, nfollow, sizeof(*follow), fcmp);
	for(tt=&amp;state0; t = *tt;) {
		if(t-&gt;count &gt; nfollow) {
			tt = &amp;t-&gt;linkleft;
			goto cont;
		}
		if(t-&gt;count &lt; nfollow) {
			tt = &amp;t-&gt;linkright;
			goto cont;
		}
		for(i=0; i&lt;nfollow; i++) {
			re1 = t-&gt;re[i];
			re2 = follow[i];
			if(re1 &gt; re2) {
				tt = &amp;t-&gt;linkleft;
				goto cont;
			}
			if(re1 &lt; re2) {
				tt = &amp;t-&gt;linkright;
				goto cont;
			}
		}
		if(!!matched &amp;&amp; !t-&gt;match) {
			tt = &amp;t-&gt;linkleft;
			goto cont;
		}
		if(!matched &amp;&amp; !!t-&gt;match) {
			tt = &amp;t-&gt;linkright;
			goto cont;
		}
		s-&gt;next[c] = t;
		return;
	cont:;
	}

	t = sal(nfollow);
	*tt = t;
	for(i=0; i&lt;nfollow; i++) {
		re1 = follow[i];
		t-&gt;re[i] = re1;
	}
	s-&gt;next[c] = t;
	t-&gt;match = matched;
}

int
fcmp(const void *va, const void *vb)
{
	Re **aa, **bb;
	Re *a, *b;

	aa = (Re**)va;
	bb = (Re**)vb;
	a = *aa;
	b = *bb;
	if(a &gt; b)
		return 1;
	if(a &lt; b)
		return -1;
	return 0;
}

void
fol1(Re *r, int c)
{
	Re *r1;

loop:
	if(r-&gt;gen == gen)
		return;
	if(nfollow &gt;= maxfollow)
		error("nfollow");
	r-&gt;gen = gen;
	switch(r-&gt;type) {
	default:
		error("fol1");

	case Tcase:
		if(c &gt;= 0 &amp;&amp; c &lt; 256)
		if(r1 = r-&gt;u.cases[c])
			follow[nfollow++] = r1;
		if(r = r-&gt;next)
			goto loop;
		break;

	case Talt:
	case Tor:
		fol1(r-&gt;u.alt, c);
		r = r-&gt;next;
		goto loop;

	case Tbegin:
		if(c == '\n' || c == Cbegin)
			follow[nfollow++] = r-&gt;next;
		break;

	case Tend:
		if(c == '\n')
			matched = 1;
		break;

	case Tclass:
		if(c &gt;= r-&gt;u.x.lo &amp;&amp; c &lt;= r-&gt;u.x.hi)
			follow[nfollow++] = r-&gt;next;
		break;
	}
}

Rune	tab1[] =
{
	0x007f,
	0x07ff
};
Rune	tab2[] =
{
	0x003f,
	0x0fff
};

Re2
rclass(Rune p0, Rune p1)
{
	char xc0[6], xc1[6];
	int i, n, m;
	Re2 x;

	if(p0 &gt; p1)
		return re2char(0xff, 0xff);	/* no match */

	/*
	 * bust range into same length
	 * character sequences
	 */
	for(i=0; i&lt;nelem(tab1); i++) {
		m = tab1[i];
		if(p0 &lt;= m &amp;&amp; p1 &gt; m)
			return re2or(rclass(p0, m), rclass(m+1, p1));
	}

	/*
	 * bust range into part of a single page
	 * or into full pages
	 */
	for(i=0; i&lt;nelem(tab2); i++) {
		m = tab2[i];
		if((p0 &amp; ~m) != (p1 &amp; ~m)) {
			if((p0 &amp; m) != 0)
				return re2or(rclass(p0, p0|m), rclass((p0|m)+1, p1));
			if((p1 &amp; m) != m)
				return re2or(rclass(p0, (p1&amp;~m)-1), rclass(p1&amp;~m, p1));
		}
	}

	n = runetochar(xc0, &amp;p0);
	i = runetochar(xc1, &amp;p1);
	if(i != n)
		error("length");

	x = re2char(xc0[0], xc1[0]);
	for(i=1; i&lt;n; i++)
		x = re2cat(x, re2char(xc0[i], xc1[i]));
	return x;
}

int
pcmp(const void *va, const void *vb)
{
	int n;
	Rune *a, *b;

	a = (Rune*)va;
	b = (Rune*)vb;

	n = a[0] - b[0];
	if(n)
		return n;
	return a[1] - b[1];
}

/*
 * convert character chass into
 * run-pair ranges of matches.
 * this is 10646/utf specific and
 * needs to be changed for some
 * other input character set.
 * this is the key to a fast
 * regular search of characters
 * by looking at sequential bytes.
 */
Re2
re2class(char *s)
{
	Rune pairs[200], *p, *q, ov;
	int nc;
	Re2 x;

	nc = 0;
	if(*s == '^') {
		nc = 1;
		s++;
	}

	p = pairs;
	s += chartorune(p, s);
	for(;;) {
		if(*p == '\\')
			s += chartorune(p, s);
		if(*p == 0)
			break;
		p[1] = *p;
		p += 2;
		s += chartorune(p, s);
		if(*p != '-')
			continue;
		s += chartorune(p, s);
		if(*p == '\\')
			s += chartorune(p, s);
		if(*p == 0)
			break;
		p[-1] = *p;
		s += chartorune(p, s);
	}
	*p = 0;
	qsort(pairs, (p-pairs)/2, 2*sizeof(*pairs), pcmp);

	q = pairs;
	for(p=pairs+2; *p; p+=2) {
		if(p[0] &gt; p[1])
			continue;
		if(p[0] &gt; q[1] || p[1] &lt; q[0]) {
			q[2] = p[0];
			q[3] = p[1];
			q += 2;
			continue;
		}
		if(p[0] &lt; q[0])
			q[0] = p[0];
		if(p[1] &gt; q[1])
			q[1] = p[1];
	}
	q[2] = 0;

	p = pairs;
	if(nc) {
		x = rclass(0, p[0]-1);
		ov = p[1]+1;
		for(p+=2; *p; p+=2) {
			x = re2or(x, rclass(ov, p[0]-1));
			ov = p[1]+1;
		}
		x = re2or(x, rclass(ov, 0xffff));
	} else {
		x = rclass(p[0], p[1]);
		for(p+=2; *p; p+=2)
			x = re2or(x, rclass(p[0], p[1]));
	}
	return x;
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
