def levenstein_prefix(s1, s2):
	#returns the minimal levenstein distance between s1 and the prefixes of s2
	table = [[i+j for i in range(1+len(s2))] for j in range(1+len(s1))]
	for i in range(len(s1)):
		for j in range(len(s2)):
			if s1[i].lower()==s2[j].lower():
				table[1+i][1+j] = table[i][j]
			else:
				table[1+i][1+j] = 1+min(table[i][j], table[i+1][j], table[i][j+1])
	return min(table[len(s1)])

def k_best_match(s, ref_list, k):
	# returns the k strings of ref_list which are closest to the string s with the levenstein prefix distance
	return sorted(ref_list, key = lambda x:levenstein_prefix(s, x))[:k]