<html>
<head>
<title>/src/cmd/grep/grep.h - Plan 9 from User Space</title>
</head>
<body>

<center>
<a href="/plan9port/">Plan 9 from User Space</a>'s
<b><a href="/usr/local/plan9/">/usr/local/plan9</a>/<a href="/usr/local/plan9/src">src</a>/<a href="/usr/local/plan9/src/cmd">cmd</a>/<a href="/usr/local/plan9/src/cmd/grep">grep</a>/<a href="/usr/local/plan9/src/cmd/grep/grep.h">grep.h</a></b>
</center>

<p>

<center>
<table cellspacing=0 cellpadding=5 bgcolor=#eeeeff>
<tr><td>
<pre>
#include	&lt;u.h&gt;
#include	&lt;libc.h&gt;
#include	&lt;bio.h&gt;

#ifndef	EXTERN
#define	EXTERN	extern
#endif

typedef	struct	Re	Re;
typedef	struct	Re2	Re2;
typedef	struct	State	State;

struct	State
{
	int	count;
	int	match;
	Re**	re;
	State*	linkleft;
	State*	linkright;
	State*	next[256];
};
struct	Re2
{
	Re*	beg;
	Re*	end;
};
struct	Re
{
	uchar	type;
	ushort	gen;
	union
	{
		Re*	alt;	/* Talt */
		Re**	cases;	/* case */
		struct		/* class */
		{
			Rune	lo;
			Rune	hi;
		} x;	
		Rune	val;	/* char */
	} u;
	Re*	next;
};

enum
{
	Talt		= 1,
	Tbegin,
	Tcase,
	Tclass,
	Tend,
	Tor,

	Caselim		= 7,
	Nhunk		= 1&lt;&lt;16,
	Cbegin		= 0x10000,
	Flshcnt		= (1&lt;&lt;9)-1,

	Cflag		= 1&lt;&lt;0,
	Hflag		= 1&lt;&lt;1,
	Iflag		= 1&lt;&lt;2,
	Llflag		= 1&lt;&lt;3,
	LLflag		= 1&lt;&lt;4,
	Nflag		= 1&lt;&lt;5,
	Sflag		= 1&lt;&lt;6,
	Vflag		= 1&lt;&lt;7,
	Bflag		= 1&lt;&lt;8
};

EXTERN	union
{
	char	string[16*1024];
	struct
	{
		/*
		 * if a line requires multiple reads, we keep shifting
		 * buf down into pre and then do another read into
		 * buf.  so you'll get the last 16-32k of the matching line.
		 * if h were smaller than buf you'd get a suffix of the
		 * line with a hole cut out.
		 */
		uchar	pre[16*1024];	/* to save to previous '\n' */
		uchar	buf[16*1024];	/* input buffer */
	} u;
} u;

EXTERN	char	*filename;
EXTERN	Biobuf	bout;
EXTERN	char	flags[256];
EXTERN	Re**	follow;
EXTERN	ushort	gen;
EXTERN	char*	input;
EXTERN	long	lineno;
EXTERN	int	literal;
EXTERN	int	matched;
EXTERN	long	maxfollow;
EXTERN	long	nfollow;
EXTERN	int	peekc;
EXTERN	Biobuf*	rein;
EXTERN	State*	state0;
EXTERN	Re2	topre;

extern	Re*	addcase(Re*);
extern	void	appendnext(Re*, Re*);
extern	void	error(char*);
extern	int	fcmp(const void*, const void*); 	/* (Re**, Re**) */
extern	void	fol1(Re*, int);
extern	int	getrec(void);
extern	void	increment(State*, int);
#define initstate grepinitstate
extern	State*	initstate(Re*);
extern	void*	mal(int);
extern	void	patchnext(Re*, Re*);
extern	Re*	ral(int);
extern	Re2	re2cat(Re2, Re2);
extern	Re2	re2class(char*);
extern	Re2	re2or(Re2, Re2);
extern	Re2	re2char(int, int);
extern	Re2	re2star(Re2);
extern	State*	sal(int);
extern	int	search(char*, int);
extern	void	str2top(char*);
extern	int	yyparse(void);
extern	void	reprint(char*, Re*);
extern	void	yyerror(char*, ...);

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
