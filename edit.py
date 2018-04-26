from enum import Enum


EditType = Enum('EditType', 'Insertion Deletion')
# returns int start
def detectEdit(before, after):
	# usage:
	# will only be one edit between before and after
	# and before != after and len(before) != len(after)

	# search for a deletion
	if len(before) > len(after):
		for i in range(len(before)):
			t = (EditType.Deletion, i)
			if i == len(after):	return t	# reached end
			# unless we reach the end, the edit's in the middle somewhere
			if before[i] != after[i]:	return t
			# no more possibilities
	# search for an insertion
	elif len(before) < len(after):
		for i in range(len(after)):
			t = (EditType.Insertion, i)
			if i == len(before):	return t
			if after[i] != before[i]:	return t
