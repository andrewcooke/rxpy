<html>
<head>
<title>/src/cmd/grep/sub.c - Plan 9 from User Space</title>
</head>
<body>

<center>
<a href="/plan9port/">Plan 9 from User Space</a>'s
<b><a href="/usr/local/plan9/">/usr/local/plan9</a>/<a href="/usr/local/plan9/src">src</a>/<a href="/usr/local/plan9/src/cmd">cmd</a>/<a href="/usr/local/plan9/src/cmd/grep">grep</a>/<a href="/usr/local/plan9/src/cmd/grep/sub.c">sub.c</a></b>
</center>

<p>

<center>
<table cellspacing=0 cellpadding=5 bgcolor=#eeeeff>
<tr><td>
<pre>
#include	"grep.h"

void*
mal(int n)
{
	static char *s;
	static int m = 0;
	void *v;

	n = (n+3) &amp; ~3;
	if(m &lt; n) {
		if(n &gt; Nhunk) {
			v = sbrk(n);
			memset(v, 0, n);
			return v;
		}
		s = sbrk(Nhunk);
		m = Nhunk;
	}
	v = s;
	s += n;
	m -= n;
	memset(v, 0, n);
	return v;
}

State*
sal(int n)
{
	State *s;

	s = mal(sizeof(*s));
/*	s-&gt;next = mal(256*sizeof(*s-&gt;next)); */
	s-&gt;count = n;
	s-&gt;re = mal(n*sizeof(*state0-&gt;re));
	return s;
}

Re*
ral(int type)
{
	Re *r;

	r = mal(sizeof(*r));
	r-&gt;type = type;
	maxfollow++;
	return r;
}

void
error(char *s)
{
	fprint(2, "grep: internal error: %s\n", s);
	exits(s);
}

int
countor(Re *r)
{
	int n;

	n = 0;
loop:
	switch(r-&gt;type) {
	case Tor:
		n += countor(r-&gt;u.alt);
		r = r-&gt;next;
		goto loop;
	case Tclass:
		return n + r-&gt;u.x.hi - r-&gt;u.x.lo + 1;
	}
	return n;
}

Re*
oralloc(int t, Re *r, Re *b)
{
	Re *a;

	if(b == 0)
		return r;
	a = ral(t);
	a-&gt;u.alt = r;
	a-&gt;next = b;
	return a;
}

void
case1(Re *c, Re *r)
{
	int n;

loop:
	switch(r-&gt;type) {
	case Tor:
		case1(c, r-&gt;u.alt);
		r = r-&gt;next;
		goto loop;

	case Tclass:	/* add to character */
		for(n=r-&gt;u.x.lo; n&lt;=r-&gt;u.x.hi; n++)
			c-&gt;u.cases[n] = oralloc(Tor, r-&gt;next, c-&gt;u.cases[n]);
		break;

	default:	/* add everything unknown to next */
		c-&gt;next = oralloc(Talt, r, c-&gt;next);
		break;
	}
}

Re*
addcase(Re *r)
{
	int i, n;
	Re *a;

	if(r-&gt;gen == gen)
		return r;
	r-&gt;gen = gen;
	switch(r-&gt;type) {
	default:
		error("addcase");

	case Tor:
		n = countor(r);
		if(n &gt;= Caselim) {
			a = ral(Tcase);
			a-&gt;u.cases = mal(256*sizeof(*a-&gt;u.cases));
			case1(a, r);
			for(i=0; i&lt;256; i++)
				if(a-&gt;u.cases[i]) {
					r = a-&gt;u.cases[i];
					if(countor(r) &lt; n)
						a-&gt;u.cases[i] = addcase(r);
				}
			return a;
		}
		return r;

	case Talt:
		r-&gt;next = addcase(r-&gt;next);
		r-&gt;u.alt = addcase(r-&gt;u.alt);
		return r;

	case Tbegin:
	case Tend:
	case Tclass:
		return r;
	}
}

void
str2top(char *p)
{
	Re2 oldtop;

	oldtop = topre;
	input = p;
	topre.beg = 0;
	topre.end = 0;
	yyparse();
	gen++;
	if(topre.beg == 0)
		yyerror("syntax");
	if(oldtop.beg)
		topre = re2or(oldtop, topre);
}

void
appendnext(Re *a, Re *b)
{
	Re *n;

	while(n = a-&gt;next)
		a = n;
	a-&gt;next = b;
}

void
patchnext(Re *a, Re *b)
{
	Re *n;

	while(a) {
		n = a-&gt;next;
		a-&gt;next = b;
		a = n;
	}
}

int
getrec(void)
{
	int c;

	if(flags['f']) {
		c = Bgetc(rein);
		if(c &lt;= 0)
			return 0;
	} else
		c = *input++ &amp; 0xff;
	if(flags['i'] &amp;&amp; c &gt;= 'A' &amp;&amp; c &lt;= 'Z')
		c += 'a'-'A';
	if(c == '\n')
		lineno++;
	return c;
}

Re2
re2cat(Re2 a, Re2 b)
{
	Re2 c;

	c.beg = a.beg;
	c.end = b.end;
	patchnext(a.end, b.beg);
	return c;
}

Re2
re2star(Re2 a)
{
	Re2 c;

	c.beg = ral(Talt);
	c.beg-&gt;u.alt = a.beg;
	patchnext(a.end, c.beg);
	c.end = c.beg;
	return c;
}

Re2
re2or(Re2 a, Re2 b)
{
	Re2 c;

	c.beg = ral(Tor);
	c.beg-&gt;u.alt = b.beg;
	c.beg-&gt;next = a.beg;
	c.end = b.end;
	appendnext(c.end,  a.end);
	return c;
}

Re2
re2char(int c0, int c1)
{
	Re2 c;

	c.beg = ral(Tclass);
	c.beg-&gt;u.x.lo = c0 &amp; 0xff;
	c.beg-&gt;u.x.hi = c1 &amp; 0xff;
	c.end = c.beg;
	return c;
}

void
reprint1(Re *a)
{
	int i, j;

loop:
	if(a == 0)
		return;
	if(a-&gt;gen == gen)
		return;
	a-&gt;gen = gen;
	print("%p: ", a);
	switch(a-&gt;type) {
	default:
		print("type %d\n", a-&gt;type);
		error("print1 type");

	case Tcase:
		print("case -&gt;%p\n", a-&gt;next);
		for(i=0; i&lt;256; i++)
			if(a-&gt;u.cases[i]) {
				for(j=i+1; j&lt;256; j++)
					if(a-&gt;u.cases[i] != a-&gt;u.cases[j])
						break;
				print("	[%.2x-%.2x] -&gt;%p\n", i, j-1, a-&gt;u.cases[i]);
				i = j-1;
			}
		for(i=0; i&lt;256; i++)
			reprint1(a-&gt;u.cases[i]);
		break;

	case Tbegin:
		print("^ -&gt;%p\n", a-&gt;next);
		break;

	case Tend:
		print("$ -&gt;%p\n", a-&gt;next);
		break;

	case Tclass:
		print("[%.2x-%.2x] -&gt;%p\n", a-&gt;u.x.lo, a-&gt;u.x.hi, a-&gt;next);
		break;

	case Tor:
	case Talt:
		print("| %p -&gt;%p\n", a-&gt;u.alt, a-&gt;next);
		reprint1(a-&gt;u.alt);
		break;
	}
	a = a-&gt;next;
	goto loop;
}

void
reprint(char *s, Re *r)
{
	print("%s:\n", s);
	gen++;
	reprint1(r);
	print("\n\n");
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
