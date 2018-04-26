import re
import sys

#TODO escape html ?

# BROKEN WITH \/
def interpret_(code, out, progression, html=False):
	expression = re.compile(r'^((?:[^\\\/]|\\.)*)\/((?:[^\\\/]|\\.)*)\/((?:[^\\\/]|\\.)*)\/', re.DOTALL)
	match = expression.search(code)
	s = None
	while match:
		code = code[len(match.group(0)):]
		groups = [re.compile(r'\\(.)', re.DOTALL).sub(r"\1", x) for x in match.groups()]
		out(groups[0])
		s = True
		while s:
			s = False
			def replace(match):
				nonlocal s
				s = True
				return groups[2]
			code = re.sub(re.escape(groups[1]), replace, code)
		match = expression.search(code)
		# look ahead (don't print last progression, because it's redundant)
		if progression and match:	out(code + '\n')
	o = ''
	arrow = '<span style="color:darkgrey">-></span> '
	if progression and html: o += arrow
	o += re.compile(r'\/.*$', re.DOTALL).sub('', re.compile(r'\\(.)', re.DOTALL).sub(lambda m: m.group(1), code))
	# o += re.compile(r'\/.*$', re.DOTALL).sub('', re.compile(r'\\(.)', re.DOTALL).sub(lambda m: "\u012F" if m.group(1) == "/" else m.group(1), code))
	if html: o = re.sub('\n', '<br>', o)
	out(o)
	# out((arrow if progression else '') + re.compile(r'\/.*$', re.DOTALL).sub('', re.compile(r'\\(.)\/', re.DOTALL).sub(lambda y, x: "\u012F" if x == "/" else x, code)))

def interpret(code, out, progression, output_html=False):
	wc = r'(?:[^/]|(?<=\\).)'	# wildcard, EXCLUDING the slash function
	expression = re.compile(r'({}*)(?<!\\)\/({}*)(?<!\\)\/({}*)(?<!\\)\/(.*)$'.format(wc, wc, wc), re.DOTALL)
	match = expression.search(code)
	if not match:
		code = re.compile(r'\\(.)', re.DOTALL).sub(lambda m: m.group(1), code)	# escape here, because loop is never entered
	while match:
		print_block, pattern, replacement, text = tuple(
			[re.compile(r'\\(.)', re.DOTALL).sub(lambda m: m.group(1), g) for g in \
			(match.group(1), match.group(2), match.group(3))] + [match.group(4)]	# don't unescape chars in substitution, right?
		)
		replacements = -1
		while replacements != 0:
			text, replacements = re.subn(re.escape(pattern), replacement, text)
			code = print_block + text
		match = expression.search(code)
		if progression and match: out(code + '<br>' if output_html else '\n')
	if output_html:
		code = '<span style="color:darkgrey">-></span> ' + code
		code = re.sub('\n', '<br>', code)
	out(code)

if __name__ == "__main__":
	file = open(sys.argv[1], 'r')
	interpret(file.read(), lambda s: print(s, end=''), False)
	file.close()
