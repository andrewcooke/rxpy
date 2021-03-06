<html>
<head>
<title>/src/cmd/grep/grep.y - Plan 9 from User Space</title>
</head>
<body>

<center>
<a href="/plan9port/">Plan 9 from User Space</a>'s
<b><a href="/usr/local/plan9/">/usr/local/plan9</a>/<a href="/usr/local/plan9/src">src</a>/<a href="/usr/local/plan9/src/cmd">cmd</a>/<a href="/usr/local/plan9/src/cmd/grep">grep</a>/<a href="/usr/local/plan9/src/cmd/grep/grep.y">grep.y</a></b>
</center>

<p>

<center>
<table cellspacing=0 cellpadding=5 bgcolor=#eeeeff>
<tr><td>
<pre>
%{
#include	"grep.h"
%}

%union
{
	int	val;
	char*	str;
	Re2	re;
}

%type	&lt;re&gt;	expr prog
%type	&lt;re&gt;	expr0 expr1 expr2 expr3 expr4
%token	&lt;str&gt;	LCLASS
%token	&lt;val&gt;	LCHAR
%token		LLPAREN LRPAREN LALT LSTAR LPLUS LQUES
%token		LBEGIN LEND LDOT LBAD LNEWLINE
%%

prog:
	expr newlines
	{
		$$.beg = ral(Tend);
		$$.end = $$.beg;
		$$ = re2cat(re2star(re2or(re2char(0x00, '\n'-1), re2char('\n'+1, 0xff))), $$);
		$$ = re2cat($1, $$);
		$$ = re2cat(re2star(re2char(0x00, 0xff)), $$);
		topre = $$;
	}

expr:
	expr0
|	expr newlines expr0
	{
		$$ = re2or($1, $3);
	}

expr0:
	expr1
|	LSTAR { literal = 1; } expr1
	{
		$$ = $3;
	}

expr1:
	expr2
|	expr1 LALT expr2
	{
		$$ = re2or($1, $3);
	}

expr2:
	expr3
|	expr2 expr3
	{
		$$ = re2cat($1, $2);
	}

expr3:
	expr4
|	expr3 LSTAR
	{
		$$ = re2star($1);
	}
|	expr3 LPLUS
	{
		$$.beg = ral(Talt);
		patchnext($1.end, $$.beg);
		$$.beg-&gt;u.alt = $1.beg;
		$$.end = $$.beg;
		$$.beg = $1.beg;
	}
|	expr3 LQUES
	{
		$$.beg = ral(Talt);
		$$.beg-&gt;u.alt = $1.beg;
		$$.end = $1.end;
		appendnext($$.end,  $$.beg);
	}

expr4:
	LCHAR
	{
		$$.beg = ral(Tclass);
		$$.beg-&gt;u.x.lo = $1;
		$$.beg-&gt;u.x.hi = $1;
		$$.end = $$.beg;
	}
|	LBEGIN
	{
		$$.beg = ral(Tbegin);
		$$.end = $$.beg;
	}
|	LEND
	{
		$$.beg = ral(Tend);
		$$.end = $$.beg;
	}
|	LDOT
	{
		$$ = re2class("^\n");
	}
|	LCLASS
	{
		$$ = re2class($1);
	}
|	LLPAREN expr1 LRPAREN
	{
		$$ = $2;
	}

newlines:
	LNEWLINE
|	newlines LNEWLINE
%%

void
yyerror(char *e, ...)
{
	if(filename)
		fprint(2, "grep: %s:%ld: %s\n", filename, lineno, e);
	else
		fprint(2, "grep: %s\n", e);
	exits("syntax");
}

int
yylex(void)
{
	char *q, *eq;
	int c, s;

	if(peekc) {
		s = peekc;
		peekc = 0;
		return s;
	}
	c = getrec();
	if(literal) {
		if(c != 0 &amp;&amp; c != '\n') {
			yylval.val = c;
			return LCHAR;
		}
		literal = 0;
	}
	switch(c) {
	default:
		yylval.val = c;
		s = LCHAR;
		break;
	case '\\':
		c = getrec();
		yylval.val = c;
		s = LCHAR;
		if(c == '\n')
			s = LNEWLINE;
		break;
	case '[':
		goto getclass;
	case '(':
		s = LLPAREN;
		break;
	case ')':
		s = LRPAREN;
		break;
	case '|':
		s = LALT;
		break;
	case '*':
		s = LSTAR;
		break;
	case '+':
		s = LPLUS;
		break;
	case '?':
		s = LQUES;
		break;
	case '^':
		s = LBEGIN;
		break;
	case '$':
		s = LEND;
		break;
	case '.':
		s = LDOT;
		break;
	case 0:
		peekc = -1;
	case '\n':
		s = LNEWLINE;
		break;
	}
	return s;

getclass:
	q = u.string;
	eq = q + nelem(u.string) - 5;
	c = getrec();
	if(c == '^') {
		q[0] = '^';
		q[1] = '\n';
		q[2] = '-';
		q[3] = '\n';
		q += 4;
		c = getrec();
	}
	for(;;) {
		if(q &gt;= eq)
			error("class too long");
		if(c == ']' || c == 0)
			break;
		if(c == '\\') {
			*q++ = c;
			c = getrec();
			if(c == 0)
				break;
		}
		*q++ = c;
		c = getrec();
	}
	*q = 0;
	if(c == 0)
		return LBAD;
	yylval.str = u.string;
	return LCLASS;
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
